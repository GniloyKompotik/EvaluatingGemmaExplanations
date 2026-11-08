# Evaluating the Instructional Quality of Open-Weights Gemma Explanations for Introductory Software Engineering (SE) in Python

**Course:** Research Methods and Tools (RMT) — `SE-2417` (School of Software Engineering, Astana IT University)  
**Authors:** Daniil Khvan, Diyar Amangeldiyev, Yersultan Kambekov  
**Repository:** [https://github.com/GniloyKompotik/EvaluatingGemmaExplanations](https://github.com/GniloyKompotik/EvaluatingGemmaExplanations)  
**Tagged Release:** `assignment-4`  

---

## 1. Purpose & Overview
This repository contains the complete reproducibility package, frozen datasets, automated unit-test execution harnesses, live LLM outputs, statistical analysis scripts, figures, and manuscript files for **Assignment #3** and **Assignment #4** (*Experiment Execution, Results and Discussion*).

Our study evaluates a locally deployed, 4-bit Quantization-Aware Trained open-weights LLM (`lmstudio-community/gemma-4-12B-it-QAT-GGUF` / API ID `google/gemma-4-12b-qat`) across:
1. **Primary SE Rubric Benchmark ($N = 150$ Stratified Tasks):** 50 Syntax Errors, 50 Runtime Debugging, and 50 Basic Algorithms (with full item provenance across Google MBPP, QuixBugs, Think Python 2e, PY4E, Official Python 3.12 Docs, and Stack Overflow SEDE), evaluated by a blinded 3-rater Software Engineering panel and an independent deterministic 27B LLM judge (`lmstudio-community/Qwen3.8-27B-GGUF` / `qwen/qwen3.8-27b`).
2. **Independent QuixBugs Execution & Program Repair Suite ($31$ Algorithms, $242$ JSON Unit Tests):** Sandboxed execution of all 242 unit tests across unpatched buggy baseline programs (`26.45%`), ground-truth references (`89.26%`), 150-item dataset explanations at `max_tokens = 1024` (`10.1%`), and live `google/gemma-4-12b-qat` repairs at `max_tokens = 2048` with concise chain-of-thought (`97.6%`, $41/42$ unit tests passed).
3. **Live Trilingual SE Benchmark (Experiment E5; $10$ Paired Tasks $\times 3$ Languages = $30$ Runs):** Paired evaluation across English (`EN`), Russian (`RU`), and Kazakh (`KK`), measuring functional unit-test `Pass@1` (`100.0%` across all three languages at `max_tokens = 2048`), Language Consistency, Terminology Preservation, internal reasoning token overhead, and 1–5 SE rubric scores.

---

## 2. Repository Structure
```text
EvaluatingGemmaExplanations/
├── README.md                                           # Main documentation & reproduction instructions
├── LICENSE                                             # MIT License + third-party dataset attributions
├── requirements.txt                                    # Pinned Python dependencies
├── .gitignore                                          # Git ignore rules
│
├── Assignment4_Khvan_Amangeldiyev_Kambekov.docx        # Main Assignment #4 submission (Word DOCX)
├── Appendix_A_Experiment_Protocol_Freeze_Form.docx     # Standalone Protocol Freeze Form (Appendix A)
├── Assignment_4_Research_Report.md                     # Markdown version of Assignment #4 report
├── Assignment_3_Khvan_Amangeldiyev_Kambekov.docx        # Revised Assignment #3 submission (Word DOCX)
├── Assignment_3_Research_Paper.md                      # Markdown version of Assignment #3 paper
│
├── reproduce_all_assignment4.py                        # ONE-COMMAND master verification & reproduction script
├── calculate_scores.py                                 # Computes 150-item rubric stats, ICC, kappa, alpha
├── comprehensive_statistical_analysis.py               # Full statistical & execution analysis pipeline
├── run_quixbugs_benchmark.py                           # Runs 242 QuixBugs JSON unit tests + live LLM repair
├── run_multilingual_llm_benchmark.py                   # Runs 30 live trilingual (EN/RU/KK) queries & unit tests
├── patch_truncated_runs.py                             # Runs 2048-token sensitivity/ablation evaluation
├── generate_assignment4_figures_and_stats.py           # Generates all 4 high-res PNG figures in figures/
├── generate_assignment4.py                             # Builds Assignment #4 DOCX & Appendix A files
│
├── dataset_eval_150_rated.csv                          # Frozen 150-task dataset with all 4 raters' scores
├── dataset_eval_150_rated.json                         # Full JSON dataset with prompts, explanations & metadata
├── evaluation_summary_by_category.csv                  # Category-level summary table
├── quixbugs_execution_results.csv                      # Per-algorithm QuixBugs unit-test results (31 algos)
├── quixbugs_live_llm_repairs.json                      # Raw live Gemma-4-12B-QAT QuixBugs repairs & token logs
├── multilingual_real_responses.json                    # Raw live EN/RU/KK responses, reasoning traces & scores
├── multilingual_real_summary.csv                       # Tabular summary of all 30 multilingual runs
│
├── assignment4_verification_log.txt                    # Output of reproduce_all_assignment4.py (Pick-a-Number log)
├── evaluation_summary_report.txt                       # Output of calculate_scores.py
├── statistical_analysis_full_report.txt                # Output of comprehensive_statistical_analysis.py
├── quixbugs_execution_report.txt                       # Output of run_quixbugs_benchmark.py
├── multilingual_real_report.txt                        # Output of run_multilingual_llm_benchmark.py
├── 2026-11-08.1.log                                    # Raw LM Studio llama.cpp server inference log
│
├── figures/                                            # Publication-grade figures (300 DPI PNG)
│   ├── fig1_category_and_baseline_comparison.png
│   ├── fig2_quixbugs_ablation_and_sensitivity.png
│   ├── fig3_multilingual_subgroup_analysis.png
│   └── fig4_human_vs_judge_confusion_matrix.png
└── QuixBugs/                                           # Official QuixBugs benchmark suite & 242 JSON testcases
```

---

## 3. Cryptographic SHA-256 Dataset Hashes (Frozen Protocol)
| File | Items / Scope | SHA-256 Hash |
| :--- | :--- | :--- |
| `dataset_eval_150_rated.csv` | $N = 150$ tasks $\times 4$ evaluators | `3543bbb76d24c3c2d23c8aee71e4531a5a01e7e03597edd4a974926daf80e5d7` |
| `dataset_eval_150_rated.json` | $N = 150$ full responses & metadata | `094eb4b08e798a45981fb45a3141044b7ada8ecceba1a1b22c3f844609d99f31` |
| `quixbugs_execution_results.csv` | $31$ algorithms ($242$ unit tests) | `4176c866c40880fe1a7ab6505314e7bdad97d5f895753eb006db3433f4d5b5c1` |
| `quixbugs_live_llm_repairs.json` | $6$ live QuixBugs repairs ($42$ tests) | `ce0c610c1f714098cd9dd14e586ed84e9a581a895b40723a7cf53ce9a59cf4cf` |
| `multilingual_real_responses.json` | $30$ live EN/RU/KK evaluations | `0c4de70d960611f4920db66a310b0ce56c169cdcf31717977e593b4440256acd` |
| `multilingual_real_summary.csv` | $30$ multilingual summary rows | `e9bd4d4e7780f4ca618921cbe6f463e6ea81b22111fb6fb9ae5a0a156b4a6168` |

---

## 4. Installation & Exact Commands to Reproduce All Results

### Step 1: Clone Repository and Install Dependencies
```bash
git clone https://github.com/GniloyKompotik/EvaluatingGemmaExplanations.git
cd EvaluatingGemmaExplanations
git checkout assignment-4
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: One-Command Offline Reproduction of All Main Tables, Statistical Tests & Figures (<15 seconds, No GPU Required)
```bash
python reproduce_all_assignment4.py
```
This single command:
- Verifies all 6 SHA-256 dataset and log hashes;
- Recomputes all descriptive statistics, 95% bootstrap confidence intervals (`seed=42`), Kruskal-Wallis $H$-tests, Holm-Bonferroni Mann-Whitney $U$ tests, $ICC(2,1)/ICC(2,k)$, Krippendorff's $\alpha$, quadratic/linear weighted $\kappa$, Fisher's exact tests, Friedman $\chi^2$, and Wilcoxon signed-rank tests;
- Regenerates all 4 figures in `figures/`;
- Saves the complete verification output to `assignment4_verification_log.txt`.

### Step 3: Individual Analysis & Document Generation Scripts
```bash
python calculate_scores.py                      # Generates evaluation_summary_report.txt
python comprehensive_statistical_analysis.py    # Generates statistical_analysis_full_report.txt
python generate_assignment4_figures_and_stats.py# Regenerates figures/fig1..fig4.png
python generate_assignment4.py                  # Rebuilds Assignment4_Khvan_Amangeldiyev_Kambekov.docx
```

### Step 4: Re-Running Live LLM Inference & QuixBugs Unit Tests (Requires LM Studio Server on `http://localhost:1235/v1`)
If you wish to re-query the live local `google/gemma-4-12b-qat` model in LM Studio:
```bash
python run_quixbugs_benchmark.py
python run_multilingual_llm_benchmark.py
python patch_truncated_runs.py
```

---

## 5. Oral Defence "Pick-a-Number" Traceability Index
| Reported Number in Report | Value | Log / Data File | Script that Produced It |
| :--- | :--- | :--- | :--- |
| **Grand Mean Overall Score ($N=150$)** | `4.27 ± 0.59 [4.17, 4.36]` | `evaluation_summary_report.txt` | `calculate_scores.py` |
| **Category Means (Syn / Dbg / Alg)** | `4.49 / 3.88 / 4.44` | `evaluation_summary_by_category.csv` | `calculate_scores.py` |
| **Kruskal-Wallis Test (Overall)** | `H = 39.68, p = 2.42e-09, eta^2 = 0.256` | `statistical_analysis_full_report.txt` | `comprehensive_statistical_analysis.py` |
| **Human Panel `ICC(2,k)` (Acc/Comp/Clar)** | `0.868 / 0.877 / 0.883` | `evaluation_summary_report.txt` | `calculate_scores.py` |
| **Human vs. Judge Quad. Weighted $\kappa$** | `0.930 / 0.970 / 0.967` | `evaluation_summary_report.txt` | `calculate_scores.py` |
| **QuixBugs 31-Algorithm Suite Baseline** | `64/242 (26.45%)` vs `216/242 (89.26%)` | `quixbugs_execution_report.txt` | `run_quixbugs_benchmark.py` |
| **QuixBugs 1024-Tok vs. 2048-Tok Live Repair** | `7/69 (10.1%)` vs `41/42 (97.6%)`, `p = 6.34e-22` | `quixbugs_live_llm_repairs.json` | `reproduce_all_assignment4.py` |
| **Multilingual Overall (EN / RU / KK)** | `5.00 / 4.87 / 4.22` (`p = 8.84e-05`) | `multilingual_real_report.txt` | `patch_truncated_runs.py` |
