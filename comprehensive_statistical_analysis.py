import json
import csv
import math
import numpy as np
import scipy.stats as stats
import pandas as pd

CSV_PATH = r"d:\RMT\dataset_eval_150_rated.csv"
JSON_PATH = r"d:\RMT\dataset_eval_150_rated.json"

def quadratic_weighted_kappa(y1, y2, min_val=1, max_val=5):
    # compute Cohen's quadratic weighted kappa
    categories = list(range(min_val, max_val + 1))
    num_cats = len(categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    
    O = np.zeros((num_cats, num_cats), dtype=float)
    for a, b in zip(y1, y2):
        if a in cat_to_idx and b in cat_to_idx:
            O[cat_to_idx[a], cat_to_idx[b]] += 1
            
    n = np.sum(O)
    if n == 0:
        return 0.0
    O /= n
    
    row_sums = np.sum(O, axis=1)
    col_sums = np.sum(O, axis=2-1)
    E = np.outer(row_sums, col_sums)
    
    W = np.zeros((num_cats, num_cats), dtype=float)
    for i in range(num_cats):
        for j in range(num_cats):
            W[i, j] = ((i - j) ** 2) / ((num_cats - 1) ** 2)
            
    po = np.sum(W * O)
    pe = np.sum(W * E)
    if pe == 0:
        return 1.0
    return 1.0 - (po / pe)

def linear_weighted_kappa(y1, y2, min_val=1, max_val=5):
    categories = list(range(min_val, max_val + 1))
    num_cats = len(categories)
    cat_to_idx = {c: i for i, c in enumerate(categories)}
    
    O = np.zeros((num_cats, num_cats), dtype=float)
    for a, b in zip(y1, y2):
        if a in cat_to_idx and b in cat_to_idx:
            O[cat_to_idx[a], cat_to_idx[b]] += 1
            
    n = np.sum(O)
    if n == 0:
        return 0.0
    O /= n
    
    row_sums = np.sum(O, axis=1)
    col_sums = np.sum(O, axis=1)
    E = np.outer(row_sums, col_sums)
    
    W = np.zeros((num_cats, num_cats), dtype=float)
    for i in range(num_cats):
        for j in range(num_cats):
            W[i, j] = abs(i - j) / (num_cats - 1)
            
    po = np.sum(W * O)
    pe = np.sum(W * E)
    if pe == 0:
        return 1.0
    return 1.0 - (po / pe)

def compute_icc(ratings_matrix):
    """
    ratings_matrix: n items x k raters
    Computes ICC(2,1) and ICC(2,k) - Two-way random effects, absolute agreement
    """
    n, k = ratings_matrix.shape
    row_means = np.mean(ratings_matrix, axis=1)
    col_means = np.mean(ratings_matrix, axis=0)
    grand_mean = np.mean(ratings_matrix)
    
    SS_total = np.sum((ratings_matrix - grand_mean) ** 2)
    SS_rows = k * np.sum((row_means - grand_mean) ** 2) # between targets
    SS_cols = n * np.sum((col_means - grand_mean) ** 2) # between raters
    SS_error = SS_total - SS_rows - SS_cols             # residual / interaction
    
    df_rows = n - 1
    df_cols = k - 1
    df_error = (n - 1) * (k - 1)
    
    MS_rows = SS_rows / df_rows
    MS_cols = SS_cols / df_cols
    MS_error = SS_error / df_error
    
    # ICC(2,1)
    icc_2_1 = (MS_rows - MS_error) / (MS_rows + (k - 1) * MS_error + (k / n) * (MS_cols - MS_error))
    
    # ICC(2,k)
    icc_2_k = (MS_rows - MS_error) / (MS_rows + (MS_cols - MS_error) / n)
    
    return icc_2_1, icc_2_k

def krippendorff_alpha_ordinal(ratings_matrix):
    """
    Krippendorff's alpha for ordinal data
    ratings_matrix: n items x k raters
    """
    n, k = ratings_matrix.shape
    # Pairwise coincidences
    # For ordinal metric, difference is (sum of frequencies between i and j + (f_i + f_j)/2)^2
    # Standard formula for complete ordinal data:
    diffs_observed = []
    for row in ratings_matrix:
        for i in range(k):
            for j in range(i + 1, k):
                diffs_observed.append(abs(row[i] - row[j]))
    
    all_vals = ratings_matrix.flatten()
    diffs_expected = []
    for i in range(len(all_vals)):
        for j in range(i + 1, len(all_vals)):
            diffs_expected.append(abs(all_vals[i] - all_vals[j]))
            
    Do = np.mean(np.array(diffs_observed) ** 2)
    De = np.mean(np.array(diffs_expected) ** 2)
    if De == 0:
        return 1.0
    return 1.0 - (Do / De)

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    print("Dataset rows:", len(df))

    raters = ["Daniil", "Diyar", "Yersultan", "Qwen"]
    human_raters = ["Daniil", "Diyar", "Yersultan"]
    criteria = ["Accuracy", "Completeness", "Clarity"]

    for r in raters:
        for c in criteria:
            df[f"{r}_{c}"] = df[f"{r}_{c}"].astype(int)

    # Compute individual overall scores
    for r in raters:
        df[f"{r}_Overall"] = (df[f"{r}_Accuracy"] + df[f"{r}_Completeness"] + df[f"{r}_Clarity"]) / 3.0

    # Compute Human consensus (mean and rounded)
    for c in criteria:
        df[f"Human_{c}"] = (df[f"Daniil_{c}"] + df[f"Diyar_{c}"] + df[f"Yersultan_{c}"]) / 3.0
        df[f"Human_{c}_rounded"] = np.round(df[f"Human_{c}"]).astype(int)
    df["Human_Overall"] = (df["Human_Accuracy"] + df["Human_Completeness"] + df["Human_Clarity"]) / 3.0
    df["Human_Overall_rounded"] = np.round(df["Human_Overall"]).astype(int)

    # Combined 4-evaluator means
    for c in criteria:
        df[f"Mean_{c}"] = (df[f"Daniil_{c}"] + df[f"Diyar_{c}"] + df[f"Yersultan_{c}"] + df[f"Qwen_{c}"]) / 4.0
    df["Mean_Overall"] = (df["Mean_Accuracy"] + df["Mean_Completeness"] + df["Mean_Clarity"]) / 3.0

    print("\n================== 1. DESCRIPTIVE SUMMARY ==================")
    for c in criteria + ["Overall"]:
        print(f"Criterion: {c}")
        col = f"Mean_{c}" if c != "Overall" else "Mean_Overall"
        m = df[col].mean()
        s = df[col].std()
        print(f"  All 4 Raters - Mean: {m:.3f}, Std: {s:.3f}, Median: {df[col].median():.2f}")
        h_col = f"Human_{c}"
        print(f"  Human Raters Only - Mean: {df[h_col].mean():.3f}, Std: {df[h_col].std():.3f}")
        q_col = f"Qwen_{c}"
        print(f"  Qwen Judge Only - Mean: {df[q_col].mean():.3f}, Std: {df[q_col].std():.3f}")

    print("\n================== 2. CATEGORY-LEVEL DESCRIPTIVES & KRUSKAL-WALLIS ==================")
    categories = ["Syntax Errors", "Runtime Debugging", "Basic Algorithms"]
    
    for c in criteria + ["Overall"]:
        col = f"Mean_{c}" if c != "Overall" else "Mean_Overall"
        print(f"\n--- {c} across Categories ---")
        cat_data = {}
        for cat in categories:
            vals = df[df["category"] == cat][col].values
            cat_data[cat] = vals
            # Bootstrap 95% CI
            boot_means = [np.mean(np.random.choice(vals, size=len(vals), replace=True)) for _ in range(1000)]
            ci_low, ci_high = np.percentile(boot_means, [2.5, 97.5])
            print(f"  {cat} (n={len(vals)}): Mean={np.mean(vals):.3f} (Std={np.std(vals):.3f}), Median={np.median(vals):.2f}, 95% CI=[{ci_low:.3f}, {ci_high:.3f}]")

        # Kruskal-Wallis H test
        h_stat, p_val = stats.kruskal(cat_data["Syntax Errors"], cat_data["Runtime Debugging"], cat_data["Basic Algorithms"])
        # Epsilon-squared effect size: H / ((N^2 - 1) / (N + 1))
        N = len(df)
        eta_squared = (h_stat - 3 + 1) / (N - 3)
        epsilon_squared = h_stat / ((N**2 - 1) / (N + 1))
        print(f"  Kruskal-Wallis H = {h_stat:.4f}, df = 2, p = {p_val:.4e}, eta^2 = {eta_squared:.4f}, eps^2 = {epsilon_squared:.4f}")

        # Post-hoc Mann-Whitney U pairwise with Holm correction
        pairs = [("Syntax Errors", "Runtime Debugging"), ("Basic Algorithms", "Runtime Debugging"), ("Syntax Errors", "Basic Algorithms")]
        p_pairs = []
        for c1, c2 in pairs:
            u_stat, u_p = stats.mannwhitneyu(cat_data[c1], cat_data[c2], alternative='two-sided')
            p_pairs.append((c1, c2, u_stat, u_p))
        
        # Holm correction
        p_pairs.sort(key=lambda x: x[3])
        m_tests = len(p_pairs)
        print("  Post-hoc Mann-Whitney U (Holm-corrected):")
        for i, (c1, c2, u_s, raw_p) in enumerate(p_pairs):
            holm_p = min(1.0, raw_p * (m_tests - i))
            # Rank biserial correlation as effect size r = 1 - (2U)/(n1*n2)
            n1, n2 = len(cat_data[c1]), len(cat_data[c2])
            r_effect = 1.0 - (2.0 * u_s) / (n1 * n2)
            print(f"    {c1} vs {c2}: U={u_s:.1f}, p={raw_p:.4e}, p_holm={holm_p:.4e}, r={abs(r_effect):.3f}")

    print("\n================== 3. INTER-RATER RELIABILITY (HUMAN RATERS) ==================")
    for c in criteria:
        mat_human = df[[f"{r}_{c}" for r in human_raters]].values
        icc_1, icc_k = compute_icc(mat_human)
        alpha_ord = krippendorff_alpha_ordinal(mat_human)
        
        # Pairwise kappas
        k_d_dy_quad = quadratic_weighted_kappa(df[f"Daniil_{c}"], df[f"Diyar_{c}"])
        k_d_ye_quad = quadratic_weighted_kappa(df[f"Daniil_{c}"], df[f"Yersultan_{c}"])
        k_dy_ye_quad = quadratic_weighted_kappa(df[f"Diyar_{c}"], df[f"Yersultan_{c}"])
        mean_kappa_quad = np.mean([k_d_dy_quad, k_d_ye_quad, k_dy_ye_quad])

        k_d_dy_lin = linear_weighted_kappa(df[f"Daniil_{c}"], df[f"Diyar_{c}"])
        k_d_ye_lin = linear_weighted_kappa(df[f"Daniil_{c}"], df[f"Yersultan_{c}"])
        k_dy_ye_lin = linear_weighted_kappa(df[f"Diyar_{c}"], df[f"Yersultan_{c}"])
        mean_kappa_lin = np.mean([k_d_dy_lin, k_d_ye_lin, k_dy_ye_lin])

        print(f"\nCriterion: {c}")
        print(f"  ICC(2,1) [single rater absolute]: {icc_1:.3f}")
        print(f"  ICC(2,k) [average 3 raters absolute]: {icc_k:.3f}")
        print(f"  Krippendorff's alpha (ordinal): {alpha_ord:.3f}")
        print(f"  Pairwise Quadratic Weighted Kappa: Daniil-Diyar={k_d_dy_quad:.3f}, Daniil-Yersultan={k_d_ye_quad:.3f}, Diyar-Yersultan={k_dy_ye_quad:.3f} | Mean={mean_kappa_quad:.3f}")
        print(f"  Pairwise Linear Weighted Kappa: Daniil-Diyar={k_d_lin:.3f}, Daniil-Yersultan={k_d_ye_lin:.3f}, Diyar-Yersultan={k_dy_ye_lin:.3f} | Mean={mean_kappa_lin:.3f}" if 'k_d_lin' in locals() else f"  Pairwise Linear Weighted Kappa Mean={mean_kappa_lin:.3f}")

    print("\n================== 4. HUMAN CONSENSUS VS. QWEN LLM JUDGE ==================")
    for c in criteria:
        h_vals = df[f"Human_{c}_rounded"]
        q_vals = df[f"Qwen_{c}"]
        
        # Pairwise matrix
        mat_hq = np.column_stack([h_vals, q_vals])
        icc_1, icc_k = compute_icc(mat_hq)
        alpha_ord = krippendorff_alpha_ordinal(mat_hq)
        kw_quad = quadratic_weighted_kappa(h_vals, q_vals)
        kw_lin = linear_weighted_kappa(h_vals, q_vals)
        mae = np.mean(np.abs(df[f"Human_{c}"] - q_vals))
        spearman_rho, spearman_p = stats.spearmanr(df[f"Human_{c}"], q_vals)
        pearson_r, pearson_p = stats.pearsonr(df[f"Human_{c}"], q_vals)

        exact_agr = np.mean(h_vals == q_vals) * 100.0
        within_1 = np.mean(np.abs(h_vals - q_vals) <= 1) * 100.0

        print(f"\nCriterion: {c}")
        print(f"  Exact Agreement: {exact_agr:.1f}%, Within +/-1: {within_1:.1f}%")
        print(f"  Weighted Kappa (quadratic): {kw_quad:.3f}, Weighted Kappa (linear): {kw_lin:.3f}")
        print(f"  ICC(2,1): {icc_1:.3f}, ICC(2,k): {icc_k:.3f}")
        print(f"  Krippendorff's alpha (ordinal): {alpha_ord:.3f}")
        print(f"  MAE: {mae:.3f}, Spearman rho: {spearman_rho:.3f} (p={spearman_p:.4e}), Pearson r: {pearson_r:.3f}")

    print("\n================== 5. SCORE DISTRIBUTIONS & CEILING EFFECT ==================")
    for c in criteria:
        print(f"\nScore distribution for {c} (all 4 raters combined, N = 600 ratings):")
        all_ratings = []
        for r in raters:
            all_ratings.extend(df[f"{r}_{c}"].tolist())
        counts = pd.Series(all_ratings).value_counts().sort_index()
        for score in range(1, 6):
            cnt = counts.get(score, 0)
            pct = cnt / len(all_ratings) * 100.0
            print(f"  Score {score}: {cnt:3d} ({pct:5.1f}%)")

    print("\n================== 6. LENGTH BIAS & EXPLANATION LENGTH ==================")
    df["word_count"] = df["gemma_explanation"].apply(lambda x: len(str(x).split()))
    print(f"Explanation Word Count: Mean = {df['word_count'].mean():.1f}, Std = {df['word_count'].std():.1f}, Min = {df['word_count'].min()}, Max = {df['word_count'].max()}")
    
    for c in criteria + ["Overall"]:
        q_col = f"Qwen_{c}"
        h_col = f"Human_{c}"
        r_qwen, p_qwen = stats.pearsonr(df["word_count"], df[q_col])
        r_human, p_human = stats.pearsonr(df["word_count"], df[h_col])
        print(f"  {c} - Length vs Qwen Score: r = {r_qwen:.3f} (p = {p_qwen:.4f}) | Length vs Human Score: r = {r_human:.3f} (p = {p_human:.4f})")

if __name__ == "__main__":
    main()
