from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import t


ROOT = Path(__file__).resolve().parent
SOURCES = (
    ROOT / "bossbase_results_rs128",
    ROOT / "bossbase_results_rs128_tail",
    ROOT / "bossbase_results_rs128_seed101",
)
OUTPUT = ROOT / "bossbase_results_rs128_final"
FIGURES = ROOT / "paper" / "figures"
OUTPUT.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def read_csv(name: str) -> pd.DataFrame:
    frames = []
    for source in SOURCES:
        path = source / name
        if path.exists() and path.stat().st_size > 2:
            frames.append(pd.read_csv(path))
    return pd.concat(frames, ignore_index=True).drop_duplicates()


def ci95(values: pd.Series) -> tuple[float, float, float]:
    array = values.to_numpy(dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half = float(
        t.ppf(0.975, len(array) - 1)
        * array.std(ddof=1)
        / np.sqrt(len(array))
    )
    return mean, mean - half, mean + half


attacks = read_csv("end_to_end_raw.csv")
trials = read_csv("codebook_trials.csv")
security = read_csv("selection_detectors.csv")
history = pd.read_csv(ROOT / "bossbase_results" / "training_history.csv")

expected_seeds = {11, 29, 47, 71, 101}
found_seeds = set(attacks["seed"].astype(int).unique())
if found_seeds != expected_seeds:
    raise RuntimeError(f"Incomplete seed set: {sorted(found_seeds)}")
if len(attacks) != 1050:
    raise RuntimeError(f"Expected 1050 attack trials, found {len(attacks)}")

attacks.to_csv(OUTPUT / "end_to_end_raw.csv", index=False)
trials.to_csv(OUTPUT / "codebook_trials.csv", index=False)
security.to_csv(OUTPUT / "selection_detectors.csv", index=False)
history.to_csv(OUTPUT / "training_history.csv", index=False)

attack_summary = (
    attacks.groupby("attack", as_index=False)
    .agg(
        trials=("message_success", "size"),
        successes=("message_success", "sum"),
        message_success=("message_success", "mean"),
        symbol_accuracy=("symbol_accuracy", "mean"),
        minimum_symbol_accuracy=("symbol_accuracy", "min"),
        maximum_rs_corrections=("rs_corrections", "max"),
    )
    .sort_values("symbol_accuracy")
)
attack_summary.to_csv(OUTPUT / "end_to_end_summary.csv", index=False)

selected = (
    trials[trials["feasible"].astype(str).str.lower() == "true"]
    .sort_values(["seed", "clusters"], ascending=[True, False])
    .groupby("seed", as_index=False)
    .first()
)
selected.to_csv(OUTPUT / "selected_configurations.csv", index=False)

seed_summary = (
    attacks.groupby("seed", as_index=False)
    .agg(
        trials=("message_success", "size"),
        successes=("message_success", "sum"),
        message_success=("message_success", "mean"),
        symbol_accuracy=("symbol_accuracy", "mean"),
        minimum_symbol_accuracy=("symbol_accuracy", "min"),
    )
)
seed_summary.to_csv(OUTPUT / "seed_summary.csv", index=False)

security_summary = {}
for column in ("global_logistic_auc", "srm_lite_extratrees_auc"):
    mean, low, high = ci95(security[column])
    security_summary[column] = {
        "mean": mean,
        "ci95_low": low,
        "ci95_high": high,
        "minimum": float(security[column].min()),
        "maximum": float(security[column].max()),
    }

report = {
    "dataset": "BOSSBase 1.01",
    "images": 10000,
    "native_channel_resolution": [512, 512],
    "model_input_resolution": [128, 128],
    "seeds": sorted(expected_seeds),
    "messages_per_seed": 10,
    "conditions": 21,
    "total_message_condition_trials": int(len(attacks)),
    "successful_trials": int(attacks["message_success"].sum()),
    "message_success_rate": float(attacks["message_success"].mean()),
    "mean_symbol_accuracy": float(attacks["symbol_accuracy"].mean()),
    "worst_symbol_accuracy": float(attacks["symbol_accuracy"].min()),
    "selected_bits_per_cover": {
        str(int(row.seed)): int(row.bits_per_cover)
        for row in selected.itertuples()
    },
    "security": security_summary,
    "reed_solomon_parity_bytes": 128,
}
(OUTPUT / "campaign_report.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)

fig, ax = plt.subplots(figsize=(7.2, 4.4))
for seed, frame in history.groupby("seed"):
    ax.plot(frame["epoch"], frame["loss"], marker="o", alpha=0.65, label=str(seed))
mean_history = history.groupby("epoch", as_index=False)["loss"].mean()
ax.plot(
    mean_history["epoch"],
    mean_history["loss"],
    color="black",
    linewidth=2.5,
    marker="s",
    label="mean",
)
ax.set_xlabel("Training epoch")
ax.set_ylabel("Representation loss")
ax.set_xticks(sorted(history["epoch"].unique()))
ax.grid(alpha=0.25)
ax.legend(ncol=3, title="Seed")
fig.tight_layout()
fig.savefig(FIGURES / "Fig_06.pdf", bbox_inches="tight")
fig.savefig(FIGURES / "Fig_06.png", dpi=300, bbox_inches="tight")
plt.close(fig)

frame = attack_summary[attack_summary["attack"] != "clean"].copy()
frame["holdout"] = frame["attack"].str.contains("holdout")
labels = (
    frame["attack"]
    .str.replace("_holdout", " (H)", regex=False)
    .str.replace("_", " ", regex=False)
)
fig, ax = plt.subplots(figsize=(8.2, 5.0))
ax.barh(
    labels,
    frame["symbol_accuracy"],
    color=["#b54a4a" if value else "#315f8c" for value in frame["holdout"]],
)
ax.set_xlim(0.74, 1.005)
ax.set_xlabel("Mean symbol accuracy")
ax.set_ylabel("Channel condition")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURES / "Fig_04.pdf", bbox_inches="tight")
fig.savefig(FIGURES / "Fig_04.png", dpi=300, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.8, 4.2))
x = np.arange(len(security))
width = 0.36
ax.bar(
    x - width / 2,
    security["global_logistic_auc"],
    width,
    label="Global logistic",
    color="#315f8c",
)
ax.bar(
    x + width / 2,
    security["srm_lite_extratrees_auc"],
    width,
    label="SRM-lite ExtraTrees",
    color="#c58b2a",
)
ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
ax.set_xticks(x, security["seed"].astype(str))
ax.set_ylim(0.4, 0.6)
ax.set_xlabel("Seed")
ax.set_ylabel("Selection-detection AUC")
ax.legend()
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(FIGURES / "bossbase_detectability.pdf", bbox_inches="tight")
fig.savefig(FIGURES / "bossbase_detectability.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print(json.dumps(report, indent=2))
