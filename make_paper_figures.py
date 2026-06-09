from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)


def attack_accuracy() -> None:
    summary = pd.read_csv(ROOT / "final_results" / "end_to_end_summary.csv")
    frame = summary[
        (summary["descriptor"] == "narcis_neural")
        & (summary["attack"] != "clean")
    ].copy()
    frame["holdout"] = frame["attack"].str.contains("holdout")
    frame = frame.sort_values("symbol_accuracy_mean")
    labels = (
        frame["attack"]
        .str.replace("_holdout", " (H)", regex=False)
        .str.replace("_", " ", regex=False)
    )
    colors = ["#b54a4a" if value else "#315f8c" for value in frame["holdout"]]

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.barh(labels, frame["symbol_accuracy_mean"], color=colors)
    ax.axvline(1.0, color="black", linewidth=0.7)
    ax.set_xlim(0.84, 1.005)
    ax.set_xlabel("Mean symbol accuracy")
    ax.set_ylabel("Channel condition")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "attack_symbol_accuracy.pdf", bbox_inches="tight")
    fig.savefig(OUT / "attack_symbol_accuracy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def capacity_stability() -> None:
    report = json.loads(
        (ROOT / "large_scale_results_rs128" / "large_scale_report.json").read_text()
    )
    trials = pd.DataFrame(report["trials"]).sort_values("bits_per_cover")

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    colors = [
        "#2f7d4a" if value else "#9b9b9b"
        for value in trials["tested_messages_feasible"]
    ]
    ax.bar(
        trials["bits_per_cover"].astype(str),
        100 * trials["stable_fraction"],
        color=colors,
    )
    ax.set_xlabel("Nominal bits per transmitted cover")
    ax.set_ylabel("Attack-qualified covers (%)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "capacity_stability.pdf", bbox_inches="tight")
    fig.savefig(OUT / "capacity_stability.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def stability_ablation() -> None:
    raw = pd.read_csv(ROOT / "final_results" / "ablation_raw.csv")
    grouped = (
        raw.groupby("ablation", as_index=False)
        .agg(
            message_success=("message_success", "mean"),
            symbol_accuracy=("symbol_accuracy", "mean"),
        )
        .set_index("ablation")
        .loc[["full", "no_stability_filter"]]
    )
    grouped.index = ["NARCIS", "Without cover qualification"]

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    x = range(len(grouped))
    width = 0.34
    ax.bar(
        [value - width / 2 for value in x],
        grouped["message_success"],
        width,
        label="Complete-message success",
        color="#315f8c",
    )
    ax.bar(
        [value + width / 2 for value in x],
        grouped["symbol_accuracy"],
        width,
        label="Symbol accuracy",
        color="#c58b2a",
    )
    ax.set_xticks(list(x), grouped.index)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean rate")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "stability_ablation.pdf", bbox_inches="tight")
    fig.savefig(OUT / "stability_ablation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    attack_accuracy()
    capacity_stability()
    stability_ablation()
