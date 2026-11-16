#!/usr/bin/env python3
"""
Real Independent QuixBugs Automated Test Suite & Live LLM Repair Benchmark
Course: Research Methods and Tools (RMT) — SE-2417, Astana IT University
Executes official QuixBugs test cases (`json_testcases/*.json`) against:
  1. All 31 JSON-testable QuixBugs Python programs (Buggy Baseline vs. Correct Reference)
  2. Extracted code from the 150-item SE dataset (`dataset_eval_150_rated.json`, max_tokens=1024)
  3. Live repair inference via `google/gemma-4-12b-qat` at http://localhost:1235/v1 (max_tokens=1500)
"""

import os
import sys
import json
import glob
import time
import re
import subprocess
import urllib.request
import urllib.error
import pandas as pd

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
QUIXBUGS_DIR = os.path.join(BASE_DIR, "QuixBugs")
PYTHON_PROGRAMS_DIR = os.path.join(QUIXBUGS_DIR, "python_programs")
JSON_TESTCASES_DIR = os.path.join(QUIXBUGS_DIR, "json_testcases")
DATASET_JSON = os.path.join(BASE_DIR, "dataset_eval_150_rated.json")
OUTPUT_REPORT = os.path.join(BASE_DIR, "quixbugs_execution_report.txt")
OUTPUT_CSV = os.path.join(BASE_DIR, "quixbugs_execution_results.csv")
LIVE_QUIXBUGS_JSON = os.path.join(BASE_DIR, "quixbugs_live_llm_repairs.json")

API_URL = "http://localhost:1235/v1/chat/completions"
MODEL_NAME = "google/gemma-4-12b-qat"

WORKER_NATIVE_TEMPLATE = """import sys
import os
import json
import types
import io
import contextlib
import importlib

def main():
    algo_name = sys.argv[1]
    func_name = sys.argv[2]
    mode = sys.argv[3]
    testcases_path = sys.argv[4]

    target_dir = r"{python_dir}"
    if mode == "correct":
        target_dir = os.path.join(os.path.dirname(target_dir), "correct_python_programs")
    
    sys.path.insert(0, target_dir)
    
    try:
        mod = importlib.import_module(algo_name)
        fn = getattr(mod, func_name)
    except Exception as e:
        print("---PAYLOAD_START---")
        print(json.dumps({{"error": f"Import/Attr error: {{str(e)}}"}}))
        print("---PAYLOAD_END---")
        sys.exit(0)

    results = []
    with open(testcases_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            tc = json.loads(line)
            if isinstance(tc, list):
                inputs = tc[0]
                expected = tc[1] if len(tc) > 1 else None
            elif isinstance(tc, dict):
                inputs = tc.get("args")
                expected = tc.get("expected")
            else:
                continue
            
            try:
                f_supp = io.StringIO()
                with contextlib.redirect_stdout(f_supp):
                    if isinstance(inputs, list):
                        actual = fn(*inputs)
                    else:
                        actual = fn(inputs)
                    if isinstance(actual, types.GeneratorType):
                        actual = list(actual)
                
                if actual == expected:
                    results.append({{"status": "PASS"}})
                else:
                    results.append({{"status": "FAIL", "actual": str(actual)[:60], "expected": str(expected)[:60]}})
            except Exception as e:
                results.append({{"status": "ERROR", "error": f"{{type(e).__name__}}: {{str(e)}}"}})

    print("---PAYLOAD_START---")
    print(json.dumps(results))
    print("---PAYLOAD_END---")

if __name__ == "__main__":
    main()
"""

WORKER_CUSTOM_TEMPLATE = """import sys
import os
import json
import types
import io
import contextlib

def main():
    code_file = sys.argv[1]
    func_name = sys.argv[2]
    testcases_path = sys.argv[3]

    with open(code_file, "r", encoding="utf-8") as f:
        code_str = f.read()

    sandbox = {{}}
    f_supp = io.StringIO()
    try:
        with contextlib.redirect_stdout(f_supp):
            exec(code_str, sandbox)
    except Exception as e:
        print("---PAYLOAD_START---")
        print(json.dumps({{"error": f"Compile/Exec Error: {{type(e).__name__}}: {{str(e)}}"}}))
        print("---PAYLOAD_END---")
        sys.exit(0)

    if func_name not in sandbox:
        # fallback: find any user-defined function in sandbox
        funcs = [v for k, v in sandbox.items() if isinstance(v, types.FunctionType)]
        if funcs:
            fn = funcs[0]
        else:
            print("---PAYLOAD_START---")
            print(json.dumps({{"error": f"Function {{func_name}} not found"}}))
            print("---PAYLOAD_END---")
            sys.exit(0)
    else:
        fn = sandbox[func_name]

    results = []
    with open(testcases_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            tc = json.loads(line)
            inputs = tc[0] if isinstance(tc, list) else tc.get("args")
            expected = tc[1] if isinstance(tc, list) and len(tc) > 1 else tc.get("expected")

            try:
                with contextlib.redirect_stdout(f_supp):
                    if isinstance(inputs, list):
                        actual = fn(*inputs)
                    else:
                        actual = fn(inputs)
                    if isinstance(actual, types.GeneratorType):
                        actual = list(actual)
                if actual == expected:
                    results.append({{"status": "PASS"}})
                else:
                    results.append({{"status": "FAIL", "actual": str(actual)[:60], "expected": str(expected)[:60]}})
            except Exception as e:
                results.append({{"status": "ERROR", "error": f"{{type(e).__name__}}: {{str(e)}}"}})

    print("---PAYLOAD_START---")
    print(json.dumps(results))
    print("---PAYLOAD_END---")

if __name__ == "__main__":
    main()
"""

def extract_payload(stdout_text):
    if "---PAYLOAD_START---" in stdout_text and "---PAYLOAD_END---" in stdout_text:
        part = stdout_text.split("---PAYLOAD_START---")[1].split("---PAYLOAD_END---")[0].strip()
        return json.loads(part)
    return {"error": f"Parse error: {stdout_text[:80]}"}

def run_quixbugs_native(algo, func_name, is_correct=False, timeout=2.5):
    testcases_path = os.path.join(JSON_TESTCASES_DIR, f"{algo}.json")
    if not os.path.exists(testcases_path):
        return {"total": 0, "passed": 0, "failed": 0, "timeouts": 0, "errors": 0, "pass_rate": 0.0, "status": "NO_TESTS"}

    with open(testcases_path, "r", encoding="utf-8") as f:
        total = sum(1 for line in f if line.strip())

    worker_script = os.path.join(QUIXBUGS_DIR, "_worker_native.py")
    with open(worker_script, "w", encoding="utf-8") as f:
        f.write(WORKER_NATIVE_TEMPLATE.format(python_dir=PYTHON_PROGRAMS_DIR))

    cmd = [sys.executable, worker_script, algo, func_name, "correct" if is_correct else "buggy", testcases_path]
    try:
        p = subprocess.run(cmd, cwd=QUIXBUGS_DIR, capture_output=True, text=True, timeout=timeout)
        if os.path.exists(worker_script):
            os.remove(worker_script)
        if p.returncode != 0:
            return {"total": total, "passed": 0, "failed": 0, "timeouts": 0, "errors": total, "pass_rate": 0.0, "status": f"CRASH"}
        out_json = extract_payload(p.stdout)
        if isinstance(out_json, dict) and "error" in out_json:
            return {"total": total, "passed": 0, "failed": 0, "timeouts": 0, "errors": total, "pass_rate": 0.0, "status": out_json["error"]}
        passed = sum(1 for r in out_json if r["status"] == "PASS")
        failed = sum(1 for r in out_json if r["status"] == "FAIL")
        errors = sum(1 for r in out_json if r["status"] == "ERROR")
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "timeouts": 0,
            "errors": errors,
            "pass_rate": (passed / total * 100.0) if total > 0 else 0.0,
            "status": "OK" if errors == 0 else f"{errors} runtime errors"
        }
    except subprocess.TimeoutExpired:
        if os.path.exists(worker_script):
            os.remove(worker_script)
        return {"total": total, "passed": 0, "failed": 0, "timeouts": total, "errors": 0, "pass_rate": 0.0, "status": "TIMEOUT (INFINITE LOOP)"}

def run_custom_snippet(code_str, algo, func_name, timeout=2.5):
    testcases_path = os.path.join(JSON_TESTCASES_DIR, f"{algo}.json")
    with open(testcases_path, "r", encoding="utf-8") as f:
        total = sum(1 for line in f if line.strip())

    temp_code = os.path.join(QUIXBUGS_DIR, "_temp_snippet.py")
    with open(temp_code, "w", encoding="utf-8") as f:
        f.write(code_str)

    worker_script = os.path.join(QUIXBUGS_DIR, "_worker_custom.py")
    with open(worker_script, "w", encoding="utf-8") as f:
        f.write(WORKER_CUSTOM_TEMPLATE.format())

    cmd = [sys.executable, worker_script, temp_code, func_name, testcases_path]
    try:
        p = subprocess.run(cmd, cwd=QUIXBUGS_DIR, capture_output=True, text=True, timeout=timeout)
        for fp in [temp_code, worker_script]:
            if os.path.exists(fp):
                os.remove(fp)
        if p.returncode != 0:
            return {"total": total, "passed": 0, "failed": 0, "timeouts": 0, "errors": total, "pass_rate": 0.0, "status": "EXEC_ERROR"}
        out_json = extract_payload(p.stdout)
        if isinstance(out_json, dict) and "error" in out_json:
            return {"total": total, "passed": 0, "failed": 0, "timeouts": 0, "errors": total, "pass_rate": 0.0, "status": out_json["error"][:45]}
        passed = sum(1 for r in out_json if r["status"] == "PASS")
        failed = sum(1 for r in out_json if r["status"] == "FAIL")
        errors = sum(1 for r in out_json if r["status"] == "ERROR")
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "timeouts": 0,
            "errors": errors,
            "pass_rate": (passed / total * 100.0) if total > 0 else 0.0,
            "status": "ALL PASSED" if passed == total else f"{failed} failed, {errors} errors"
        }
    except subprocess.TimeoutExpired:
        for fp in [temp_code, worker_script]:
            if os.path.exists(fp):
                os.remove(fp)
        return {"total": total, "passed": 0, "failed": 0, "timeouts": total, "errors": 0, "pass_rate": 0.0, "status": "TIMEOUT (INFINITE LOOP)"}

def extract_code_block(text, func_name):
    if not text:
        return None
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)(?:```|$)", text, re.DOTALL)
    for b in blocks:
        if f"def {func_name}" in b:
            return b.strip()
    for b in blocks:
        if "def " in b:
            return b.strip()
    return None

def query_live_gemma_repair(algo, buggy_code):
    sys_prompt = (
        "You are an expert Software Engineering instructor. Keep internal reasoning brief (<150 tokens). "
        "Explain the root cause of the bug concisely and provide the complete, corrected Python function inside a ```python code block."
    )
    user_prompt = (
        f"The following Python function `{algo}` from the QuixBugs benchmark contains a defect. "
        f"Explain the root cause and provide the corrected `{algo}` function:\n\n```python\n{buggy_code}\n```"
    )
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1500
    }
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
        msg = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return {
            "content": msg.get("content", ""),
            "reasoning": msg.get("reasoning_content", ""),
            "finish_reason": data["choices"][0].get("finish_reason", ""),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "reasoning_tokens": usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
            "elapsed_sec": round(elapsed, 2)
        }

def main():
    report_lines = []
    def log(msg=""):
        print(msg, flush=True)
        report_lines.append(msg)

    log("=" * 88)
    log("  REAL INDEPENDENT QUIXBUGS TEST SUITE & LIVE GEMMA-4-12B-QAT REPAIR BENCHMARK")
    log("=" * 88)

    # PART 1: All 31 JSON-tested QuixBugs algorithms
    json_files = sorted(glob.glob(os.path.join(JSON_TESTCASES_DIR, "*.json")))
    algorithms = [os.path.splitext(os.path.basename(f))[0] for f in json_files]

    log(f"\n[PART 1] FULL QUIXBUGS SUITE BASELINE VERIFICATION ({len(algorithms)} Algorithms)")
    log(f"{'Algorithm':<26} | {'Buggy Baseline':<18} | {'Correct Reference':<18} | {'Buggy Behavior'}")
    log("-" * 88)

    total_tests_all = 0
    total_buggy_pass = 0
    total_corr_pass = 0
    suite_rows = []

    for algo in algorithms:
        b_res = run_quixbugs_native(algo, algo, is_correct=False)
        c_res = run_quixbugs_native(algo, algo, is_correct=True)
        total_tests_all += b_res["total"]
        total_buggy_pass += b_res["passed"]
        total_corr_pass += c_res["passed"]

        b_str = f"{b_res['passed']}/{b_res['total']} ({b_res['pass_rate']:.1f}%)"
        c_str = f"{c_res['passed']}/{c_res['total']} ({c_res['pass_rate']:.1f}%)"
        b_behav = b_res["status"] if b_res["status"] != "OK" else f"{b_res['failed']} wrong outputs"
        log(f"{algo:<26} | {b_str:<18} | {c_str:<18} | {b_behav}")
        suite_rows.append({
            "Algorithm": algo,
            "Total_Tests": b_res["total"],
            "Buggy_Passed": b_res["passed"],
            "Buggy_Pass_Rate": round(b_res["pass_rate"], 1),
            "Correct_Passed": c_res["passed"],
            "Correct_Pass_Rate": round(c_res["pass_rate"], 1),
            "Buggy_Mode": b_behav
        })

    log("-" * 88)
    log(f"TOTAL ACROSS {len(algorithms)} ALGORITHMS ({total_tests_all} Unit Tests):")
    log(f"  * Unpatched Buggy QuixBugs Pass Rate:  {total_buggy_pass}/{total_tests_all} ({total_buggy_pass/total_tests_all*100:.2f}%)")
    log(f"  * Ground-Truth Reference Pass Rate:    {total_corr_pass}/{total_tests_all} ({total_corr_pass/total_tests_all*100:.2f}%)")

    # PART 2: Dataset 150 Rated QuixBugs Subset (Original 1024-token limit)
    log("\n" + "=" * 88)
    log("[PART 2] EVALUATION OF QUIXBUGS TASKS IN 150-ITEM DATASET (max_tokens = 1024)")
    log("=" * 88)
    log(f"{'Task ID':<10} | {'Algorithm':<22} | {'Code Block':<12} | {'Unit Tests Passed':<18} | {'Outcome'}")
    log("-" * 88)

    with open(DATASET_JSON, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_algos = ["find_first_in_sorted", "sieve", "bucketsort", "flatten", "gcd", "bitcount"]
    quix_items = [d for d in dataset if 'quixbugs' in d.get('source_name', '').lower() or 'quixbugs' in str(d.get('sub_type', '')).lower()]

    ds_passed_tasks = 0
    ds_total_tests = 0
    ds_passed_tests = 0

    for item in quix_items:
        qid = item["question_id"]
        sub = item.get("sub_type", "")
        algo = next((a for a in target_algos if a in sub.lower() or a in item["user_prompt"].lower()), None)
        if not algo:
            continue
        tc_path = os.path.join(JSON_TESTCASES_DIR, f"{algo}.json")
        with open(tc_path, "r", encoding="utf-8") as f:
            n_tc = sum(1 for line in f if line.strip())
        ds_total_tests += n_tc

        code_str = extract_code_block(item.get("gemma_explanation", ""), algo)
        if not code_str:
            log(f"{qid:<10} | {algo:<22} | {'No (Trunc.)':<12} | {f'0/{n_tc} (0.0%)':<18} | Truncated / No function def")
            continue

        res = run_custom_snippet(code_str, algo, algo)
        ds_passed_tests += res["passed"]
        if res["passed"] == res["total"] and res["total"] > 0:
            ds_passed_tasks += 1
        p_str = f"{res['passed']}/{res['total']} ({res['pass_rate']:.1f}%)"
        log(f"{qid:<10} | {algo:<22} | {'Yes':<12} | {p_str:<18} | {res['status']}")

    log("-" * 88)
    log(f"1024-Token Cap Dataset QuixBugs Pass@1: {ds_passed_tasks}/{len(quix_items)} tasks ({ds_passed_tasks/len(quix_items)*100:.1f}%), {ds_passed_tests}/{ds_total_tests} unit tests ({ds_passed_tests/ds_total_tests*100:.1f}%)")

    # PART 3: Live Gemma-4-12B-QAT Inference (max_tokens = 1500) on the 6 Canonical QuixBugs Tasks
    log("\n" + "=" * 88)
    log("[PART 3] LIVE GEMMA-4-12B-QAT REPAIR & TEST EXECUTION (http://localhost:1235/v1, max_tokens=1500)")
    log("=" * 88)
    log(f"{'Algorithm':<22} | {'Reason/Total Tok':<18} | {'Latency':<9} | {'Unit Tests Passed':<18} | {'Status'}")
    log("-" * 88)

    live_results = []
    live_passed_tasks = 0
    live_total_tests = 0
    live_passed_tests = 0

    for algo in target_algos:
        buggy_path = os.path.join(PYTHON_PROGRAMS_DIR, f"{algo}.py")
        with open(buggy_path, "r", encoding="utf-8") as f:
            lines = [line for line in f if not line.strip().startswith('"""') and not line.strip().startswith("#")]
            buggy_code = "".join(lines).strip()

        try:
            llm_out = query_live_gemma_repair(algo, buggy_code)
            code_str = extract_code_block(llm_out["content"], algo)
            if code_str:
                t_res = run_custom_snippet(code_str, algo, algo)
            else:
                tc_path = os.path.join(JSON_TESTCASES_DIR, f"{algo}.json")
                with open(tc_path, "r", encoding="utf-8") as f:
                    n_tc = sum(1 for line in f if line.strip())
                t_res = {"total": n_tc, "passed": 0, "pass_rate": 0.0, "status": "NO_CODE_EXTRACTED"}

            live_total_tests += t_res["total"]
            live_passed_tests += t_res["passed"]
            if t_res["passed"] == t_res["total"] and t_res["total"] > 0:
                live_passed_tasks += 1

            tok_str = f"{llm_out['reasoning_tokens']}/{llm_out['completion_tokens']}"
            lat_str = f"{llm_out['elapsed_sec']:.1f}s"
            p_str = f"{t_res['passed']}/{t_res['total']} ({t_res['pass_rate']:.1f}%)"
            log(f"{algo:<22} | {tok_str:<18} | {lat_str:<9} | {p_str:<18} | {t_res['status']}")

            live_results.append({
                "algorithm": algo,
                "buggy_code": buggy_code,
                "extracted_code": code_str,
                "llm_response": llm_out,
                "test_results": t_res
            })
        except Exception as e:
            log(f"{algo:<22} | {'ERROR':<18} | {'N/A':<9} | {'0/0':<18} | {str(e)[:40]}")

    log("-" * 88)
    if live_total_tests > 0:
        log(f"Live Gemma-4-12B-QAT (max_tokens=1500) Pass@1: {live_passed_tasks}/{len(target_algos)} algorithms ({live_passed_tasks/len(target_algos)*100:.1f}%), {live_passed_tests}/{live_total_tests} unit tests ({live_passed_tests/live_total_tests*100:.1f}%)")

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    pd.DataFrame(suite_rows).to_csv(OUTPUT_CSV, index=False)
    with open(LIVE_QUIXBUGS_JSON, "w", encoding="utf-8") as f:
        json.dump(live_results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved full QuixBugs report to {OUTPUT_REPORT}, CSV to {OUTPUT_CSV}, and live repairs to {LIVE_QUIXBUGS_JSON}.")

if __name__ == "__main__":
    main()
