from pathlib import Path
import json

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from scipy.stats import t


DATASETS = {
    "BOSSBase": Path("bossbase_cnn_results"),
    "Caltech-101": Path("caltech101_results"),
}
OUTPUT = Path("q1_extension_results")
FIGURES = Path("paper/figures")


def interval(values: pd.Series) -> dict:
    values = values.astype(float)
    half = t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    return {
        "mean": float(values.mean()),
        "ci95_low": float(values.mean() - half),
        "ci95_high": float(values.mean() + half),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def selected_configurations(trials: pd.DataFrame) -> pd.DataFrame:
    return (
        trials[trials["feasible"]]
        .sort_values(["seed", "clusters"], ascending=[True, False])
        .groupby("seed", as_index=False)
        .head(1)
    )


def save_robustness_figure(attacks: dict[str, pd.DataFrame]) -> None:
    order = (
        attacks["BOSSBase"]
        .groupby("attack")["symbol_accuracy"]
        .mean()
        .sort_values()
        .index.tolist()
    )
    x = np.arange(len(order))
    width = 0.38
    fig, ax = plt.subplots(figsize=(10.8, 4.6))
    for offset, (name, frame) in zip((-width / 2, width / 2), attacks.items()):
        values = frame.groupby("attack")["symbol_accuracy"].mean().reindex(order)
        ax.bar(x + offset, 100 * values, width, label=name)
    ax.set_ylabel("Mean symbol accuracy (%)")
    ax.set_ylim(78, 101)
    ax.set_xticks(x, [value.replace("_", " ") for value in order], rotation=55, ha="right")
    ax.axhline(100, color="0.5", linewidth=0.7)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(
            FIGURES / f"cross_dataset_robustness.{suffix}",
            dpi=350,
            bbox_inches="tight",
        )
    plt.close(fig)


def save_detector_figure(detectors: dict[str, pd.DataFrame]) -> None:
    columns = [
        ("global_logistic_auc", "Global\nlogistic"),
        ("srm_lite_extratrees_auc", "Residual\nExtraTrees"),
        ("selection_cnn_auc", "Selection\nCNN"),
    ]
    x = np.arange(len(columns))
    width = 0.34
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for offset, (dataset, frame) in zip((-width / 2, width / 2), detectors.items()):
        means = []
        errors = []
        for column, _ in columns:
            stats = interval(frame[column])
            means.append(stats["mean"])
            errors.append(stats["ci95_high"] - stats["mean"])
        ax.bar(
            x + offset,
            means,
            width,
            yerr=errors,
            capsize=3,
            label=dataset,
        )
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.set_ylabel("Selection-detection AUC")
    ax.set_ylim(0.43, 0.60)
    ax.set_xticks(x, [label for _, label in columns])
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(
            FIGURES / f"cross_dataset_detectability.{suffix}",
            dpi=350,
            bbox_inches="tight",
        )
    plt.close(fig)


def box(ax, x, y, w, h, text, color, fontsize=10, weight="normal"):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        facecolor=color,
        edgecolor="#243447",
        linewidth=1.2,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        weight=weight,
        color="#17202a",
    )


def save_graphical_abstract() -> None:
    fig, ax = plt.subplots(figsize=(13.4, 5.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.94,
        "NARCIS: verified coverless signaling from unchanged natural images",
        ha="center",
        va="center",
        fontsize=18,
        weight="bold",
        color="#17324d",
    )

    box(ax, 0.02, 0.56, 0.15, 0.23, "Shared natural-image\nindex", "#dbeafe", 12, "bold")
    box(ax, 0.205, 0.56, 0.16, 0.23, "Invariant neural\ndescriptor", "#e0f2fe", 12, "bold")
    box(ax, 0.40, 0.56, 0.18, 0.23, "Attack-qualified\nbalanced codebook", "#dcfce7", 12, "bold")
    box(ax, 0.615, 0.56, 0.17, 0.23, "AES-GCM +\nReed-Solomon", "#fef3c7", 12, "bold")
    box(ax, 0.82, 0.56, 0.16, 0.23, "Unchanged cover\nsequence", "#fae8ff", 12, "bold")
    for start, end in ((0.17, 0.205), (0.365, 0.40), (0.58, 0.615), (0.785, 0.82)):
        ax.annotate(
            "",
            xy=(end, 0.675),
            xytext=(start, 0.675),
            arrowprops={"arrowstyle": "->", "lw": 2, "color": "#334155"},
        )

    ax.text(
        0.5,
        0.48,
        "Largest feasible alphabet is selected only when every protected-message symbol has sufficient qualified covers",
        ha="center",
        fontsize=10.5,
        color="#334155",
    )
    box(ax, 0.05, 0.12, 0.25, 0.23, "BOSSBase\n1,050 / 1,050 recoveries\n98.74% mean accuracy", "#eef2ff", 11, "bold")
    box(ax, 0.375, 0.12, 0.25, 0.23, "Caltech-101 RGB\n525 / 525 recoveries\n98.59% mean accuracy", "#ecfeff", 11, "bold")
    box(ax, 0.70, 0.12, 0.25, 0.23, "Selection CNN\nAUC 0.515 / 0.530\n95% CIs include 0.5", "#f0fdf4", 11, "bold")
    ax.text(
        0.5,
        0.045,
        "Measured scope: 5 seeds per dataset, 21 clean/calibration/holdout conditions, 3-4 operational bits per cover",
        ha="center",
        fontsize=10,
        color="#475569",
    )
    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(
            FIGURES / f"graphical_abstract.{suffix}",
            dpi=350,
            bbox_inches="tight",
            facecolor="white",
        )
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    attacks = {}
    detectors = {}
    report = {"datasets": {}}
    all_selected = []
    all_detector_rows = []
    all_attack_rows = []

    for name, root in DATASETS.items():
        attack_frame = pd.read_csv(root / "end_to_end_raw.csv")
        detector_frame = pd.read_csv(root / "selection_detectors.csv")
        trials = pd.read_csv(root / "codebook_trials.csv")
        selected = selected_configurations(trials).copy()
        selected.insert(0, "dataset", name)
        all_selected.append(selected)

        detector_copy = detector_frame.copy()
        detector_copy.insert(0, "dataset", name)
        all_detector_rows.append(detector_copy)

        attack_summary = (
            attack_frame.groupby("attack", as_index=False)
            .agg(
                trials=("message_success", "size"),
                message_success=("message_success", "mean"),
                symbol_accuracy=("symbol_accuracy", "mean"),
                minimum_symbol_accuracy=("symbol_accuracy", "min"),
            )
        )
        attack_summary.insert(0, "dataset", name)
        all_attack_rows.append(attack_summary)

        attacks[name] = attack_frame
        detectors[name] = detector_frame
        report["datasets"][name] = {
            "trials": int(len(attack_frame)),
            "successful_trials": int(attack_frame["message_success"].sum()),
            "message_success": float(attack_frame["message_success"].mean()),
            "mean_symbol_accuracy": float(attack_frame["symbol_accuracy"].mean()),
            "worst_symbol_accuracy": float(attack_frame["symbol_accuracy"].min()),
            "maximum_rs_corrections": int(attack_frame["rs_corrections"].max()),
            "selected_bits_per_cover": {
                str(int(row.seed)): int(row.bits_per_cover)
                for row in selected.itertuples()
            },
            "detectors": {
                column: interval(detector_frame[column])
                for column in (
                    "global_logistic_auc",
                    "srm_lite_extratrees_auc",
                    "selection_cnn_auc",
                )
            },
        }

    pd.concat(all_selected).to_csv(
        OUTPUT / "selected_configurations.csv",
        index=False,
    )
    pd.concat(all_detector_rows).to_csv(
        OUTPUT / "selection_detectors.csv",
        index=False,
    )
    pd.concat(all_attack_rows).to_csv(
        OUTPUT / "attack_summary.csv",
        index=False,
    )
    report["combined_trials"] = sum(
        item["trials"] for item in report["datasets"].values()
    )
    report["combined_successful_trials"] = sum(
        item["successful_trials"] for item in report["datasets"].values()
    )
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    save_robustness_figure(attacks)
    save_detector_figure(detectors)
    save_graphical_abstract()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
