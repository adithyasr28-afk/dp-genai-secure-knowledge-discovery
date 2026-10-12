"""
report/references.py

IEEE-style reference strings used by build_report.py. Every entry carries a
`check` field recording how its bibliographic details were confirmed while
drafting:

  "web"    - title, authors, venue and identifiers confirmed against an
             online record (publisher, PMLR, ACL Anthology, VLDB, NIST, DBLP,
             government site) during drafting, October 2026.
  "known"  - long-established reference reproduced from standard metadata;
             not re-checked online. The team should spot-check DOIs/pages.
  "verify" - one or more details (usually DOI or pages) could NOT be
             confirmed; rendered with a [VERIFY] flag in the draft.

Only references actually cited in report/src are printed in the report.
"""

def _r(text, check="known"):
    return {"text": text, "check": check, "verified": check != "verify"}


REFERENCES = {
    # --- Differential privacy foundations -------------------------------------
    "dwork2006": _r('C. Dwork, F. McSherry, K. Nissim, and A. Smith, "Calibrating noise to sensitivity in private data '
                    'analysis," in *Proc. Theory of Cryptography Conf. (TCC)*, LNCS, vol. 3876. Berlin, Germany: Springer, '
                    '2006, pp. 265–284, doi: 10.1007/11681878_14.'),
    "dwork2014": _r('C. Dwork and A. Roth, "The algorithmic foundations of differential privacy," *Found. Trends Theor. '
                    'Comput. Sci.*, vol. 9, no. 3–4, pp. 211–407, 2014, doi: 10.1561/0400000042.'),
    "mcsherry2007": _r('F. McSherry and K. Talwar, "Mechanism design via differential privacy," in *Proc. 48th IEEE Symp. '
                       'Found. Comput. Sci. (FOCS)*, 2007, pp. 94–103, doi: 10.1109/FOCS.2007.66.'),
    "bun2016": _r('M. Bun and T. Steinke, "Concentrated differential privacy: Simplifications, extensions, and lower '
                  'bounds," in *Proc. TCC*, LNCS, vol. 9985. Berlin, Germany: Springer, 2016, pp. 635–658, '
                  'doi: 10.1007/978-3-662-53641-4_24.'),
    "mironov2017": _r('I. Mironov, "Rényi differential privacy," in *Proc. IEEE 30th Comput. Security Found. Symp. (CSF)*, '
                      '2017, pp. 263–275, doi: 10.1109/CSF.2017.11.'),
    "abadi2016": _r('M. Abadi, A. Chu, I. Goodfellow, H. B. McMahan, I. Mironov, K. Talwar, and L. Zhang, "Deep learning '
                    'with differential privacy," in *Proc. ACM SIGSAC Conf. Comput. Commun. Security (CCS)*, 2016, '
                    'pp. 308–318, doi: 10.1145/2976749.2978318.'),
    "ponomareva2023": _r('N. Ponomareva, H. Hazimeh, A. Kurakin, Z. Xu, C. Denison, H. B. McMahan, S. Vassilvitskii, S. Chien, '
                         'and A. G. Thakurta, "How to DP-fy ML: A practical guide to machine learning with differential '
                         'privacy," *J. Artif. Intell. Res.*, vol. 77, pp. 1113–1201, 2023, doi: 10.1613/jair.1.14649.', "verify"),
    "near2025": _r('J. P. Near, D. Darais, N. Lefkovitz, and G. Howarth, "Guidelines for evaluating differential privacy '
                   'guarantees," Nat. Inst. Standards Technol., Gaithersburg, MD, USA, NIST SP 800-226, Mar. 2025, '
                   'doi: 10.6028/NIST.SP.800-226.', "web"),
    "abowd2018": _r('J. M. Abowd, "The U.S. Census Bureau adopts differential privacy," in *Proc. 24th ACM SIGKDD Int. Conf. '
                    'Knowl. Discovery Data Mining*, 2018, p. 2867, doi: 10.1145/3219819.3226070.'),

    # --- DP synthetic data -----------------------------------------------------
    "mckenna2022aim": _r('R. McKenna, B. Mullins, D. Sheldon, and G. Miklau, "AIM: An adaptive and iterative mechanism for '
                         'differentially private synthetic data," *Proc. VLDB Endow.*, vol. 15, no. 11, pp. 2599–2612, 2022, '
                         'doi: 10.14778/3551793.3551817.', "web"),
    "mckenna2021mst": _r('R. McKenna, G. Miklau, and D. Sheldon, "Winning the NIST contest: A scalable and general approach to '
                         'differentially private synthetic data," *J. Privacy Confidentiality*, vol. 11, no. 3, Dec. 2021, '
                         'doi: 10.29012/jpc.778.', "web"),
    "zhang2017privbayes": _r('J. Zhang, G. Cormode, C. M. Procopiuc, D. Srivastava, and X. Xiao, "PrivBayes: Private data '
                             'release via Bayesian networks," *ACM Trans. Database Syst.*, vol. 42, no. 4, Art. no. 25, 2017, '
                             'doi: 10.1145/3134428.', "web"),
    "chen2025bench": _r('K. Chen, X. Li, C. Gong, R. McKenna, and T. Wang, "Benchmarking differentially private tabular data '
                        'synthesis: [Experiments & analysis]," *Proc. ACM Manag. Data (SIGMOD)*, vol. 3, no. 6, 2025, '
                        'doi: 10.1145/3769764.', "web"),
    "tao2021bench": _r('Y. Tao, R. McKenna, M. Hay, A. Machanavajjhala, and G. Miklau, "Benchmarking differentially private '
                       'synthetic data generation algorithms," 2021, *arXiv:2112.09238*.', "web"),
    "jordon2019pategan": _r('J. Jordon, J. Yoon, and M. van der Schaar, "PATE-GAN: Generating synthetic data with differential '
                            'privacy guarantees," in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2019.'),
    "rosenblatt2023": _r('L. Rosenblatt, B. Herman, A. Holovenko, W. Lee, J. Loftus, E. McKinnie, T. Rumezhak, A. Stadnik, '
                         'B. Howe, and J. Stoyanovich, "Epistemic parity: Reproducibility as an evaluation metric for '
                         'differential privacy," *Proc. VLDB Endow.*, vol. 16, no. 11, pp. 3178–3191, 2023, '
                         'doi: 10.14778/3611479.3611517.', "web"),
    "ganev2022": _r('G. Ganev, B. Oprisanu, and E. De Cristofaro, "Robin Hood and Matthew effects: Differential privacy has '
                    'disparate impact on synthetic data," in *Proc. 39th Int. Conf. Mach. Learn. (ICML)*, PMLR, vol. 162, '
                    '2022, pp. 6944–6959.', "web"),
    "stadler2022": _r('T. Stadler, B. Oprisanu, and C. Troncoso, "Synthetic data – Anonymisation groundhog day," in *Proc. 31st '
                      'USENIX Security Symp.*, 2022, pp. 1451–1468.', "web"),
    "lin2024pe": _r('Z. Lin, S. Gopi, J. Kulkarni, H. Nori, and S. Yekhanin, "Differentially private synthetic data via '
                    'foundation model APIs 1: Images," in *Proc. ICLR*, 2024.', "web"),
    "xie2024pe": _r('C. Xie *et al.*, "Differentially private synthetic data via foundation model APIs 2: Text," in *Proc. 41st '
                    'ICML*, PMLR, vol. 235, 2024.', "web"),
    "yue2023": _r('X. Yue, H. A. Inan, X. Li, G. Kumar, J. McAnallen, H. Shajari, H. Sun, D. Levitan, and R. Sim, "Synthetic text '
                  'generation with differential privacy: A simple and practical recipe," in *Proc. 61st Annu. Meeting Assoc. '
                  'Comput. Linguistics (ACL)*, 2023, pp. 1321–1342.', "verify"),

    # --- Non-DP tabular generators -------------------------------------------
    "xu2019ctgan": _r('L. Xu, M. Skoularidou, A. Cuesta-Infante, and K. Veeramachaneni, "Modeling tabular data using '
                      'conditional GAN," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019.'),
    "patki2016sdv": _r('N. Patki, R. Wedge, and K. Veeramachaneni, "The synthetic data vault," in *Proc. IEEE Int. Conf. Data Sci. '
                       'Adv. Anal. (DSAA)*, 2016, pp. 399–410, doi: 10.1109/DSAA.2016.49.'),
    "kotelnikov2023": _r('A. Kotelnikov, D. Baranchuk, I. Rubachev, and A. Babenko, "TabDDPM: Modelling tabular data with '
                         'diffusion models," in *Proc. 40th ICML*, PMLR, vol. 202, 2023, pp. 17564–17579.', "web"),
    "borisov2023": _r('V. Borisov, K. Seßler, T. Leemann, M. Pawelczyk, and G. Kasneci, "Language models are realistic tabular '
                      'data generators," in *Proc. ICLR*, 2023.'),
    "qian2023synthcity": _r('Z. Qian, R. Davis, and M. van der Schaar, "Synthcity: A benchmark framework for diverse use cases '
                            'of tabular synthetic data," in *Adv. Neural Inf. Process. Syst. (NeurIPS) Datasets and Benchmarks '
                            'Track*, vol. 36, 2023.', "web"),
    "hernandez2022": _r('M. Hernandez, G. Epelde, A. Alberdi, R. Cilla, and D. Rankin, "Synthetic data generation for tabular '
                        'health records: A systematic review," *Neurocomputing*, vol. 493, pp. 28–45, 2022, '
                        'doi: 10.1016/j.neucom.2022.04.053.', "web"),

    # --- Attacks and privacy risk in ML / LLMs ---------------------------------
    "shokri2017": _r('R. Shokri, M. Stronati, C. Song, and V. Shmatikov, "Membership inference attacks against machine '
                     'learning models," in *Proc. IEEE Symp. Security Privacy (S&P)*, 2017, pp. 3–18, '
                     'doi: 10.1109/SP.2017.41.'),
    "carlini2022lira": _r('N. Carlini, S. Chien, M. Nasr, S. Song, A. Terzis, and F. Tramèr, "Membership inference attacks from '
                          'first principles," in *Proc. IEEE S&P*, 2022, pp. 1897–1914, doi: 10.1109/SP46214.2022.9833649.'),
    "hilprecht2019": _r('B. Hilprecht, M. Härterich, and D. Bernau, "Monte Carlo and reconstruction membership inference '
                        'attacks against generative models," *Proc. Privacy Enhancing Technol.*, vol. 2019, no. 4, '
                        'pp. 232–249, 2019, doi: 10.2478/popets-2019-0067.'),
    "vanbreugel2023domias": _r('B. van Breugel, H. Sun, Z. Qian, and M. van der Schaar, "Membership inference attacks against '
                               'synthetic data through overfitting detection," in *Proc. 26th Int. Conf. Artif. Intell. Statist. '
                               '(AISTATS)*, PMLR, vol. 206, 2023, pp. 3493–3514.', "web"),
    "fredrikson2015": _r('M. Fredrikson, S. Jha, and T. Ristenpart, "Model inversion attacks that exploit confidence '
                         'information and basic countermeasures," in *Proc. ACM CCS*, 2015, pp. 1322–1333, '
                         'doi: 10.1145/2810103.2813677.'),
    "carlini2021extract": _r('N. Carlini, F. Tramèr, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, '
                             'D. Song, Ú. Erlingsson, A. Oprea, and C. Raffel, "Extracting training data from large language '
                             'models," in *Proc. 30th USENIX Security Symp.*, 2021, pp. 2633–2650.'),
    "carlini2023memorization": _r('N. Carlini, D. Ippolito, M. Jagielski, K. Lee, F. Tramèr, and C. Zhang, "Quantifying '
                                  'memorization across neural language models," in *Proc. ICLR*, 2023.'),
    "lukas2023": _r('N. Lukas, A. Salem, R. Sim, S. Tople, L. Wutschitz, and S. Zanella-Béguelin, "Analyzing leakage of '
                    'personally identifiable information in language models," in *Proc. IEEE S&P*, 2023, pp. 346–363, '
                    'doi: 10.1109/SP46215.2023.10179300.', "verify"),
    "greshake2023": _r('K. Greshake, S. Abdelnabi, S. Mishra, C. Endres, T. Holz, and M. Fritz, "Not what you\'ve signed up for: '
                       'Compromising real-world LLM-integrated applications with indirect prompt injection," in *Proc. 16th ACM '
                       'Workshop Artif. Intell. Security (AISec)*, 2023, pp. 79–90, doi: 10.1145/3605764.3623985.', "verify"),
    "zeng2024rag": _r('S. Zeng *et al.*, "The good and the bad: Exploring privacy issues in retrieval-augmented generation (RAG)," '
                      'in *Findings Assoc. Comput. Linguistics: ACL 2024*, 2024, pp. 4505–4524, '
                      'doi: 10.18653/v1/2024.findings-acl.267.', "web"),
    "yao2024survey": _r('Y. Yao, J. Duan, K. Xu, Y. Cai, Z. Sun, and Y. Zhang, "A survey on large language model (LLM) security '
                        'and privacy: The good, the bad, and the ugly," *High-Confidence Comput.*, vol. 4, no. 2, Art. no. '
                        '100211, 2024, doi: 10.1016/j.hcc.2024.100211.', "web"),
    "weidinger2022": _r('L. Weidinger *et al.*, "Taxonomy of risks posed by language models," in *Proc. ACM Conf. Fairness, '
                        'Accountability, Transparency (FAccT)*, 2022, pp. 214–229, doi: 10.1145/3531146.3533088.'),
    "jagielski2020": _r('M. Jagielski, J. Ullman, and A. Oprea, "Auditing differentially private machine learning: How private '
                        'is private SGD?" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 22205–22216.', "verify"),

    # --- DP for LLMs / generative AI -----------------------------------------
    "li2022llmdp": _r('X. Li, F. Tramèr, P. Liang, and T. Hashimoto, "Large language models can be strong differentially '
                      'private learners," in *Proc. ICLR*, 2022.'),
    "yu2022dpft": _r('D. Yu *et al.*, "Differentially private fine-tuning of language models," in *Proc. ICLR*, 2022.'),
    "tramer2024": _r('F. Tramèr, G. Kamath, and N. Carlini, "Position: Considerations for differentially private learning with '
                     'large-scale public pretraining," in *Proc. 41st ICML*, PMLR, vol. 235, 2024, pp. 48453–48467.', "web"),
    "lewis2020rag": _r('P. Lewis *et al.*, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Adv. Neural '
                       'Inf. Process. Syst. (NeurIPS)*, vol. 33, 2020, pp. 9459–9474.'),
    "kairouz2021fl": _r('P. Kairouz *et al.*, "Advances and open problems in federated learning," *Found. Trends Mach. Learn.*, '
                        'vol. 14, no. 1–2, pp. 1–210, 2021, doi: 10.1561/2200000083.'),

    # --- Fairness, transparency, accountability ------------------------------
    "bagdasaryan2019": _r('E. Bagdasaryan, O. Poursaeed, and V. Shmatikov, "Differential privacy has disparate impact on model '
                          'accuracy," in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019.'),
    "hardt2016": _r('M. Hardt, E. Price, and N. Srebro, "Equality of opportunity in supervised learning," in *Adv. Neural Inf. '
                    'Process. Syst. (NeurIPS)*, vol. 29, 2016.'),
    "mehrabi2021": _r('N. Mehrabi, F. Morstatter, N. Saxena, K. Lerman, and A. Galstyan, "A survey on bias and fairness in '
                      'machine learning," *ACM Comput. Surv.*, vol. 54, no. 6, Art. no. 115, 2021, doi: 10.1145/3457607.'),
    "mitchell2019": _r('M. Mitchell *et al.*, "Model cards for model reporting," in *Proc. Conf. Fairness, Accountability, '
                       'Transparency (FAT\\*)*, 2019, pp. 220–229, doi: 10.1145/3287560.3287596.'),
    "gebru2021": _r('T. Gebru *et al.*, "Datasheets for datasets," *Commun. ACM*, vol. 64, no. 12, pp. 86–92, 2021, '
                    'doi: 10.1145/3458723.'),

    # --- Regulation, standards, frameworks ----------------------------------
    "gdpr2016": _r('"Regulation (EU) 2016/679 of the European Parliament and of the Council of 27 April 2016 (General Data '
                   'Protection Regulation)," *Off. J. Eur. Union*, vol. L 119, pp. 1–88, May 2016.'),
    "euaiact2024": _r('"Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down '
                      'harmonised rules on artificial intelligence (Artificial Intelligence Act)," *Off. J. Eur. Union*, '
                      'OJ L 2024/1689, Jul. 2024.'),
    "dpdp2023": _r('"The Digital Personal Data Protection Act, 2023 (No. 22 of 2023)," *Gazette of India, Extraordinary*, '
                   'Part II, Sec. 1, Ministry of Law and Justice, New Delhi, India, Aug. 11, 2023.', "web"),
    "hipaa2012": _r('U.S. Dept. of Health and Human Services, Office for Civil Rights, "Guidance regarding methods for '
                    'de-identification of protected health information in accordance with the Health Insurance Portability '
                    'and Accountability Act (HIPAA) Privacy Rule," Nov. 2012 (45 CFR §164.514).'),
    "ccpa2018": _r('"California Consumer Privacy Act of 2018," Cal. Civ. Code §1798.100 et seq., as amended by the California '
                   'Privacy Rights Act of 2020.'),
    "nist2020pf": _r('National Institute of Standards and Technology, "NIST Privacy Framework: A tool for improving privacy '
                     'through enterprise risk management, Version 1.0," Jan. 2020, doi: 10.6028/NIST.CSWP.01162020.'),
    "nist2023airmf": _r('National Institute of Standards and Technology, "Artificial intelligence risk management framework '
                        '(AI RMF 1.0)," NIST AI 100-1, Jan. 2023, doi: 10.6028/NIST.AI.100-1.'),
    "iso27701": _r('*Security Techniques — Extension to ISO/IEC 27001 and ISO/IEC 27002 for Privacy Information Management — '
                   'Requirements and Guidelines*, ISO/IEC 27701:2019, International Organization for Standardization, 2019.'),
    "iso42001": _r('*Information Technology — Artificial Intelligence — Management System*, ISO/IEC 42001:2023, International '
                   'Organization for Standardization, 2023.'),

    # --- Data, software ---------------------------------------------------------
    "becker1996adult": _r('B. Becker and R. Kohavi, "Adult," UCI Machine Learning Repository, 1996, doi: 10.24432/C5XW20.'),
    "smartnoise": _r('OpenDP, "SmartNoise synthesizers (smartnoise-synth)," software documentation. [Online]. Available: '
                     'https://docs.smartnoise.org/ (accessed Oct. 2026).'),
    "anthropicapi": _r('Anthropic, "Claude API documentation: Messages API," [Online]. Available: '
                       'https://docs.anthropic.com/ (accessed Oct. 2026).'),
    "geminiapi": _r('Google, "Gemini API documentation: Google Gen AI SDK (google-genai) and generateContent," [Online]. Available: '
                    'https://ai.google.dev/gemini-api/docs (accessed Oct. 2026).'),
}
