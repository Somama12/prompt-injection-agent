"""Turn results/raw_results.csv into a heatmap PNG and markdown summary tables.

Run after evaluation.harness. Produces:
  results/heatmap.png            attack-category x defense, attack success rate
  results/summary.md             per-defense + per-category tables, judge agreement
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark.attacks import CATEGORIES
from defenses.registry import DEFENSE_ORDER

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
CAT_ORDER = ["direct_override", "roleplay_jailbreak", "data_exfiltration", "fake_system"]


def _load():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "raw_results.csv"))
    df["programmatic_success"] = df["programmatic_success"].astype(bool)
    return df


def _defense_labels(df):
    return {r["defense"]: r["defense_label"] for _, r in df.iterrows()}


def make_heatmap(df):
    labels = _defense_labels(df)
    defenses = [d for d in DEFENSE_ORDER if d in df["defense"].unique()]
    cats = [c for c in CAT_ORDER if c in df["category"].unique()]

    # rows = category, cols = defense, value = attack success rate (%)
    mat = np.zeros((len(cats), len(defenses)))
    for i, cat in enumerate(cats):
        for j, dfn in enumerate(defenses):
            sub = df[(df["category"] == cat) & (df["defense"] == dfn)]
            mat[i, j] = 100.0 * sub["programmatic_success"].mean() if len(sub) else np.nan

    fig, ax = plt.subplots(figsize=(1.6 * len(defenses) + 2, 1.1 * len(cats) + 2))
    im = ax.imshow(mat, cmap="RdYlGn_r", vmin=0, vmax=100, aspect="auto")

    ax.set_xticks(range(len(defenses)))
    ax.set_xticklabels([labels.get(d, d) for d in defenses], rotation=30, ha="right")
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([CATEGORIES.get(c, c) for c in cats])

    for i in range(len(cats)):
        for j in range(len(defenses)):
            val = mat[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center",
                        color="white" if (val > 60 or val < 15) else "black",
                        fontsize=11, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Attack success rate (%)")
    ax.set_title("Prompt-injection attack success rate\nby attack category x defense",
                 fontweight="bold")
    fig.tight_layout()
    out = os.path.join(RESULTS_DIR, "heatmap.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)
    return mat, cats, defenses, labels


def make_summary_md(df, mat, cats, defenses, labels):
    task = {}
    tpath = os.path.join(RESULTS_DIR, "task_success.json")
    if os.path.exists(tpath):
        task = json.load(open(tpath))
    summ = {}
    spath = os.path.join(RESULTS_DIR, "run_summary.json")
    if os.path.exists(spath):
        summ = json.load(open(spath))

    lines = ["# Results summary\n"]
    if summ:
        api = summ.get("api_stats", {})
        lines.append(
            f"Run: {summ.get('n_attacks')} attacks x {summ.get('n_defenses')} defenses = "
            f"**{summ.get('n_cells')} attack-defense cells**, "
            f"{api.get('calls','?')} real Gemini calls, "
            f"judge {'on' if summ.get('judge_used') else 'off'}, "
            f"wall-clock {summ.get('wall_clock_s','?')}s.\n"
        )

    # ---- per-defense table ----
    lines.append("## Attack success rate per defense\n")
    lines.append("| Defense | Attack success rate | Attacks blocked | Legit. task success | Mean latency/run (s) | Extra LLM calls/action |")
    lines.append("|---|---|---|---|---|---|")
    for dfn in defenses:
        sub = df[df["defense"] == dfn]
        asr = 100.0 * sub["programmatic_success"].mean()
        n_succ = int(sub["programmatic_success"].sum())
        n_tot = len(sub)
        blocked = int((sub["blocked_count"] > 0).sum())
        lat = sub["latency_s"].mean()
        t = task.get(dfn, {})
        ts = "yes" if t.get("task_success") else ("no" if t else "-")
        extra = next((d["extra_llm_calls_per_action"] for d in summ.get("defenses", [])
                      if d["name"] == dfn), "-")
        lines.append(f"| {labels.get(dfn,dfn)} | **{asr:.0f}%** ({n_succ}/{n_tot}) | "
                     f"{blocked}/{n_tot} | {ts} | {lat:.1f} | {extra} |")
    lines.append("")

    # ---- category x defense matrix ----
    lines.append("## Attack success rate: category x defense (%)\n")
    header = "| Attack category | " + " | ".join(labels.get(d, d) for d in defenses) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(defenses) + 1))
    for i, cat in enumerate(cats):
        row = [CATEGORIES.get(cat, cat)] + [f"{mat[i,j]:.0f}%" for j in range(len(defenses))]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # ---- judge agreement ----
    if "judge_success" in df.columns:
        judged = df[df["judge_success"].notna() & (df["judge_success"].astype(str) != "")]
        if len(judged):
            judged = judged.copy()
            judged["j"] = judged["judge_success"].astype(str).str.lower().isin(["true", "1"])
            agree = (judged["j"] == judged["programmatic_success"]).mean() * 100
            lines.append("## LLM-judge validation\n")
            lines.append(f"Programmatic scorer vs. Gemini-as-judge agreed on "
                         f"**{agree:.0f}%** of {len(judged)} judged cells.\n")

    out = os.path.join(RESULTS_DIR, "summary.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print("wrote", out)


def main():
    df = _load()
    mat, cats, defenses, labels = make_heatmap(df)
    make_summary_md(df, mat, cats, defenses, labels)


if __name__ == "__main__":
    main()
