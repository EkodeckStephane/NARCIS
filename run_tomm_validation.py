from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.data import discover_images
from narcis.tomm_evaluation import (
    glcm_selection_auc,
    run_real_payload_channel,
    select_calibration_locked_projection,
    summarize_payload_trials,
    write_choice_manifest,
)
from run_bossbase_campaign import (
    CALIBRATION_ATTACKS,
    NativeImageDataset,
    dataset_statistics,
    embed_dataset,
    encrypted_messages,
    selection_auc,
    train_encoder,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_SEEDS = (11, 29, 47, 71, 101)


def parse_int_tuple(value: str) -> tuple[int, ...]:
    parsed = tuple(int(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise ValueError("at least one integer is required")
    return parsed


def preflight_dataset(
    *,
    name: str,
    dataset_root: Path,
    checkpoint_root: Path,
    seeds: tuple[int, ...],
    train_count: int,
    index_count: int,
    epochs: int,
) -> dict:
    report = {
        "dataset": name,
        "dataset_root": str(dataset_root),
        "dataset_root_exists": dataset_root.exists(),
        "checkpoint_root": str(checkpoint_root),
        "epochs": epochs,
        "required_images": train_count + index_count,
        "images_found": 0,
        "checkpoints": {},
        "ready": False,
    }
    if dataset_root.exists():
        try:
            paths = discover_images(dataset_root)
            report["images_found"] = len(paths)
        except Exception as error:
            report["dataset_error"] = f"{type(error).__name__}: {error}"
    for seed in seeds:
        checkpoint = checkpoint_root / f"encoder_seed_{seed}.pt"
        report["checkpoints"][str(seed)] = {
            "path": str(checkpoint),
            "exists": checkpoint.exists(),
        }
    enough_images = report["images_found"] >= report["required_images"]
    checkpoint_ready = epochs > 0 or all(
        item["exists"] for item in report["checkpoints"].values()
    )
    report["ready"] = bool(
        report["dataset_root_exists"] and enough_images and checkpoint_ready
    )
    return report


def prepare_partition(
    *,
    dataset_root: Path,
    checkpoint_root: Path,
    output: Path,
    seed: int,
    train_count: int,
    index_count: int,
    epochs: int,
    input_mode: str,
    channel_size: int,
    model_size: int,
    embedding_dim: int,
):
    paths = discover_images(dataset_root)
    if train_count + index_count > len(paths):
        raise ValueError(
            f"partition requires {train_count + index_count} images, "
            f"but only {len(paths)} were discovered"
        )
    order = np.random.default_rng(seed).permutation(len(paths))
    train_paths = [paths[position] for position in order[:train_count]]
    index_paths = [
        paths[position]
        for position in order[train_count : train_count + index_count]
    ]
    dataset = NativeImageDataset(index_paths, input_mode, channel_size)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    model, history = train_encoder(
        train_paths,
        seed,
        epochs,
        model_size,
        embedding_dim,
        output,
        checkpoint_root=checkpoint_root,
        input_mode=input_mode,
        channel_size=channel_size,
    )
    clean, identifiers, clean_seconds = embed_dataset(
        model,
        dataset,
        model_size,
    )
    suite = attack_suite(channel_size, seed)
    attacked = {}
    calibration_seconds = {}
    for attack_name in CALIBRATION_ATTACKS:
        embeddings, _, seconds = embed_dataset(
            model,
            dataset,
            model_size,
            suite[attack_name],
        )
        attacked[attack_name] = embeddings
        calibration_seconds[attack_name] = seconds
    visual_features = dataset_statistics(dataset)
    return {
        "dataset": dataset,
        "model": model,
        "history": history,
        "clean": clean,
        "identifiers": identifiers,
        "attacked": attacked,
        "visual_features": visual_features,
        "clean_embedding_seconds": clean_seconds,
        "calibration_seconds": calibration_seconds,
    }


def repeated_detectability(
    *,
    dataset,
    identifiers: list[str],
    selected_ids: list[str],
    seed: int,
    repeats: int,
    samples: int,
    cnn_epochs: int,
) -> pd.DataFrame:
    rows = []
    for repeat in range(repeats):
        local_seed = seed * 10000 + repeat
        conventional = selection_auc(
            dataset,
            identifiers,
            selected_ids,
            local_seed,
            maximum_per_class=samples,
            cnn_epochs=cnn_epochs,
        )
        glcm = glcm_selection_auc(
            dataset,
            identifiers,
            selected_ids,
            local_seed,
            maximum_per_class=samples,
        )
        rows.append(
            {
                "seed": seed,
                "repeat": repeat,
                "split_seed": local_seed,
                **conventional,
                "glcm_auc": glcm["glcm_auc"],
                "glcm_feature_count": glcm["glcm_feature_count"],
            }
        )
    return pd.DataFrame(rows)


def run_dataset(
    *,
    name: str,
    dataset_root: Path,
    checkpoint_root: Path,
    output_root: Path,
    seeds: tuple[int, ...],
    train_count: int,
    index_count: int,
    input_mode: str,
    channel_size: int,
    model_size: int,
    embedding_dim: int,
    epochs: int,
    clusters: int,
    payload_sizes: tuple[int, ...],
    messages: int,
    rs_parity: int,
    detector_repeats: int,
    detector_samples: int,
    detector_epochs: int,
    principal_components: int,
    random_directions: int,
) -> None:
    dataset_output = output_root / name.lower().replace("-", "_")
    dataset_output.mkdir(parents=True, exist_ok=True)
    all_payload = []
    all_detector = []
    all_selected_projection = []

    for seed in seeds:
        partition_output = dataset_output / f"seed_{seed}"
        partition_output.mkdir(parents=True, exist_ok=True)
        prepared = prepare_partition(
            dataset_root=dataset_root,
            checkpoint_root=checkpoint_root,
            output=partition_output,
            seed=seed,
            train_count=train_count,
            index_count=index_count,
            epochs=epochs,
            input_mode=input_mode,
            channel_size=channel_size,
            model_size=model_size,
            embedding_dim=embedding_dim,
        )

        choice, candidates = select_calibration_locked_projection(
            prepared["clean"],
            prepared["attacked"],
            prepared["identifiers"],
            prepared["visual_features"],
            clusters,
            principal_components=principal_components,
            random_directions=random_directions,
            random_seed=20260828 + seed,
        )
        candidates.to_csv(
            partition_output / "projection_candidates.csv",
            index=False,
        )
        write_choice_manifest(
            choice,
            partition_output / "projection_choice.json",
            name,
            seed,
        )
        all_selected_projection.append(
            {
                "dataset": name,
                "seed": seed,
                "direction": choice.name,
                "family": choice.family,
                "clusters": clusters,
                "stable_images": int(choice.stable.sum()),
                "stable_fraction": float(choice.stable.mean()),
                "minimum_bucket": choice.index.minimum_bucket_size(clusters),
                "effective_sample_size": choice.diagnostics.effective_sample_size,
                "mean_abs_smd_before": choice.diagnostics.mean_abs_smd_before,
                "mean_abs_smd_after": choice.diagnostics.mean_abs_smd_after,
                "max_abs_smd_before": choice.diagnostics.max_abs_smd_before,
                "max_abs_smd_after": choice.diagnostics.max_abs_smd_after,
            }
        )

        payload_raw, selected_ids = run_real_payload_channel(
            dataset_name=name,
            dataset=prepared["dataset"],
            model=prepared["model"],
            model_size=model_size,
            channel_size=channel_size,
            identifiers=prepared["identifiers"],
            choice=choice,
            encrypted_message_factory=encrypted_messages,
            seed=seed,
            payload_sizes=payload_sizes,
            messages_per_size=messages,
            rs_parity=rs_parity,
        )
        payload_raw.to_csv(partition_output / "payload_raw.csv", index=False)
        payload_summary = summarize_payload_trials(payload_raw)
        payload_summary.to_csv(
            partition_output / "payload_summary.csv",
            index=False,
        )
        all_payload.append(payload_raw)

        if selected_ids:
            detector = repeated_detectability(
                dataset=prepared["dataset"],
                identifiers=prepared["identifiers"],
                selected_ids=selected_ids,
                seed=seed,
                repeats=detector_repeats,
                samples=detector_samples,
                cnn_epochs=detector_epochs,
            )
            detector.insert(0, "dataset", name)
            detector.to_csv(
                partition_output / "detectability_repetitions.csv",
                index=False,
            )
            all_detector.append(detector)

        timing = {
            "dataset": name,
            "seed": seed,
            "clean_embedding_seconds": prepared["clean_embedding_seconds"],
            "calibration_seconds": prepared["calibration_seconds"],
            "epochs": epochs,
            "model_size": model_size,
            "embedding_dim": embedding_dim,
        }
        (partition_output / "timing.json").write_text(
            json.dumps(timing, indent=2), encoding="utf-8"
        )
        if prepared["history"]:
            pd.DataFrame(prepared["history"]).to_csv(
                partition_output / "training_history.csv",
                index=False,
            )

    pd.DataFrame(all_selected_projection).to_csv(
        dataset_output / "selected_projections.csv", index=False
    )
    if all_payload:
        combined_payload = pd.concat(all_payload, ignore_index=True)
        combined_payload.to_csv(
            dataset_output / "payload_raw_all_seeds.csv",
            index=False,
        )
        summarize_payload_trials(combined_payload).to_csv(
            dataset_output / "payload_summary_all_seeds.csv",
            index=False,
        )
    if all_detector:
        pd.concat(all_detector, ignore_index=True).to_csv(
            dataset_output / "detectability_all_seeds.csv",
            index=False,
        )


def main() -> None:
    parser = ArgumentParser(
        description="Fresh ACM TOMM validation campaign for NARCIS"
    )
    parser.add_argument("--stage", choices=("preflight", "boss", "caltech", "all"), default="preflight")
    parser.add_argument("--bossbase-root", type=Path, default=ROOT / "dataset_external" / "BOSSbase")
    parser.add_argument("--caltech-root", type=Path, default=ROOT / "dataset_external" / "caltech101" / "images")
    parser.add_argument("--boss-checkpoints", type=Path, default=ROOT / "bossbase_results")
    parser.add_argument("--caltech-checkpoints", type=Path, default=ROOT / "caltech101_results")
    parser.add_argument("--output", type=Path, default=ROOT / "tomm_results")
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--payload-sizes", default="8,32,64")
    parser.add_argument("--messages", type=int, default=10)
    parser.add_argument("--epochs", type=int, default=0)
    parser.add_argument("--clusters", type=int, default=16)
    parser.add_argument("--rs-parity", type=int, default=128)
    parser.add_argument("--model-size", type=int, default=128)
    parser.add_argument("--embedding-dim", type=int, default=64)
    parser.add_argument("--detector-repeats", type=int, default=20)
    parser.add_argument("--detector-samples", type=int, default=500)
    parser.add_argument("--detector-epochs", type=int, default=8)
    parser.add_argument("--principal-components", type=int, default=16)
    parser.add_argument("--random-directions", type=int, default=32)
    args = parser.parse_args()

    seeds = parse_int_tuple(args.seeds)
    payload_sizes = parse_int_tuple(args.payload_sizes)
    args.output.mkdir(parents=True, exist_ok=True)

    boss_preflight = preflight_dataset(
        name="BOSSBase",
        dataset_root=args.bossbase_root,
        checkpoint_root=args.boss_checkpoints,
        seeds=seeds,
        train_count=2000,
        index_count=8000,
        epochs=args.epochs,
    )
    caltech_preflight = preflight_dataset(
        name="Caltech-101",
        dataset_root=args.caltech_root,
        checkpoint_root=args.caltech_checkpoints,
        seeds=seeds,
        train_count=1500,
        index_count=7000,
        epochs=args.epochs,
    )
    preflight = {
        "requested_stage": args.stage,
        "payload_sizes": payload_sizes,
        "seeds": seeds,
        "bossbase": boss_preflight,
        "caltech101": caltech_preflight,
    }
    (args.output / "preflight.json").write_text(
        json.dumps(preflight, indent=2), encoding="utf-8"
    )
    print(json.dumps(preflight, indent=2))
    if args.stage == "preflight":
        return

    if args.stage in {"boss", "all"}:
        if not boss_preflight["ready"]:
            raise RuntimeError(
                "BOSSBase preflight failed; inspect tomm_results/preflight.json"
            )
        run_dataset(
            name="BOSSBase",
            dataset_root=args.bossbase_root,
            checkpoint_root=args.boss_checkpoints,
            output_root=args.output,
            seeds=seeds,
            train_count=2000,
            index_count=8000,
            input_mode="L",
            channel_size=512,
            model_size=args.model_size,
            embedding_dim=args.embedding_dim,
            epochs=args.epochs,
            clusters=args.clusters,
            payload_sizes=payload_sizes,
            messages=args.messages,
            rs_parity=args.rs_parity,
            detector_repeats=args.detector_repeats,
            detector_samples=args.detector_samples,
            detector_epochs=args.detector_epochs,
            principal_components=args.principal_components,
            random_directions=args.random_directions,
        )

    if args.stage in {"caltech", "all"}:
        if not caltech_preflight["ready"]:
            raise RuntimeError(
                "Caltech-101 preflight failed; inspect tomm_results/preflight.json"
            )
        run_dataset(
            name="Caltech-101",
            dataset_root=args.caltech_root,
            checkpoint_root=args.caltech_checkpoints,
            output_root=args.output,
            seeds=seeds,
            train_count=1500,
            index_count=7000,
            input_mode="RGB",
            channel_size=256,
            model_size=args.model_size,
            embedding_dim=args.embedding_dim,
            epochs=args.epochs,
            clusters=args.clusters,
            payload_sizes=payload_sizes,
            messages=args.messages,
            rs_parity=args.rs_parity,
            detector_repeats=args.detector_repeats,
            detector_samples=args.detector_samples,
            detector_epochs=args.detector_epochs,
            principal_components=args.principal_components,
            random_directions=args.random_directions,
        )


if __name__ == "__main__":
    main()
