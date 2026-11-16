#!/usr/bin/env python3
"""
Real Multilingual Comparative Benchmark Pipeline (Experiment E5)
Course: Research Methods and Tools (RMT) — SE-2417, Astana IT University
Queries live local `google/gemma-4-12b-qat` at http://localhost:1235/v1 across a paired
10-task Software Engineering (SE) benchmark (30 total evaluations across English, Russian, Kazakh).
Executes generated Python code against real unit tests, measures Language Consistency,
Terminology Preservation, Reasoning Token Overhead, and Rubric Scores, and computes
Friedman chi-square and Wilcoxon signed-rank tests.
"""

import os
import sys
import json
import time
import re
import ast
import types
import io
import contextlib
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
API_URL = "http://localhost:1235/v1/chat/completions"
MODEL_NAME = "google/gemma-4-12b-qat"

OUTPUT_JSON = os.path.join(BASE_DIR, "multilingual_real_responses.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "multilingual_real_summary.csv")
OUTPUT_REPORT = os.path.join(BASE_DIR, "multilingual_real_report.txt")

# 10 Paired Software Engineering Tasks (Syntax, Runtime Debugging, Basic Algorithms)
MULTILINGUAL_TASKS = [
    {
        "id": "SE_ML_01",
        "category": "Basic Algorithms",
        "func_name": "is_palindrome",
        "en": "Write a Python function `is_palindrome(s: str) -> bool` that checks if a string is a palindrome ignoring case and spaces, and briefly explain how it works.",
        "ru": "Напишите функцию Python `is_palindrome(s: str) -> bool`, которая проверяет, является ли строка палиндромом без учета регистра и пробелов, и кратко объясните принцип работы.",
        "kk": "Жолдың регистрі мен бос орындарды елемей, палиндром екенін тексеретін `is_palindrome(s: str) -> bool` Python функциясын жазыңыз және жұмыс істеу принципін қысқаша түсіндіріңіз.",
        "test_code": "assert is_palindrome('Race car') == True\nassert is_palindrome('hello') == False\nassert is_palindrome('Aba') == True",
        "ru_terms": ["строк", "регистр", "пробел", "функц", "срез"],
        "kk_terms": ["жол", "регистр", "бос орын", "функция", "палиндром"]
    },
    {
        "id": "SE_ML_02",
        "category": "Runtime Debugging",
        "func_name": "find_first_in_sorted",
        "en": "In binary search `def find_first_in_sorted(arr, x):`, setting `hi = len(arr)` causes an `IndexError` when `x` is larger than all elements. Explain why and provide the corrected `find_first_in_sorted(arr, x)` function returning the first index of `x` or `-1`.",
        "ru": "В бинарном поиске `def find_first_in_sorted(arr, x):` установка `hi = len(arr)` вызывает `IndexError`, когда `x` больше всех элементов. Объясните причину и приведите исправленную функцию `find_first_in_sorted(arr, x)`, возвращающую первый индекс `x` или `-1`.",
        "kk": "Екілік іздеуде `def find_first_in_sorted(arr, x):` ішінде `hi = len(arr)` деп орнату `x` барлық элементтерден үлкен болғанда `IndexError` тудырады. Себебін түсіндіріп, `x`-тің бірінші индексін немесе `-1` қайтаратын түзетілген `find_first_in_sorted(arr, x)` функциясын жазыңыз.",
        "test_code": "assert find_first_in_sorted([3, 4, 5, 5, 6], 5) == 2\nassert find_first_in_sorted([1, 2, 3], 9) == -1\nassert find_first_in_sorted([1, 2, 3], 0) == -1",
        "ru_terms": ["индекс", "спис", "массив", "границ", "поиск"],
        "kk_terms": ["индекс", "тізім", "іздеу", "шекара", "элемент"]
    },
    {
        "id": "SE_ML_03",
        "category": "Syntax Errors",
        "func_name": "check_grade",
        "en": "Why does `if score = 100:` raise a `SyntaxError` in Python? Explain the difference between `=` and `==`, and write a function `check_grade(score)` that returns `'Perfect'` if `score == 100` else `'Keep trying'`.",
        "ru": "Почему `if score = 100:` вызывает `SyntaxError` в Python? Объясните разницу между `=` и `==`, и напишите функцию `check_grade(score)`, которая возвращает `'Perfect'`, если `score == 100`, иначе `'Keep trying'`.",
        "kk": "Неліктен Python-да `if score = 100:` коды `SyntaxError` қатесін тудырады? `=` мен `==` айырмашылығын түсіндіріп, егер `score == 100` болса `'Perfect'`, әйтпесе `'Keep trying'` қайтаратын `check_grade(score)` функциясын жазыңыз.",
        "test_code": "assert check_grade(100) == 'Perfect'\nassert check_grade(85) == 'Keep trying'",
        "ru_terms": ["присваиван", "сравнен", "оператор", "услов", "ошибк"],
        "kk_terms": ["меншіктеу", "салыстыру", "оператор", "шарт", "қате"]
    },
    {
        "id": "SE_ML_04",
        "category": "Runtime Debugging",
        "func_name": "append_item",
        "en": "Explain why `def append_item(item, target=[]): target.append(item); return target` causes a mutable default argument bug in Python, and provide the corrected `append_item(item, target=None)` function.",
        "ru": "Объясните, почему `def append_item(item, target=[]): target.append(item); return target` вызывает ошибку изменяемого аргумента по умолчанию в Python, и напишите исправленную функцию `append_item(item, target=None)`.",
        "kk": "Python-да `def append_item(item, target=[]): target.append(item); return target` неліктен өзгермелі әдепкі аргумент қатесін тудыратынын түсіндіріңіз және түзетілген `append_item(item, target=None)` функциясын жазыңыз.",
        "test_code": "assert append_item(1) == [1]\nassert append_item(2) == [2]\nassert append_item(3, [10]) == [10, 3]",
        "ru_terms": ["аргумент", "умолчан", "спис", "изменяем", "вызов"],
        "kk_terms": ["аргумент", "тізім", "функция", "шақыру", "мән"]
    },
    {
        "id": "SE_ML_05",
        "category": "Runtime Debugging",
        "func_name": "gcd",
        "en": "The buggy QuixBugs function `def gcd(a, b): return a if b == 0 else gcd(a % b, b)` fails with infinite recursion. Explain the bug in argument order and provide the corrected `gcd(a, b)` function.",
        "ru": "Функция из QuixBugs `def gcd(a, b): return a if b == 0 else gcd(a % b, b)` уходит в бесконечную рекурсию. Объясните ошибку в порядке аргументов и приведите исправленную функцию `gcd(a, b)`.",
        "kk": "QuixBugs ішіндегі `def gcd(a, b): return a if b == 0 else gcd(a % b, b)` функциясы шексіз рекурсияға түседі. Аргументтер ретіндегі қатені түсіндіріп, түзетілген `gcd(a, b)` функциясын жазыңыз.",
        "test_code": "assert gcd(12, 8) == 4\nassert gcd(17, 0) == 17\nassert gcd(37, 600) == 1",
        "ru_terms": ["рекурс", "делител", "остаток", "аргумент", "базов"],
        "kk_terms": ["рекурсия", "бөлгіш", "қалдық", "аргумент", "функция"]
    },
    {
        "id": "SE_ML_06",
        "category": "Runtime Debugging",
        "func_name": "bitcount",
        "en": "In QuixBugs `def bitcount(n):`, writing `n ^= n - 1` instead of `n &= n - 1` causes an infinite loop when counting set bits. Explain why and write the corrected `bitcount(n)` function.",
        "ru": "В функции QuixBugs `def bitcount(n):` запись `n ^= n - 1` вместо `n &= n - 1` вызывает бесконечный цикл при подсчете единичных битов. Объясните причину и напишите исправленную функцию `bitcount(n)`.",
        "kk": "QuixBugs-тағы `def bitcount(n):` функциясында бірлік биттерді санау кезінде `n &= n - 1` орнына `n ^= n - 1` жазу шексіз цикл тудырады. Себебін түсіндіріп, түзетілген `bitcount(n)` функциясын жазыңыз.",
        "test_code": "assert bitcount(127) == 7\nassert bitcount(128) == 1\nassert bitcount(0) == 0",
        "ru_terms": ["бит", "операц", "цикл", "побитов", "числ"],
        "kk_terms": ["бит", "операция", "цикл", "сан", "функция"]
    },
    {
        "id": "SE_ML_07",
        "category": "Basic Algorithms",
        "func_name": "common_elements",
        "en": "Write a Python function `common_elements(list1, list2)` that returns a sorted list of unique elements present in both input lists, and explain your approach.",
        "ru": "Напишите функцию Python `common_elements(list1, list2)`, которая возвращает отсортированный список уникальных элементов, присутствующих в обоих списках, и объясните решение.",
        "kk": "Екі тізімде де кездесетін бірегей элементтердің сұрыпталған тізімін қайтаратын `common_elements(list1, list2)` Python функциясын жазыңыз және шешіміңізді түсіндіріңіз.",
        "test_code": "assert common_elements([1, 2, 2, 3], [2, 3, 4]) == [2, 3]\nassert common_elements([1, 5], [2, 3]) == []",
        "ru_terms": ["множеств", "спис", "пересечен", "сортиров", "уникальн"],
        "kk_terms": ["тізім", "жиын", "сұрыптау", "ортақ", "элемент"]
    },
    {
        "id": "SE_ML_08",
        "category": "Syntax Errors",
        "func_name": "sum_even",
        "en": "Why does forgetting a colon after `for x in nums` or `if x % 2 == 0` cause a `SyntaxError`? Explain briefly and write a working function `sum_even(nums)` returning the sum of even numbers in `nums`.",
        "ru": "Почему пропуск двоеточия после `for x in nums` или `if x % 2 == 0` вызывает `SyntaxError`? Кратко объясните и напишите функцию `sum_even(nums)`, возвращающую сумму четных чисел.",
        "kk": "Неліктен `for x in nums` немесе `if x % 2 == 0` кейін қос нүктені ұмыту `SyntaxError` тудырады? Қысқаша түсіндіріп, жұп сандардың қосындысын қайтаратын `sum_even(nums)` функциясын жазыңыз.",
        "test_code": "assert sum_even([1, 2, 3, 4, 6]) == 12\nassert sum_even([1, 3, 5]) == 0",
        "ru_terms": ["двоеточ", "блок", "цикл", "отступ", "синтаксис"],
        "kk_terms": ["қос нүкте", "блок", "цикл", "шегініс", "синтаксис"]
    },
    {
        "id": "SE_ML_09",
        "category": "Runtime Debugging",
        "func_name": "safe_divide",
        "en": "Explain why dividing by zero raises `ZeroDivisionError` in Python and write a function `safe_divide(a, b)` that returns `a / b` or `0.0` if `b == 0`.",
        "ru": "Объясните, почему деление на ноль вызывает `ZeroDivisionError` в Python, и напишите функцию `safe_divide(a, b)`, которая возвращает `a / b` или `0.0`, если `b == 0`.",
        "kk": "Python-да нөлге бөлу неліктен `ZeroDivisionError` тудыратынын түсіндіріңіз және егер `b == 0` болса `0.0`, әйтпесе `a / b` қайтаратын `safe_divide(a, b)` функциясын жазыңыз.",
        "test_code": "assert safe_divide(10, 2) == 5.0\nassert safe_divide(10, 0) == 0.0",
        "ru_terms": ["делен", "ноль", "исключен", "проверк", "ошибк"],
        "kk_terms": ["бөлу", "нөл", "қате", "тексеру", "функция"]
    },
    {
        "id": "SE_ML_10",
        "category": "Basic Algorithms",
        "func_name": "count_vowels",
        "en": "Write a Python function `count_vowels(s: str) -> int` that counts the number of English vowels (`a, e, i, o, u`, case-insensitive) in a string and explain how it works.",
        "ru": "Напишите функцию Python `count_vowels(s: str) -> int`, которая подсчитывает количество английских гласных (`a, e, i, o, u`, без учета регистра) в строке, и объясните её работу.",
        "kk": "Жолдағы ағылшын дауысты дыбыстарының (`a, e, i, o, u`, регистрді ескермей) санын есептейтін `count_vowels(s: str) -> int` Python функциясын жазыңыз және оның жұмысын түсіндіріңіз.",
        "test_code": "assert count_vowels('Astana IT University') == 8\nassert count_vowels('RMT') == 0",
        "ru_terms": ["гласн", "строк", "счетчик", "цикл", "регистр"],
        "kk_terms": ["дауысты", "жол", "санау", "цикл", "регистр"]
    }
]

SYSTEM_PROMPTS = {
    "en": (
        "You are a concise Software Engineering instructor at Astana IT University. "
        "Keep internal reasoning brief (<120 tokens). Immediately provide a clear pedagogical explanation "
        "in English (root cause, step-by-step logic, prevention tip) and a complete, runnable Python function in a ```python block."
    ),
    "ru": (
        "Вы преподаватель программной инженерии (Software Engineering). "
        "Держите внутренние рассуждения краткими (<120 токенов). Сразу дайте четкое педагогическое объяснение "
        "строго на русском языке и приведите полный рабочий код функции Python в блоке ```python."
    ),
    "kk": (
        "Сіз бағдарламалық инженерия (Software Engineering) оқытушысысыз. "
        "Ішкі ойлауды қысқа ұстаңыз (<120 токен). Түсініктемені тек таза қазақ тілінде беріңіз "
        "және толық жұмыс істейтін Python функциясын ```python блогында жазыңыз."
    )
}

def query_llm_single(task, lang):
    prompt = task[lang]
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS[lang]},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1350
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
        msg = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return {
            "content": msg.get("content", ""),
            "reasoning_content": msg.get("reasoning_content", ""),
            "finish_reason": data["choices"][0].get("finish_reason", ""),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "reasoning_tokens": usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
            "elapsed_sec": round(elapsed, 2)
        }

def evaluate_code_and_tests(response_text, func_name, test_code):
    if not response_text:
        return {"has_code": False, "syntax_ok": False, "tests_passed": False, "error": "Empty response"}
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)(?:```|$)", response_text, re.DOTALL)
    if not blocks:
        return {"has_code": False, "syntax_ok": False, "tests_passed": False, "error": "No code fence"}

    # Pick block with def func_name or longest block
    chosen = None
    for b in blocks:
        if f"def {func_name}" in b:
            chosen = b.strip()
            break
    if not chosen:
        chosen = max(blocks, key=len).strip()

    try:
        ast.parse(chosen)
        syntax_ok = True
    except SyntaxError as e:
        return {"has_code": True, "syntax_ok": False, "tests_passed": False, "error": f"SyntaxError: {e}"}

    sandbox = {}
    f_supp = io.StringIO()
    try:
        with contextlib.redirect_stdout(f_supp):
            exec(chosen, sandbox)
            exec(test_code, sandbox)
        return {"has_code": True, "syntax_ok": True, "tests_passed": True, "error": ""}
    except Exception as e:
        return {"has_code": True, "syntax_ok": True, "tests_passed": False, "error": f"{type(e).__name__}: {e}"}

def analyze_linguistic_metrics(response_text, lang, task):
    if not response_text or not response_text.strip():
        return {"lang_consistency": 0.0, "term_preservation": 0.0, "latin_bleed_count": 0, "prose_words": 0}

    # Strip fenced code blocks and inline code backticks to inspect pure instructional prose
    prose = re.sub(r"```.*?```", " ", response_text, flags=re.DOTALL)
    prose = re.sub(r"`[^`]+`", " ", prose)
    prose_words = len(prose.split())

    if lang == "en":
        cyr_chars = len(re.findall(r"[\u0400-\u04FF]", prose))
        lang_cons = 1.0 if cyr_chars == 0 else max(0.0, 1.0 - cyr_chars / max(len(prose), 1))
        return {"lang_consistency": lang_cons, "term_preservation": 1.0, "latin_bleed_count": 0, "prose_words": prose_words}

    # For RU and KK: check Cyrillic vs unexpected Latin prose words (excluding standard terms Python, O(n), PEP-8, None, True, False, int, str, bool)
    allowed_latin = {"python", "none", "true", "false", "int", "str", "bool", "list", "dict", "set", "pep", "indexerror", "syntaxerror", "zerodivisionerror", "valueerror", "typeerror", "quixbugs", "o", "n", "log", "mid", "low", "high", "hi", "lo", "arr", "def", "if", "else", "for", "while", "return"}
    latin_tokens = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", prose) if w.lower() not in allowed_latin]
    # Also check mixed-script corrupted tokens (e.g. Cyrillic + Latin inside same word like 'тексерікten')
    mixed_script_tokens = re.findall(r"(?:[\u0400-\u04FF]+[A-Za-z]+|[A-Za-z]+[\u0400-\u04FF]+)", prose)

    bleed_count = len(latin_tokens) + 2 * len(mixed_script_tokens)
    cyr_all = len(re.findall(r"[\u0400-\u04FF]", prose))
    alpha_all = len(re.findall(r"[A-Za-z\u0400-\u04FF]", prose))
    cyr_ratio = cyr_all / max(alpha_all, 1)

    if lang == "ru":
        # Check RU terminology
        terms = task.get("ru_terms", [])
        matched = sum(1 for t in terms if t in prose.lower())
        term_pres = min(1.0, (matched / max(len(terms), 1)) + 0.15)
        lang_cons = 1.0 if (cyr_ratio >= 0.85 and bleed_count <= 2) else max(0.5, cyr_ratio - 0.05 * bleed_count)
        return {"lang_consistency": round(lang_cons, 3), "term_preservation": round(term_pres, 3), "latin_bleed_count": bleed_count, "prose_words": prose_words}

    if lang == "kk":
        # Check Kazakh specific letters
        kk_chars = len(re.findall(r"[ӘәҒғҚқҢңӨөҰұҮүІіҺһ]", prose))
        terms = task.get("kk_terms", [])
        matched = sum(1 for t in terms if t in prose.lower())
        # Check Russian loanword intrusion in Kazakh (e.g., 'массив', 'строка', 'поэтому', 'ошибка', 'деление')
        ru_intrusions = len(re.findall(r"\b(поэтому|ошибка|строка|деление|также|список|условие)\b", prose.lower()))
        term_pres = max(0.2, min(1.0, (matched / max(len(terms), 1)) - 0.1 * ru_intrusions - 0.05 * len(mixed_script_tokens)))
        has_kk = kk_chars >= 5
        lang_cons = (0.85 if has_kk else 0.4) - 0.06 * bleed_count - 0.08 * ru_intrusions
        lang_cons = max(0.2, min(1.0, lang_cons))
        return {"lang_consistency": round(lang_cons, 3), "term_preservation": round(term_pres, 3), "latin_bleed_count": bleed_count + ru_intrusions, "prose_words": prose_words}

def compute_rubric_scores(code_eval, lang_eval, llm_resp, lang):
    # Deterministic, reproducible rubric evaluation anchored on SE criteria (1-5 scale)
    # 1. Technical Accuracy (1-5)
    if code_eval["tests_passed"]:
        acc = 5.0 if lang_eval["term_preservation"] >= 0.8 else 4.0
    elif code_eval["syntax_ok"]:
        acc = 3.5
    elif code_eval["has_code"]:
        acc = 2.5
    else:
        acc = 2.0 if len(llm_resp["content"]) > 100 else 1.0

    # 2. Explanatory Completeness (1-5)
    words = lang_eval["prose_words"]
    truncated = (llm_resp["finish_reason"] == "length")
    if code_eval["tests_passed"] and words >= 60 and not truncated:
        comp = 5.0 if words >= 90 else 4.5
    elif code_eval["has_code"] and words >= 40:
        comp = 4.0 if not truncated else 3.0
    elif words >= 30:
        comp = 2.5
    else:
        comp = 1.5

    # 3. Pedagogical Clarity (1-5)
    # Clarity depends on structure, language consistency, and terminology preservation
    base_clar = 2.0 + 1.5 * lang_eval["lang_consistency"] + 1.5 * lang_eval["term_preservation"]
    if truncated:
        base_clar -= 0.5
    if lang_eval["latin_bleed_count"] > 2:
        base_clar -= 0.4
    clar = max(1.0, min(5.0, round(base_clar * 2) / 2))

    return {
        "accuracy": round(acc, 2),
        "completeness": round(comp, 2),
        "clarity": round(clar, 2),
        "overall": round((acc + comp + clar) / 3.0, 2)
    }

def main():
    print("=" * 88)
    print("  REAL MULTILINGUAL SE BENCHMARK (E5) — LIVE GEMMA-4-12B-QAT EXECUTION")
    print("=" * 88)

    all_records = []
    for task in MULTILINGUAL_TASKS:
        tid = task["id"]
        print(f"\n>>> Task {tid} ({task['category']}): {task['func_name']}", flush=True)
        # Query EN, RU, KK in parallel across LM Studio's 4 slots
        futures = {}
        with ThreadPoolExecutor(max_workers=3) as ex:
            for lang in ["en", "ru", "kk"]:
                futures[ex.submit(query_llm_single, task, lang)] = lang

            for fut in as_completed(futures):
                lang = futures[fut]
                try:
                    llm_resp = fut.result()
                except Exception as e:
                    print(f"  [{lang.upper()}] ERROR: {e}", flush=True)
                    llm_resp = {"content": "", "reasoning_content": "", "finish_reason": "error", "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "elapsed_sec": 0.0}

                code_eval = evaluate_code_and_tests(llm_resp["content"], task["func_name"], task["test_code"])
                lang_eval = analyze_linguistic_metrics(llm_resp["content"], lang, task)
                rubric = compute_rubric_scores(code_eval, lang_eval, llm_resp, lang)

                rec = {
                    "task_id": tid,
                    "category": task["category"],
                    "func_name": task["func_name"],
                    "language": lang,
                    "prompt_tokens": llm_resp["prompt_tokens"],
                    "reasoning_tokens": llm_resp["reasoning_tokens"],
                    "completion_tokens": llm_resp["completion_tokens"],
                    "finish_reason": llm_resp["finish_reason"],
                    "elapsed_sec": llm_resp["elapsed_sec"],
                    "has_code": code_eval["has_code"],
                    "syntax_ok": code_eval["syntax_ok"],
                    "tests_passed": code_eval["tests_passed"],
                    "test_error": code_eval["error"],
                    "lang_consistency": lang_eval["lang_consistency"],
                    "term_preservation": lang_eval["term_preservation"],
                    "latin_bleed_count": lang_eval["latin_bleed_count"],
                    "prose_words": lang_eval["prose_words"],
                    "accuracy": rubric["accuracy"],
                    "completeness": rubric["completeness"],
                    "clarity": rubric["clarity"],
                    "overall": rubric["overall"],
                    "content": llm_resp["content"],
                    "reasoning_content": llm_resp["reasoning_content"]
                }
                all_records.append(rec)
                print(
                    f"  [{lang.upper()}] Pass={code_eval['tests_passed']} | "
                    f"ReasonTok={llm_resp['reasoning_tokens']}/{llm_resp['completion_tokens']} | "
                    f"Scores(A/C/Cl/O)={rubric['accuracy']}/{rubric['completeness']}/{rubric['clarity']}/{rubric['overall']} | "
                    f"LangCons={lang_eval['lang_consistency']*100:.0f}% | TermPres={lang_eval['term_preservation']*100:.0f}%",
                    flush=True
                )

    # Sort records deterministically
    all_records.sort(key=lambda r: (r["task_id"], ["en", "ru", "kk"].index(r["language"])))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    df = pd.DataFrame(all_records)
    df_csv = df.drop(columns=["content", "reasoning_content"])
    df_csv.to_csv(OUTPUT_CSV, index=False)

    # Compute Summary Table & Statistical Tests
    report_lines = []
    def log(msg=""):
        print(msg, flush=True)
        report_lines.append(msg)

    log("\n" + "=" * 95)
    log("  EMPIRICAL MULTILINGUAL SE BENCHMARK SUMMARY (N = 10 Paired Tasks x 3 Languages = 30 Runs)")
    log("=" * 95)
    log(f"{'Language':<12} | {'Acc.':<6} | {'Comp.':<6} | {'Clar.':<6} | {'Overall':<7} | {'Lang Cons.':<10} | {'Term Pres.':<10} | {'Pass@1':<8} | {'Reason Tok'}")
    log("-" * 95)

    for lang, label in [("en", "English (EN)"), ("ru", "Russian (RU)"), ("kk", "Kazakh (KK)")]:
        sub = df[df["language"] == lang]
        m_acc = sub["accuracy"].mean()
        m_comp = sub["completeness"].mean()
        m_clar = sub["clarity"].mean()
        m_ov = sub["overall"].mean()
        m_lc = sub["lang_consistency"].mean() * 100.0
        m_tp = sub["term_preservation"].mean() * 100.0
        m_pass = sub["tests_passed"].mean() * 100.0
        m_rtok = sub["reasoning_tokens"].mean()
        log(f"{label:<12} | {m_acc:<6.2f} | {m_comp:<6.2f} | {m_clar:<6.2f} | {m_ov:<7.2f} | {m_lc:<9.1f}% | {m_tp:<9.1f}% | {m_pass:<7.1f}% | {m_rtok:.1f}")

    # Friedman test on overall scores
    en_ov = df[df["language"] == "en"].sort_values("task_id")["overall"].values
    ru_ov = df[df["language"] == "ru"].sort_values("task_id")["overall"].values
    kk_ov = df[df["language"] == "kk"].sort_values("task_id")["overall"].values

    try:
        f_stat, f_p = stats.friedmanchisquare(en_ov, ru_ov, kk_ov)
        log("-" * 95)
        log(f"Friedman Test (Overall Score): chi^2 = {f_stat:.4f}, df = 2, p = {f_p:.4e}")
    except Exception as e:
        log(f"Friedman Test note: {e}")

    for name, a, b in [("EN vs RU", en_ov, ru_ov), ("EN vs KK", en_ov, kk_ov), ("RU vs KK", ru_ov, kk_ov)]:
        try:
            if np.all(a == b):
                log(f"  Wilcoxon {name}: identical distributions (p = 1.0)")
            else:
                w_stat, w_p = stats.wilcoxon(a, b)
                log(f"  Wilcoxon {name}: W = {w_stat:.2f}, p = {w_p:.4f}")
        except Exception as e:
            log(f"  Wilcoxon {name}: {e}")

    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nSaved full real multilingual dataset to {OUTPUT_JSON}, CSV to {OUTPUT_CSV}, and report to {OUTPUT_REPORT}.")

if __name__ == "__main__":
    main()
