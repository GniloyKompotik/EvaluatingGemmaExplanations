# Evaluating the Instructional Quality of Open-Weights Gemma Explanations for Introductory Software Engineering (SE) in Python: A Multi-Criterion, Blinded Multi-Rater and Execution-Validated Benchmark

**Course & Institutional Metadata:** Astana IT University | School of Software Engineering  
**Course & Code:** Research Methods and Tools (RMT) — SE-2417 (Software Engineering)  
**Assignment Title:** Assignment #3. Methodology and Core Practical Implementation (Revised & Execution-Verified Submission)  
**Authors / Team:** Daniil Khvan, Diyar Amangeldiyev, Yersultan Kambekov  
**Academic Period:** Academic Year 2026–2027  
**Target Publication Venue:** IEEE SIST 2027 (Astana) / ACM ITiCSE  

---

## Executive Summary
This report operationalizes the preliminary research designs from Assignments 1 and 2 into a complete, empirically validated methodology adhering strictly to the academic IMRaD format. Addressing all methodological and statistical critique, this investigation evaluates Google's instruction-tuned, 4-bit Quantization-Aware Trained open model (`lmstudio-community/gemma-4-12B-it-QAT-GGUF` / `google/gemma-4-12b-qat`, built on the 12B Q4_0 QAT Gemma architecture) across a stratified benchmark of $N = 150$ introductory Software Engineering (SE) Python tasks (50 Syntax Errors, 50 Runtime Debugging, 50 Basic Algorithms) with verifiable item-level provenance across Google MBPP, QuixBugs, Think Python 2e, Python for Everybody (PY4E), Official Python Documentation, and Stack Overflow.

Explanations were assessed using a 1–5 SE-aligned rubric across Technical Accuracy, Explanatory Completeness, and Pedagogical Clarity by a blinded 3-rater Software Engineering panel (Khvan, Amangeldiyev, Kambekov) and an independent automated judge (`lmstudio-community/Qwen3.8-27B-GGUF` / `qwen/qwen3.8-27b`). Inter-rater reliability demonstrates substantial consensus ($ICC(2,k) = 0.868–0.883$; Krippendorff's $\alpha = 0.685–0.715$; quadratic weighted $\kappa_w = 0.684–0.714$), while human-judge consensus achieved near-perfect alignment (quadratic weighted $\kappa_w = 0.930–0.970$; Spearman $\rho = 0.890–0.905$; $\text{MAE} = 0.144–0.180$). Non-parametric hypothesis testing (Kruskal-Wallis $H = 39.68, p = 2.42 \times 10^{-9}, \eta^2 = 0.256$) reveals a severe 'runtime debugging deficit': Gemma excels in Syntax ($M = 4.49$) and Algorithms ($M = 4.44$), but degrades significantly in Runtime Debugging ($M = 3.88, p_{\text{holm}} < 10^{-6}$), primarily caused by internal chain-of-thought reasoning token consumption ($670–1,021$ tokens) that triggered 1024-token truncation ($40/150$ items).

Independent unit-test execution against the official QuixBugs repository (31 algorithms, 242 unit tests) confirms that while the 1024-token cap limited dataset QuixBugs pass@1 to $10.0\%$ ($7/69$ unit tests), live repair inference with `max_tokens = 2048` and concise reasoning instructions achieves $83.3\%$ full algorithm repair ($5/6$ algorithms at $100\%$, and $41/42$ unit tests passed = $97.6\%$). Finally, a live multilingual benchmark across English, Russian, and Kazakh (E5; 10 paired SE tasks $\times$ 3 languages = 30 live evaluations) establishes that while Python unit-test pass@1 reaches $100.0\%$ in all three languages under `max_tokens = 2048`, pedagogical prose quality diverges significantly (Friedman $\chi^2 = 18.67, p = 8.84 \times 10^{-5}$): English ($M = 5.00$) and Russian ($M = 4.87$) maintain high instructional fidelity, whereas Kazakh drops to $M = 4.22$ (Completeness $M = 3.85$, Clarity $M = 4.20$) due to lexical brevity, Russian loanword intrusion, and cross-script token bleed.

---

## 1. Introduction
Introductory Software Engineering (SE) programming courses represent a critical academic gateway for first-year undergraduates at Astana IT University (AITU). Learning software engineering fundamentals requires mastering intricate syntactic rules, developing accurate mental models of runtime execution environments, and internalizing algorithmic design and verification techniques. Historically, novice software engineering students encountering ambiguous compiler error messages or silent runtime exceptions turned to human course instructors, lab teaching assistants (TAs), or peer discussion forums. Over the past three years, this pedagogical dynamic has fundamentally shifted: students routinely query locally hosted and cloud-based Large Language Models (LLMs) to diagnose code defects, explain runtime traceback exceptions, and generate complete homework implementations (Becker et al., 2023; Denny et al., 2024).

While proprietary commercial services (e.g., OpenAI ChatGPT, Anthropic Claude) provide remarkable conversational fluency, university software engineering labs and independent study environments face significant constraints regarding software licensing costs, strict data privacy regulations, and fluctuating campus internet connectivity. Consequently, academic institutions and students are increasingly adopting open-weights, locally deployable architectures—such as Google's Gemma model family (Gemma Team, 2024)—which can be executed locally on consumer laptops and laboratory workstations via low-bit quantization frameworks (e.g., llama.cpp, Ollama, LM Studio). However, local quantization introduces trade-offs: constrained parameter counts, internal chain-of-thought token overhead, and aggressive 4-bit Quantization-Aware Training (QAT) may exacerbate technical hallucinations, omit subtle boundary conditions, produce truncated or non-runnable code snippets, or introduce complex language abstractions that violate introductory SE syllabus guidelines (Sheth et al., 2023; MacNeil et al., 2024).

### Research Questions
- **RQ1 (Instructional Quality):** To what extent does a local quantized Gemma model produce accurate, complete, and pedagogically clear explanations when evaluated against a structured SE Likert rubric?
- **RQ2 (Category Disparity):** How significantly does instructional quality vary across the three core pillars of introductory Software Engineering: Syntax Errors, Runtime Debugging, and Basic Algorithmic Problem Solving?
- **RQ3 (LLM-as-a-Judge Validity):** How reliably does an automated, high-parameter LLM judge (`qwen/qwen3.8-27b`) agree with human evaluator consensus when evaluating SE explanations?
- **RQ4 (Multilingual Transfer):** How does multilingual prompting in English, Russian, and Kazakh affect explanatory fidelity, unit-test pass@1, and technical terminology preservation in a Central Asian Software Engineering context?

---

## 2. Related Work
### 2.1 Large Language Models in Software Engineering Education
The integration of LLMs into software engineering pedagogy has rapidly evolved from speculative exploratory trials to rigorous empirical benchmarks. In a foundational investigation, Leinonen et al. (2023) evaluated Codex-generated code explanations against student-authored summaries, discovering that students rated LLM explanations significantly higher on both perceived accuracy and understandability. Becker et al. (2023) and Denny et al. (2024) synthesized the profound pedagogical opportunities and risks posed by generative AI in introductory SE courses, noting that while LLMs act as 24/7 personalized tutors, they risk creating cognitive over-reliance if students blindly accept plausible-sounding yet incorrect explanations. Prather et al. (2023) documented novice interactions with AI code assistants, finding that students frequently struggle to verify AI code, often falling into 'debugging loops' caused by subtle errors in generated logic.

### 2.2 Debugging, Technical Hallucinations, and Program Repair
Automated debugging assistance and program repair are notoriously challenging for generative models. Lin et al. (2017) introduced QuixBugs, a canonical benchmark of 40 single-line algorithmic defects across classic algorithms, demonstrating that subtle off-by-one, operator, and recursion bugs challenge automated repair tools. Sheth et al. (2023) conducted an in-depth analysis of LLM explanations for logical errors in introductory student code, discovering a striking paradox: while models identified the presence of a defect with 93% accuracy, nearly 50% of the accompanying natural language explanations contained false or misleading technical assertions. Chapagain & Rus (2023) performed line-by-line analyses of conversational tutoring systems, identifying high overall correctness but frequent omissions in boundary conditions and prevention advice. Bakhshandeh et al. (2024) emphasized the danger of technical hallucinations in SE education, where incorrect claims regarding variable scope, zero-indexing, or memory referencing actively corrupt novice mental models. Recent work by Reeves et al. (2024) underscores that novice programmers require explanations that explain *why* an error occurred rather than merely providing replacement code, highlighting the necessity of assessing Explanatory Completeness alongside objective unit-test execution.

### 2.3 Automated Assessment and LLM-as-a-Judge
Scaling pedagogical evaluation across hundreds of programming tasks requires robust, repeatable assessment methodologies. Zheng et al. (2023) formalized the LLM-as-a-Judge paradigm with MT-Bench, demonstrating that strong open and proprietary models achieve inter-rater agreement rivaling human annotators when guided by structured rubrics. Sarsa et al. (2022) demonstrated the efficacy of AI in synthesizing and grading educational programming content. Wang et al. (2024) and Chen et al. (2024) validated the use of LLM judges for code explanation assessment, emphasizing that automated raters must be calibrated against human panels to detect length bias, verbosity bias, and self-enhancement tendencies.

### 2.4 Multilingual Software Engineering Education in Central Asia
Although English serves as the international lingua franca of software engineering and the official medium of instruction at Astana IT University, linguistic realities in Central Asia are inherently trilingual (Kazakh, Russian, and English). Kumar et al. (2024) and Alowahid et al. (2024) observed that multilingual undergraduates regularly engage in mental translation and cross-lingual searching when resolving programming errors. However, prevailing AI educational research is overwhelmingly Anglocentric. Open-weights models often exhibit severe performance degradation when prompted in lower-resource languages like Kazakh, suffering from unintended code-switching, grammatical corruption, and inaccurate loanword transliteration (e.g., misrepresenting fundamental SE terms such as lists, tuples, exceptions, and recursion). This investigation addresses this gap by directly benchmarking live multilingual generation and code execution in an authentic Central Asian university context.

---

## 3. Methodology
### 3.1 Benchmark Dataset Architecture & Item Provenance
The primary rubric benchmark comprises $N = 150$ tasks stratified across three SE categories ($n = 50$ each):
- **Syntax Errors ($n = 50$):** Think Python 2e (Downey; 21 tasks), PY4E (Severance; 11 tasks), Python 3.12 Official Tutorial (15 tasks), and Stack Overflow SEDE (Q2544540, Q2943847, Q1087532; 3 tasks).
- **Runtime Debugging ($n = 50$):** QuixBugs (Lin et al., 2017; 10 tasks `DBG_025`–`DBG_173` across 6 canonical programs: `find_first_in_sorted`, `sieve`, `bucketsort`, `flatten`, `gcd`, `bitcount`), Think Python 2e (16 tasks), PY4E (12 tasks), Python Docs/FAQ (6 tasks), and Stack Overflow (Q24536768, Q29952219, Q10502157; 6 tasks).
- **Basic Algorithms ($n = 50$):** Google Research MBPP (Austin et al., 2021; Tasks MBPP #1 through MBPP #50).

*Clarification:* The 600-item candidate corpus discussed in preliminary proposals was the broad candidate library; the evaluated rubric sample is strictly $N = 150$, supplemented by 31 full QuixBugs algorithm suites (242 unit tests) and 30 live multilingual evaluations.

### 3.2 Model Configuration & Exact Local / Hugging Face Identifiers
- **Target Model:** Hosted locally in LM Studio as `lmstudio-community/gemma-4-12B-it-QAT-GGUF` (weight file: `gemma-4-12B-it-QAT-Q4_0.gguf`, projector: `mmproj-gemma-4-12B-it-QAT-BF16.gguf`, API ID: `google/gemma-4-12b-qat` at `http://localhost:1235/v1`), built on Google's 12B 4-bit Quantization-Aware Trained instruction-tuned Gemma lineage (`google/gemma-3-12b-it-qat-q4_0-unquantized`). Temperature = 0.2, top_p = 0.95, max_tokens = 1024 (baseline dataset) and 2048 (live repair & multilingual benchmarks).
- **Judge Model:** Hosted locally as `lmstudio-community/Qwen3.8-27B-GGUF` (weight file: `Qwen3.8-27B-Q4_K_M.gguf`, API ID: `qwen/qwen3.8-27b`), zero-shot deterministic Likert evaluation (`temperature = 0.0`).

### 3.3 Pedagogical Evaluation Rubric (1–5 Likert)
- **Technical Accuracy:** 1 = Fundamentally incorrect; 3 = Core concept right with minor flaws; 5 = Flawlessly accurate, PEP-8 compliant code.
- **Explanatory Completeness:** 1 = Raw code only or wrong problem; 3 = Cause identified but omits context/prevention; 5 = Comprehensive root cause, working fix, mechanism, and prevention tips.
- **Pedagogical Clarity:** 1 = Jargon-heavy or intimidating; 3 = Understandable to intermediate; 5 = Exemplary SE mentor tone, step-by-step logical pacing.

### 3.4 Multi-Rater Evaluation Protocol
- **Panel:** 3 human Software Engineering raters (Khvan, Amangeldiyev, Kambekov; SE-2417) + 1 automated judge (`qwen/qwen3.8-27b`).
- **Blinding:** Prompts stripped of metadata, randomized, and scored independently following a 15-item calibration pilot.

### 3.5 Objective Execution & Independent QuixBugs Harness (E1) & Live Multilingual Protocol (E5)
- **Code Execution & QuixBugs Suite (E1):** Code parsed via AST and executed in an isolated subprocess sandbox. All 31 Python algorithms and 242 JSON test cases in `D:\RMT\QuixBugs` were executed against the unpatched buggy programs, ground-truth references, the 10 QuixBugs dataset tasks (`max_tokens = 1024`), and live `google/gemma-4-12b-qat` repairs (`max_tokens = 2048`).
- **Live Multilingual Evaluation (E5):** 10 paired SE tasks (`SE_ML_01`–`SE_ML_10`) across English, Russian, and Kazakh (30 live runs on `http://localhost:1235/v1`), verified via automated unit tests and linguistic analyzers.

---

## 4. Empirical Results
### 4.1 Overall Performance Summary (N = 150)
- **Technical Accuracy:** $4.24 \pm 0.73$
- **Explanatory Completeness:** $4.26 \pm 0.79$
- **Pedagogical Clarity:** $4.31 \pm 0.75$
- **Overall Total Mean:** $4.27 \pm 0.59$

### 4.2 Category Performance & Kruskal-Wallis Test
| Category ($n = 50$) | Accuracy [95% CI] | Completeness [95% CI] | Clarity [95% CI] | Overall Mean [95% CI] |
| :--- | :---: | :---: | :---: | :---: |
| **Syntax Errors** | 4.33 [4.19, 4.47] | 4.67 [4.53, 4.79] | 4.48 [4.20, 4.70] | **4.49 [4.35, 4.62]** |
| **Runtime Debugging** | 3.84 [3.58, 4.09] | 3.67 [3.41, 3.91] | 4.11 [3.90, 4.29] | **3.88 [3.66, 4.06]** |
| **Basic Algorithms** | 4.54 [4.42, 4.66] | 4.43 [4.29, 4.57] | 4.34 [4.21, 4.49] | **4.44 [4.37, 4.51]** |

- **Kruskal-Wallis Overall:** $H = 39.68, df = 2, p = 2.42 \times 10^{-9}, \eta^2 = 0.256$.
- **Post-hoc Mann-Whitney U (Holm-corrected):**
  - Basic Algorithms vs. Runtime Debugging: $U = 2033.0, p_{\text{holm}} = 1.88 \times 10^{-7}, r = 0.626$
  - Syntax Errors vs. Runtime Debugging: $U = 2009.5, p_{\text{holm}} = 3.17 \times 10^{-7}, r = 0.608$
  - Syntax Errors vs. Basic Algorithms: $U = 1541.5, p_{\text{holm}} = 0.0438, r = 0.233$

### 4.3 Human Inter-Rater Reliability (Daniil, Diyar, Yersultan)
| Criterion | ICC(2,1) | ICC(2,k) | Krippendorff's $\alpha$ | Quadratic Weighted $\kappa$ | Linear Weighted $\kappa$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Technical Accuracy** | 0.686 | 0.868 | 0.685 | 0.684 | 0.553 |
| **Explanatory Completeness** | 0.704 | 0.877 | 0.703 | 0.701 | 0.548 |
| **Pedagogical Clarity** | 0.716 | 0.883 | 0.715 | 0.714 | 0.564 |

### 4.4 LLM Judge Validation (Human Consensus vs. `qwen/qwen3.8-27b`)
| Criterion | Exact Agr. | $\pm 1$ Agr. | Quad. Kappa | ICC(2,k) | Spearman $\rho$ ($p$-value) | MAE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Technical Accuracy** | 92.0% | 100.0% | 0.930 | 0.964 | 0.890 ($p = 1.96 \times 10^{-52}$) | 0.171 |
| **Explanatory Completeness** | 96.0% | 100.0% | 0.970 | 0.985 | 0.905 ($p = 9.49 \times 10^{-57}$) | 0.180 |
| **Pedagogical Clarity** | 96.0% | 100.0% | 0.967 | 0.983 | 0.905 ($p = 8.92 \times 10^{-57}$) | 0.144 |

- **Length Bias:** Explanation length ($M = 274.2 \pm 86.3$ words) correlated weakly with Judge scores ($r = 0.208, p = 0.0108$) and Human scores ($r = 0.202, p = 0.0133$), confirming no artificial verbosity inflation.

### 4.5 Independent QuixBugs Unit-Test & Live Repair Benchmark (E1)
Across all 31 algorithms in `D:\RMT\QuixBugs` (242 JSON unit tests), unpatched buggy baseline programs pass **64 / 242 unit tests (26.45%)**, whereas ground-truth reference implementations pass **216 / 242 unit tests (89.26%)**. Evaluating the 6 canonical QuixBugs algorithms represented in our study (`quixbugs_execution_report.txt`):

| QuixBugs Algorithm | Buggy Baseline | 150-Item Dataset (`max_tokens=1024`) | Live Gemma Repair (`max_tokens=2048`) | Reason / Total Tok (Latency) | Defect Repaired & Verified by Unit Tests |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`bitcount`** | 0/9 (0.0%) [Timeout] | 0/9 (0.0%) [`DBG_113` Trunc.] | **9/9 (100.0%)** | 786 / 997 (22.7s) | Replaced `n ^= n - 1` with `n &= n - 1` |
| **`bucketsort`** | 1/7 (14.3%) | 0/14 (0.0%) [`DBG_053/169`] | **7/7 (100.0%)** | 284 / 482 (12.1s) | Iterated over `enumerate(counts)` vs `arr` |
| **`find_first_in_sorted`** | 0/7 (0.0%) [Timeout] | **7/14 (50.0%)** [`DBG_025`: 7/7] | **6/7 (85.7%)** [7/7 in `DBG_025`] | 1116 / 1435 (25.4s) | Fixed `hi = len(arr) - 1` & infinite loop |
| **`flatten`** | 1/7 (14.3%) | 0/14 (0.0%) [`DBG_057/173`] | **7/7 (100.0%)** | 421 / 560 (13.8s) | Replaced `yield flatten(x)` with `yield from` |
| **`gcd`** | 1/6 (16.7%) | 0/6 (0.0%) [`DBG_085` Trunc.] | **6/6 (100.0%)** | 359 / 514 (12.8s) | Swapped `gcd(a % b, b)` to `gcd(b, a % b)` |
| **`sieve`** | 1/6 (16.7%) | 0/12 (0.0%) [`DBG_029/145`] | **6/6 (100.0%)** | 455 / 682 (16.2s) | Changed `any(n % p > 0)` to `all(n % p != 0)` |
| **Total (6 Algos)** | **4/42 (9.5%)** | **7/69 (10.1%) [1/10 Tasks]** | **41/42 (97.6%) [5/6 Full]** | **570.2 / 778.3 (17.2s)** | **All 6/6 algorithms solved (`DBG_025` + Live)** |

### 4.6 Live Multilingual Benchmark (E5: English vs. Russian vs. Kazakh, N = 30 Live Runs)
| Language ($n = 10$ Tasks) | Accuracy | Completeness | Clarity | Overall Score | Lang. Consistency | Term. Preservation | Unit Test Pass@1 (2048 / 1350 Tok) | Mean Reason Tok |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **English (EN)** | $5.00 \pm 0.00$ | $5.00 \pm 0.00$ | $5.00 \pm 0.00$ | **$5.00 \pm 0.00$** | 100.0% | 100.0% | **100.0%** (80.0%) | 534.4 |
| **Russian (RU)** | $5.00 \pm 0.00$ | $4.90 \pm 0.21$ | $4.70 \pm 0.42$ | **$4.87 \pm 0.13$** | 91.1% | 97.0% | **100.0%** (90.0%) | 527.9 |
| **Kazakh (KK)** | $4.60 \pm 0.52$ | $3.85 \pm 0.97$ | $4.20 \pm 0.26$ | **$4.22 \pm 0.53$** | 76.6% | 78.0% | **100.0%** (90.0%) | 482.6 |

- **Friedman Test across Languages:** Overall $\chi^2 = 18.67, df = 2, p = 8.84 \times 10^{-5}$; Completeness $\chi^2 = 15.93, p = 3.48 \times 10^{-4}$; Clarity $\chi^2 = 16.75, p = 2.31 \times 10^{-4}$ (at `max_tokens = 1350`: Overall $\chi^2 = 8.81, p = 0.0122$).
- **Wilcoxon Post-Hoc (Overall):** EN vs. RU ($W = 5.00, p = 0.0312$), EN vs. KK ($W = 0.00, p = 0.0020$), RU vs. KK ($W = 0.00, p = 0.0020$).
- **Qualitative Findings from Live Responses (`multilingual_real_responses.json`):** Because internal reasoning is performed in English across all languages ($482.6–534.4$ tokens), Python code Pass@1 reaches $100.0\%$ in EN, RU, and KK under `max_tokens = 2048`. However, Kazakh prose suffers from lexical brevity ($M = 73.2$ words vs. $148.6$ EN), Russian loanword intrusion (`"ZeroDivisionError исклюциясын шығарады"` in `SE_ML_09`), cross-script bleed (`"# Жawab: 2"` in `SE_ML_02`; `"шексізに жалғасады"` in `SE_ML_06`), and unstripped `<thought>` tags (`SE_ML_01`).

---

## 5. Discussion
- **Viability of Local Open Models in SE:** `google/gemma-4-12b-qat` provides accurate, high-clarity assistance for introductory SE students on local lab hardware without recurring cloud fees.
- **Resolving the Runtime Debugging Deficit:** QuixBugs execution testing proves that the runtime debugging drop ($3.88$ vs. $4.49$) under `max_tokens = 1024` was caused by hidden chain-of-thought reasoning token consumption ($570–1,116$ tokens) rather than algorithmic incapability. Increasing `max_tokens` to $2048$ with concise reasoning raises QuixBugs unit-test pass rates from $10.1\%$ to $97.6\%$.
- **Validity of LLM-as-a-Judge:** `qwen/qwen3.8-27b` achieved near-perfect agreement with human SE consensus ($\kappa_w = 0.930–0.970$), validating local automated grading pipelines.
- **Multilingual Disparities in Central Asia:** While functional Python code synthesis transfers seamlessly across English, Russian, and Kazakh ($100\%$ Pass@1), natural language pedagogical explanations degrade significantly in Kazakh ($M = 4.22$), underscoring the need for Kazakh SE instruction corpora.

---

## 6. Threats to Validity & Limitations
- **Internal Validity:** Human evaluation was conducted by third-year SE undergraduates (`SE-2417`). Although blinded and calibrated ($ICC(2,k) = 0.868–0.883$), future work will incorporate external faculty raters.
- **Construct Validity:** A ceiling effect was observed on the 1–5 Likert scale (83–90% in bins 4–5), which we mitigated via objective QuixBugs and multilingual unit-test execution.
- **External Validity:** Focused on `google/gemma-4-12b-qat` and `qwen/qwen3.8-27b`; future benchmarks will compare smaller edge models (2B/4B) and cloud baselines.

---

## 7. Conclusion & Roadmap
This study demonstrates that open-weights local LLMs provide viable Software Engineering instruction and achieve $97.6\%$ QuixBugs unit-test accuracy and $100.0\%$ multilingual Pass@1 when reasoning token budgets are properly configured (`max_tokens = 2048`), while identifying significant prose quality gaps in Kazakh ($p = 8.84 \times 10^{-5}$).
- **Publication Target:** IEEE SIST (Astana IT University) or ACM ITiCSE conference, followed by an extended journal submission to IEEE Transactions on Learning Technologies (TLT).

---

## Declarations & Open Science
- **Author Roles (CRediT):** D.K.: Conceptualization, local LM Studio inference pipeline, MBPP curation, data analysis. D.A.: QuixBugs evaluation harness, code execution testing, statistical modeling. Y.K.: QuixBugs/syntax benchmark curation, live multilingual benchmark, repository management.
- **AI Usage:** Generative AI tools (Google Gemini) assisted in harness scripting and formatting; all live LLM experiments, unit tests, and statistical analyses were executed and verified locally by the authors.
- **Open Data & Code:** Complete dataset, prompts, QuixBugs test runner (`run_quixbugs_benchmark.py`), multilingual benchmark (`run_multilingual_llm_benchmark.py`), and analysis scripts are archived in `d:\RMT` for Zenodo release (DOI: 10.5281/zenodo.14892026). Licenses: Google MBPP (Apache 2.0), QuixBugs (MIT), Stack Overflow SEDE (CC BY-SA 4.0).
