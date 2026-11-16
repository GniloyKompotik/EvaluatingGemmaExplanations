# Evaluating Quantized Gemma Explanations for Introductory Python Software Engineering: Multi-Rater, Execution, and Trilingual Study

**Course:** Research Methods and Tools (RMT) — `SE-2417` (School of Software Engineering, Astana IT University)  
**Authors:** Daniil Khvan (ORCID: [0009-0008-8946-8094](https://orcid.org/0009-0008-8946-8094)), Diyar Amangeldiyev* (ORCID: [0009-0001-0855-7685](https://orcid.org/0009-0001-0855-7685), corresponding author), Yersultan Kambekov (ORCID: [0009-0009-8176-0856](https://orcid.org/0009-0009-8176-0856))  
**Emails:** `{240656, 241513, 242103}@astanait.edu.kz`  
**Primary Target Scopus Journal:** *IEEE Transactions on Learning Technologies* (ISSN: `1939-1382`, Scopus Q1, 93rd Percentile)  
**Backup Target Scopus Journal:** *ACM Transactions on Computing Education* (ISSN: `1946-6226`, Scopus Q1, 89th Percentile)  
**Repository:** [https://github.com/GniloyKompotik/EvaluatingGemmaExplanations](https://github.com/GniloyKompotik/EvaluatingGemmaExplanations)  
**Tagged Release:** `final` (and `assignment-4`)  
**Reproducibility Archive:** Tagged GitHub Release [`final`](https://github.com/GniloyKompotik/EvaluatingGemmaExplanations/releases/tag/final) (permanent Zenodo archive deposited upon publication)  

---

## 1. Overview & Final Submission Package Deliverables
This repository contains the complete, execution-verified reproducibility package, frozen datasets, automated unit-test harnesses, live LLM outputs, statistical analysis scripts, 300 DPI figures, presentation slides, and Scopus journal submission files for our Final Project.

### Key Deliverables in the Final Submission Package:
1. **Final Research Manuscript (IEEE TLT Template):**
   - [`Final_Research_Manuscript_IEEE_TLT_Khvan_Amangeldiyev_Kambekov.docx`](Final_Research_Manuscript_IEEE_TLT_Khvan_Amangeldiyev_Kambekov.docx) (Complete IMRaD article prepared for *IEEE Transactions on Learning Technologies*, including Tables I–IX, Figures 1–4, 38 DOI-verified IEEE references, and Appendices A–B).
   - [`Final_Research_Manuscript_IEEE_TLT.md`](Final_Research_Manuscript_IEEE_TLT.md) (Markdown version of the complete manuscript).
2. **Journal Fit Statement (Appendix A) & One-Page Cover Letter to the Editor-in-Chief:**
   - [`Appendix_A_Journal_Fit_Statement_and_Cover_Letter.docx`](Appendix_A_Journal_Fit_Statement_and_Cover_Letter.docx) (Scopus verification of *IEEE Transactions on Learning Technologies* and *ACM Transactions on Computing Education* + formal 1-page Cover Letter).
   - [`Cover_Letter_IEEE_TLT_Khvan_Amangeldiyev_Kambekov.docx`](Cover_Letter_IEEE_TLT_Khvan_Amangeldiyev_Kambekov.docx) (Dedicated standalone 1-page Cover Letter).
3. **Submission Readiness Checklist (Appendix B) & Reproduction Record:**
   - [`Appendix_B_Submission_Readiness_Checklist.docx`](Appendix_B_Submission_Readiness_Checklist.docx) (All 15 readiness checks verified + independent reproduction test record).
4. **Final Presentation Slides (10-Slide Widescreen PDF):**
   - [`Final_Presentation_Slides_Khvan_Amangeldiyev_Kambekov.pdf`](Final_Presentation_Slides_Khvan_Amangeldiyev_Kambekov.pdf) (10-minute team defence presentation covering problem/gap, RQ, methods, results with statistics, CoT token ablation, error analysis, limitations, and journal fit).
5. **Individual Defence Guide (Q1–Q6 & Pick-a-Number Traceability Matrix):**
   - [`Individual_Defence_Guide_Q1_to_Q6_and_Pick_a_Number.docx`](Individual_Defence_Guide_Q1_to_Q6_and_Pick_a_Number.docx) and [`Individual_Defence_Guide_Q1_to_Q6_and_Pick_a_Number.md`](Individual_Defence_Guide_Q1_to_Q6_and_Pick_a_Number.md).

---

## 2. Cryptographic SHA-256 Dataset Hashes (Table II in Manuscript)
| File | Items / Scope | SHA-256 Hash |
| :--- | :--- | :--- |
| `dataset_eval_150_rated.csv` | $N = 150$ tasks $\times 4$ evaluators ($600$ evals) | `3543bbb76d24c3c2d23c8aee71e4531a5a01e7e03597edd4a974926daf80e5d7` |
| `dataset_eval_150_rated.json` | $N = 150$ full responses & metadata | `094eb4b08e798a45981fb45a3141044b7ada8ecceba1a1b22c3f844609d99f31` |
| `quixbugs_execution_results.csv` | $31$ algorithms ($242$ official JSON unit tests) | `4176c866c40880fe1a7ab6505314e7bdad97d5f895753eb006db3433f4d5b5c1` |
| `quixbugs_live_llm_repairs.json` | $6$ live QuixBugs repairs ($42$ unit tests) | `ce0c610c1f714098cd9dd14e586ed84e9a581a895b40723a7cf53ce9a59cf4cf` |
| `multilingual_real_responses.json` | $30$ live EN/RU/KK evaluations & CoT traces | `0c4de70d960611f4920db66a310b0ce56c169cdcf31717977e593b4440256acd` |
| `multilingual_real_summary.csv` | $30$ multilingual summary rows | `e9bd4d4e7780f4ca618921cbe6f463e6ea81b22111fb6fb9ae5a0a156b4a6168` |

---

## 3. Exact Commands to Reproduce All Tables (Tables V–IX) and Figures (Figures 1–4)

### Step 1: Clone Repository, Checkout Release Tag `final`, and Install Dependencies
```bash
git clone https://github.com/GniloyKompotik/EvaluatingGemmaExplanations.git
cd EvaluatingGemmaExplanations
git checkout final
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: One-Command Offline Reproduction of All Results Tables, Statistical Tests & Figures (<15s, No GPU Required)
```bash
python reproduce_all_final.py
```
This single command:
1. Verifies all 6 SHA-256 dataset and log hashes (**Table II**);
2. Recomputes all descriptive means, standard deviations, 95% bootstrap confidence intervals (`RandomState(42)`), Kruskal-Wallis $H$-tests, and Holm-Bonferroni Mann-Whitney $U$ tests across $N = 150$ tasks (**Table V**);
3. Recomputes Shrout-Fleiss $ICC(2,1)/ICC(2,k)$, Krippendorff's ordinal $\alpha$, quadratic/linear weighted $\kappa$, Spearman's $\rho$, $\text{MAE}$, and length-bias correlations for the 3-rater human panel and `qwen/qwen3.8-27b` judge (**Table VI**);
4. Recomputes the 242-test QuixBugs execution rates and two-sided Fisher's exact tests across Baseline 1, Baseline 2 (1024-token), and Proposed Concise-CoT (2048-token) (**Table VII**);
5. Recomputes the 30-run trilingual (English, Russian, Kazakh) rubric scores, Pass@1 rates, Friedman $\chi^2$, and Wilcoxon signed-rank tests (**Table VIII**);
6. Verifies the 47-case manual error taxonomy counts across Classes E1–E6 (**Table IX**);
7. Regenerates all 4 high-resolution (300 DPI) figures in `figures/fig1..fig4.png` (**Figures 1–4**);
8. Writes the complete verification audit log to `final_verification_log.txt`.

### Step 3: Rebuild All Final Manuscript DOCX, Appendices & Presentation Slides PDF
```bash
python generate_final_project_package.py        # Rebuilds Final Manuscript DOCX/MD + Appendices A, B, C + Word Count Audit
python generate_final_presentation_pdf.py       # Rebuilds 10-Slide Widescreen Presentation PDF
python calculate_scores.py                      # Generates evaluation_summary_report.txt
python comprehensive_statistical_analysis.py    # Generates statistical_analysis_full_report.txt
```

### Step 4: Re-Running Live LLM Inference & Sandboxed QuixBugs Unit Tests (Requires LM Studio Server on `http://localhost:1235/v1`)
```bash
python run_quixbugs_benchmark.py
python run_multilingual_llm_benchmark.py
python patch_truncated_runs.py
```

---

## 4. Oral Defence "Pick-a-Number" Traceability Matrix
| Manuscript Table / Figure | Reported Statistic / Number | Exact Value | Log / Data File in Repository | Script & Command |
| :--- | :--- | :--- | :--- | :--- |
| **Abstract & Table V** | Grand Mean Overall ($N=150$, 600 evals) | `4.27 ± 0.59 [4.17, 4.36]` | `evaluation_summary_report.txt` | `python calculate_scores.py` |
| **Table V & Fig. 1** | Category Means (Syntax / Runtime / Alg) | `4.49 / 3.88 / 4.44` | `evaluation_summary_by_category.csv` | `python calculate_scores.py` |
| **Table V & Text** | Kruskal-Wallis Omnibus Test (Overall) | `H = 39.68, p = 2.42e-09, eta^2 = 0.256` | `statistical_analysis_full_report.txt` | `python comprehensive_statistical_analysis.py` |
| **Table V & Text** | Mann-Whitney U (Holm): Alg/Syn vs. Dbg | `U = 2033.0 (p = 1.88e-07); U = 2009.5 (p = 3.17e-07)` | `final_verification_log.txt` | `python reproduce_all_final.py` |
| **Table VI** | Human Panel `ICC(2,k)` (Acc/Comp/Clar) | `0.868 / 0.877 / 0.883` | `evaluation_summary_report.txt` | `python calculate_scores.py` |
| **Table VI & Fig. 4a** | Judge vs. Human Quad. Weighted $\kappa$ | `0.930 / 0.970 / 0.967` (`MAE = 0.144–0.180`) | `evaluation_summary_report.txt` | `python calculate_scores.py` |
| **Table VII & Fig. 2** | QuixBugs 31-Algorithm Suite (242 Tests) | `64/242 (26.45%)` Buggy vs. `216/242 (89.26%)` Ref | `quixbugs_execution_report.txt` | `python run_quixbugs_benchmark.py` |
| **Table VII & Fig. 2** | QuixBugs 1024-Tok vs. 2048-Tok Repair | `7/69 (10.1%)` vs. `41/42 (97.6%)`, `OR = 363.1, p = 6.34e-22` | `quixbugs_live_llm_repairs.json` | `python reproduce_all_final.py` |
| **Table VIII & Fig. 3** | Trilingual Overall (EN / RU / KK) | `5.00 / 4.87 / 4.22` (`Friedman chi^2 = 18.67, p = 8.84e-05`) | `multilingual_real_report.txt` | `python reproduce_all_final.py` |
| **Table IX & Fig. 4b** | Manual Error Taxonomy ($N = 47$ Cases) | `E1=22 (46.8%), E2=8 (17.0%), E3=6 (12.8%), E4=5, E5=4, E6=2` | `final_verification_log.txt` | `python reproduce_all_final.py` |

---

## 5. Data & Code Availability, Open Licenses, and Privacy Confirmation
- **Code License:** MIT License (`LICENSE`).
- **Benchmark Provenance Licenses:** Google Research MBPP (Apache 2.0), QuixBugs (MIT), Stack Overflow SEDE excerpts (CC BY-SA 4.0).
- **Privacy & Security Confirmation:** Confirmed that zero personal data, student records, API keys, or confidential material are included in this repository.
