"""
evidence/screenshots/capture_screenshots.py

Captures GENUINE screenshots of the running Streamlit dashboard by driving
a headless Chrome/Edge through the Chrome DevTools Protocol (CDP). It only
clicks the dashboard's own controls; nothing on the page is edited or mocked.

Usage (dashboard already running, e.g. `run_dashboard.bat 8517`):
    venv\\Scripts\\python evidence\\screenshots\\capture_screenshots.py --url http://localhost:8517 \
        --out evidence\\screenshots [--live]

--live additionally clicks "Generate" in LIVE mode on the LLM page (one real,
billable API call using the key in .env). Without it, the LLM page is shown
in demo mode only.

The comparative workflow runs PrivBayes (epsilon = 3, seed 7) from the UI.
That APPENDS a record to results/experiment_results.jsonl and writes a new
CSV, so restore the published results afterwards:
    git checkout -- results/  &&  del results\\synthetic_data\\*seed7*
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
WIDTH = 1600
SCALE = 1.25  # device pixel ratio -> 2000 px wide images


class CDP:
    def __init__(self, ws):
        self.ws, self.n, self.pending = ws, 0, {}

    @classmethod
    async def connect(cls, url):
        self = cls(await websockets.connect(url, max_size=None, ping_interval=None))
        asyncio.ensure_future(self._reader())
        return self

    async def _reader(self):
        async for msg in self.ws:
            data = json.loads(msg)
            fut = self.pending.pop(data.get("id"), None)
            if fut is not None and not fut.done():
                fut.set_result(data)

    async def call(self, method, **params):
        self.n += 1
        fut = asyncio.get_event_loop().create_future()
        self.pending[self.n] = fut
        await self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        res = await asyncio.wait_for(fut, 600)
        if "error" in res:
            raise RuntimeError(f"{method}: {res['error']}")
        return res.get("result", {})

    async def js(self, expr):
        r = await self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in r:
            raise RuntimeError(f"JS error: {r['exceptionDetails']}")
        return r.get("result", {}).get("value")


HELPERS = r"""
window.__vis = el => !!(el && el.offsetParent !== null);
window.__clickText = (sel, text, exact) => {
  const els = [...document.querySelectorAll(sel)].filter(e => __vis(e) &&
      (exact ? e.innerText.trim() === text : e.innerText.includes(text)));
  if (!els.length) return false; els[0].scrollIntoView({block: 'center'}); els[0].click(); return true; };
window.__running = () => !!document.querySelector('[data-testid="stStatusWidget"]') ||
      [...document.querySelectorAll('[data-testid="stSpinner"]')].some(__vis);
"""


async def settle(cdp, extra=1.0, timeout=900):
    """Wait until Streamlit has finished rerunning (no status widget / spinner)."""
    await asyncio.sleep(1.2)
    t0 = time.time()
    while time.time() - t0 < timeout:
        busy = await cdp.js(HELPERS + "__running()")
        if not busy:
            break
        await asyncio.sleep(0.5)
    await asyncio.sleep(extra)


async def mouse_click(cdp, element_js):
    """Real mouse click (CDP Input events) on the element returned by element_js."""
    rect = await cdp.js(HELPERS + f"""(() => {{ const e = ({element_js}); if (!e) return null;
        e.scrollIntoView({{block: 'center'}}); const r = e.getBoundingClientRect();
        return {{x: r.left + r.width / 2, y: r.top + r.height / 2}}; }})()""")
    if not rect:
        return False
    await asyncio.sleep(0.3)
    for typ in ("mouseMoved", "mousePressed", "mouseReleased"):
        await cdp.call("Input.dispatchMouseEvent", type=typ, x=rect["x"], y=rect["y"], button="left",
                       clickCount=1 if typ != "mouseMoved" else 0)
    return True


def _find(sel, text, exact):
    cond = "e.innerText.trim() === T" if exact else "e.innerText.includes(T)"
    return (f"(() => {{ const T = {json.dumps(text)}; return [...document.querySelectorAll({json.dumps(sel)})]"
            f".filter(e => __vis(e) && {cond})[0]; }})()")


async def click(cdp, text, sel="button", exact=False):
    if not await mouse_click(cdp, _find(sel, text, exact)):
        raise RuntimeError(f"control not found: {text!r}")
    await settle(cdp)


async def nav(cdp, label):
    """Click a sidebar radio option by its exact label."""
    await click(cdp, label, sel='[data-testid="stSidebar"] label', exact=True)


async def select_option(cdp, box_label, option):
    """Open the selectbox whose label contains box_label and choose option."""
    box = (f"[...document.querySelectorAll('[data-testid=\"stSelectbox\"]')].filter(__vis)"
           f".find(x => x.innerText.includes({json.dumps(box_label)}) || "
           f"(x.querySelector('input') && (x.querySelector('input').getAttribute('aria-label')||'').includes({json.dumps(box_label)})))")
    if not await mouse_click(cdp, f"(() => {{ const b = {box}; return b && (b.querySelector('button[aria-label=\"Open\"]') || b.querySelector('input')); }})()"):
        raise RuntimeError(f"selectbox not found: {box_label!r}")
    await asyncio.sleep(1.0)
    opt_js = f"[...document.querySelectorAll('[role=\"option\"]')].find(x => x.innerText.trim() === {json.dumps(option)})"
    if not await cdp.js(f"!!({opt_js})"):
        # the option list is virtualised: type the start of the option to filter it
        await cdp.call("Input.insertText", text=option.split(" | ")[0])
        await asyncio.sleep(1.2)
    if not await mouse_click(cdp, opt_js):
        opts = await cdp.js("[...document.querySelectorAll('[role=\"option\"]')].map(x => x.innerText.trim())")
        raise RuntimeError(f"option not found: {option!r} in {box_label!r}; visible options: {opts}")
    await settle(cdp)


MODE_JS = """(() => { const g = [...document.querySelectorAll('[role="radiogroup"]')]
    .find(x => x.innerText.includes('Live (LLM API)')); if (!g) return null;
    const c = g.querySelector('input:checked'); return c ? c.closest('label').innerText.trim() : null; })()"""


async def choose_mode(cdp, want):
    """want = 'Demo' or 'Live'. Clicks the LLM-page mode radio and VERIFIES the selection."""
    for _ in range(4):
        m = await cdp.js(MODE_JS)
        if m and m.startswith(want):
            return
        await mouse_click(cdp, "[...document.querySelectorAll('[role=\"radiogroup\"] label')]"
                               f".find(l => l.innerText.trim().startsWith({json.dumps(want)}))")
        await settle(cdp, 1.5)
    raise RuntimeError(f"could not select mode {want!r}; current {await cdp.js(MODE_JS)!r}")


async def generate(cdp, want):
    """Click 'Generate explanation' only after re-checking the mode, so a demo capture
    can never trigger a real (billable) LLM call by accident."""
    await choose_mode(cdp, want)
    m = await cdp.js(MODE_JS)
    if not (m and m.startswith(want)):
        raise RuntimeError(f"refusing to click Generate: mode is {m!r}, wanted {want!r}")
    await click(cdp, "Generate explanation")


async def set_number(cdp, label_part, value):
    """Type a value into the number input whose label contains label_part."""
    ok = await mouse_click(cdp, f"""(() => {{ const w = [...document.querySelectorAll('[data-testid="stNumberInput"]')].filter(__vis)
        .find(x => x.innerText.includes({json.dumps(label_part)})); return w && w.querySelector('input'); }})()""")
    if not ok:
        raise RuntimeError(f"number input not found: {label_part!r}")
    await cdp.call("Input.dispatchKeyEvent", type="keyDown", key="a", code="KeyA", modifiers=2,
                   windowsVirtualKeyCode=65, commands=["selectAll"])
    await cdp.call("Input.dispatchKeyEvent", type="keyUp", key="a", code="KeyA", modifiers=2, windowsVirtualKeyCode=65)
    await cdp.call("Input.dispatchKeyEvent", type="keyDown", key="Delete", code="Delete", windowsVirtualKeyCode=46)
    await cdp.call("Input.dispatchKeyEvent", type="keyUp", key="Delete", code="Delete", windowsVirtualKeyCode=46)
    await cdp.call("Input.insertText", text=str(value))
    await cdp.call("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter", windowsVirtualKeyCode=13)
    await cdp.call("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", windowsVirtualKeyCode=13)
    await settle(cdp)


async def shot(cdp, path, max_height=6000, scroll_text=None):
    """Full-content screenshot of the Streamlit page."""
    await cdp.js("(() => { window.scrollTo(0,0); const m=document.querySelector('[data-testid=\"stMain\"]'); if (m) m.scrollTop=0; })()")
    h = await cdp.js("""(() => { const m = document.querySelector('[data-testid="stMain"]') ||
        document.querySelector('section.main'); const c = m && (m.querySelector('[data-testid="stMainBlockContainer"]') || m.firstElementChild);
        return Math.ceil(Math.max(window.innerHeight, (c ? c.scrollHeight + 120 : document.body.scrollHeight))); })()""")
    h = int(min(max(900, h), max_height))
    await cdp.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=h, deviceScaleFactor=SCALE, mobile=False)
    await asyncio.sleep(1.5)
    data = await cdp.call("Page.captureScreenshot", format="png", captureBeyondViewport=False)
    Path(path).write_bytes(base64.b64decode(data["data"]))
    await cdp.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=1000, deviceScaleFactor=SCALE, mobile=False)
    await asyncio.sleep(0.8)
    print("saved", path, f"{int(WIDTH*SCALE)}x{int(h*SCALE)}")


async def assert_no_error(cdp, name):
    err = await cdp.js("""[...document.querySelectorAll('[data-testid="stException"],[data-testid="stAlertContentError"]')]
        .filter(e => e.offsetParent !== null).map(e => e.innerText.slice(0,300))""")
    if err:
        print(f"WARNING {name}: error element visible: {err}")
    return not err


async def run(url, out, live, only_comparison=False, only_llm_live=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    exe = next((b for b in BROWSERS if Path(b).exists()), None)
    if exe is None:
        sys.exit("No Chrome/Edge found")
    prof = tempfile.mkdtemp(prefix="cdp_")
    port = 9333
    proc = subprocess.Popen([exe, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                             "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
                             f"--window-size={WIDTH},1000", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1).read())
                page = next(t for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.3)
        cdp = await CDP.connect(page["webSocketDebuggerUrl"])
        await cdp.call("Page.enable")
        await cdp.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
        await cdp.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=1000, deviceScaleFactor=SCALE, mobile=False)
        await cdp.call("Page.navigate", url=url)
        await asyncio.sleep(6)
        await settle(cdp, 2)
        log = []

        async def take(name, desc, mode="n/a"):
            ok = await assert_no_error(cdp, name)
            await shot(cdp, out / name)
            log.append({"file": name, "shows": desc, "mode": mode, "error_visible": not ok})

        if only_llm_live:
            # one real LLM call on the LLM page (PrivBayes eps=3 seed 42, provider Gemini)
            await nav(cdp, "LLM Knowledge Discovery (extension)")
            await select_option(cdp, "Synthetic dataset to analyse", "PrivBayes | ε=3 (pure ε-DP, δ=0) | seed 42")
            await select_option(cdp, "LLM provider", "Gemini (Google)")
            await generate(cdp, "Live")
            await take("10d_llm_live_gemini_output.png", "Live mode, provider Gemini, PrivBayes eps=3 seed 42: a real LLM response", "live")
            (out / "capture_log_live.json").write_text(json.dumps({"url": url, "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"), "shots": log}, indent=2))
            return
        if only_comparison:
            # Model Comparison must reflect the PUBLISHED log, so capture it before any UI run
            await click(cdp, "Use bundled example dataset")
            await nav(cdp, "Model Comparison")
            await take("09_model_comparison.png", "Model comparison over all logged runs (latest record per run_id)")
            (out / "capture_log_comparison.json").write_text(json.dumps({"url": url, "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"), "shots": log}, indent=2))
            return
        # 1 main dashboard (landing)
        await take("01_main_dashboard.png", "Landing page of the comparative study before a dataset is loaded")
        # 2 dataset
        await click(cdp, "Use bundled example dataset")
        await nav(cdp, "Dataset")
        await take("02a_dataset_overview.png", "Dataset page: bundled UCI Adult sample, profile, target/sensitive selection")
        await click(cdp, "Confirm selections")
        await nav(cdp, "Preprocessing")
        await click(cdp, "Fit preprocessing")
        await take("02b_preprocessing.png", "Preprocessing fitted on the training split only (80/20 stratified)")
        # 3 model selection & generation
        await nav(cdp, "Model Selection & Generate")
        await select_option(cdp, "Method", "PrivBayes")
        await set_number(cdp, "Random seed", 7)
        seed_val = await cdp.js("[...document.querySelectorAll('[data-testid=\"stNumberInput\"] input')].map(i => i.value)")
        print("number inputs before run:", seed_val)
        await click(cdp, "Run generator")
        await take("03_model_selection_generation.png", "PrivBayes, epsilon = 3 (pure DP), seed 7, run from the UI; success message with runtimes")
        if await mouse_click(cdp, _find("button", "Compute TRTR reference", False)):
            await settle(cdp)
        # 4-8 result pages
        await nav(cdp, "Synthetic Data")
        await take("04_synthetic_data_preview.png", "Synthetic-data preview for the UI run")
        await nav(cdp, "Fidelity")
        await take("05_fidelity_evaluation.png", "Fidelity metrics (KS, TVD, correlation, 3-way marginals) for the UI run")
        await nav(cdp, "ML Utility")
        await take("06_ml_utility.png", "TSTR vs TRTR utility for the UI run")
        await nav(cdp, "Privacy")
        await take("07_privacy_evaluation.png", "Formal guarantee panel and empirical privacy (MIA AUC, DCR) for the UI run")
        await nav(cdp, "Fairness / Rare Patterns")
        await take("08_fairness_rare_patterns.png", "Fairness by sex and rare-pattern preservation for the UI run")
        # 09 (Model Comparison) is captured separately with --only-comparison on the published log
        # 10 LLM page
        await nav(cdp, "LLM Knowledge Discovery (extension)")
        await choose_mode(cdp, "Demo")  # the page defaults to Live when a key is configured
        await take("10a_llm_page_dataset_selection.png", "LLM page: DP-only dataset list, guarantee from the log, payload controls")
        await click(cdp, "Exact payload", sel='[data-testid="stExpander"] summary')
        await take("10b_llm_payload_preview.png", "Exact system prompt and aggregate-only payload shown before generation")
        await click(cdp, "Exact payload", sel='[data-testid="stExpander"] summary')
        await generate(cdp, "Demo")
        await take("10c_llm_demo_output.png", "Demo-mode output: deterministic template, labelled NOT generated by an LLM", "demo")
        if live:
            await select_option(cdp, "LLM provider", "Gemini (Google)")
            await generate(cdp, "Live")
            await take("10d_llm_live_gemini_output.png", "Live mode, provider Gemini: a real LLM response", "live")
        (out / "capture_log.json").write_text(json.dumps({"url": url, "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                                          "width_px": int(WIDTH * SCALE), "shots": log}, indent=2))
    finally:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8517")
    ap.add_argument("--out", default=str(Path(__file__).parent))
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--only-comparison", action="store_true")
    ap.add_argument("--only-llm-live", action="store_true", help="ONE real, billable LLM call")
    a = ap.parse_args()
    asyncio.run(run(a.url, a.out, a.live, a.only_comparison, a.only_llm_live))
