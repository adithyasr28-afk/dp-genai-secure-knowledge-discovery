# Student action items

Everything below needs the team. Technical work is complete.

## 1. Before anything else
- [ ] **Rotate the Gemini API key.** It was pasted into a chat on 2026-10-11. It is not in the repository or its history, but treat it as exposed. Create a new key in Google AI Studio, delete the old one, and update `.env` (never commit it).

## 2. Missing details in the report
Edit `report/build_report.py` (`FRONT` and `MEMBERS`), then run `python report/finalize.py`, or edit the DOCX directly.
- [ ] **VIT e-mails** for Amy Jose, Swetha and Adithya Shaji (`FRONT["emails"]`; placeholders `[VIT e-mail]`).
- [ ] **Contributions table:** the registration number responsible for each section (`[Reg. No.]`).
- [ ] **Consolidated contributions:** the words contributed by each student (`[words]`).
- [ ] **Acknowledgment:** keep or adjust the AI-assistance disclosure to match the course policy.

## 3. Writing and formatting
- [ ] **Humanise and proofread** the whole text in your own words. Keep every number, citation and caveat unchanged; the numbers come from `results/verified/`.
- [ ] **Minor Word formatting:** heading spacing, widows and orphans, any figure that lands awkwardly in a column.
- [ ] If you add, remove or reorder equations, **renumber them by hand**. The numbers (1)–(15) are typed text.
- [ ] If you edit the DOCX directly, **update the page numbers** in the Index, List of Figures and List of Tables afterwards. `finalize.py` fills them only when you rebuild.

## 4. Diagrams (guideline: re-draw in draw.io, ≥ 600 DPI, "Fig NN <Name>")
The diagrams are code-generated with editable `.drawio` sources in `diagrams/` and `figures/diagrams/`. Restyle or redraw these 16 in draw.io and export at ≥ 600 DPI:

| Report fig. | File | Note |
|---|---|---|
| 1 | Fig 01 Generative AI privacy risk landscape | keep the attribution "adapted from [23][24]" |
| 2 | Fig 02 Secure knowledge-discovery ecosystem | |
| 3 | Fig 03 Data lifecycle and privacy classification framework | |
| 4 | Fig 04 Threat model and attack surface | |
| 5 | Fig 05 Implemented DP-enhanced generative AI framework | |
| 6 | Fig 06 Privacy-aware data preparation pipeline | |
| 7 | Fig 07 Differential privacy integration workflow | the DP-SGD part must stay labelled "not implemented" |
| 8 | Fig 08 Knowledge-discovery workflow | |
| 9 | Fig 09 Explainability, transparency and trust assessment layer | |
| 10 | Fig 10 Experimental evaluation framework | |
| 12 | Fig 12 Compliance and governance mapping | |
| 13 | Fig 13 Trustworthy privacy-preserving generative AI lifecycle | |
| 14 | Fig 14 Proposed domain-specific deployment architecture | keep the dashed "not implemented" components |
| 15 | Fig 15 Future research roadmap | |
| 16 | Fig 16 Requirements framework (appendix) | |

The result charts (Figs 11, 17–26) are data plots generated from `results/verified/`. **Do not redraw them by hand.** Regenerate them with `python -m analysis.verify_results` if needed.

## 5. Checks and recordings
- [ ] **Similarity check** with the authorised tool, after the rewrite. It must be ≤ 10%. No percentage has been measured.
- [x] **Execution video:** recorded 16 Oct 2026 as `evidence/videos/execution_demo_2026-10-16.mp4` (3 min 37 s), added to GitHub. Original recording instructions kept below for reference.
- [x] ~~Execution video~~, following `project_docs/DEMO_GUIDE.md` and `evidence/videos/README.md`:
  - select *Demo* on the LLM page unless a live call is intended;
  - use a non-sweep seed (e.g. 7);
  - hide the key and `.env`;
  - run `git checkout -- results/` afterwards.
- [x] **Review the video** for exposed keys: 16 sampled frames checked on 16 Oct 2026; no key, `.env` or terminal visible.

## 6. Questions for Dr M Rajasekhara Babu
- [ ] Abstract (242 words) versus "Executive Summary and Abstract" (450–750): both are provided. Which is graded?
- [ ] The 80% journal-reference target: 32% achieved, with the reasons in `final_compliance_matrix.md`. Is this acceptable?
- [ ] Do code-generated diagrams with editable draw.io sources satisfy "re-draw using draw.io"?

## 7. Optional
- [ ] Merge `report-finalisation` into `main` on GitHub after review.
- [ ] Archive a release on Zenodo and cite its DOI in the Data Availability Statement.
- [ ] Test the Claude provider live with an Anthropic key.
