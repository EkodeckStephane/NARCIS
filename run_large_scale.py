from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
from time import perf_counter
import json
import math
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.cifar import CifarPartition, deterministic_partitions
from narcis.index import CoverIndex, QuantileCodebook
from narcis.model import RobustImageEncoder
from narcis.protocol import NarcisProtocol
from narcis.security import decrypt_payload, encrypt_payload


CALIBRATION = (
    "jpeg_50",
    "gaussian_12",
    "blur_1.5",
    "resize_050",
    "crop_10",
    "rotate_7",
)
CANDIDATES = (1024, 512, 256, 128, 64, 32, 16)


@torch.no_grad()
def embed_dataset(model, dataset, batch_size=128):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    embeddings = []
    identifiers = []
    started = perf_counter()
    for images, names in loader:
        embeddings.append(model(images).cpu().numpy())
        identifiers.extend(names)
    return (
        np.concatenate(embeddings),
        identifiers,
        perf_counter() - started,
    )


@torch.no_grad()
def update_stability(
    model,
    dataset,
    codebooks,
    clean_labels,
    attack,
    batch_size=128,
):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    stable = {size: np.ones(len(dataset), dtype=bool) for size in codebooks}
    offset = 0
    for images, _ in loader:
        attacked = torch.stack([attack(image) for image in images])
        embeddings = model(attacked).cpu().numpy()
        end = offset + len(images)
        for size, codebook in codebooks.items():
            labels = codebook.predict(embeddings)
            stable[size][offset:end] &= labels == clean_labels[size][offset:end]
        offset = end
    return stable


def main():
    parser = ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset_external"))
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("large_scale_results"))
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--train-count", type=int, default=2000)
    parser.add_argument("--index-count", type=int, default=48000)
    parser.add_argument("--image-size", type=int, default=64)
    parser.add_argument("--rs-parity", type=int, default=64)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    _, index_indices, _ = deterministic_partitions(
        args.seed, args.train_count, args.index_count, 1000
    )
    dataset = CifarPartition(
        args.dataset_root, True, index_indices, args.image_size
    )
    model = RobustImageEncoder(embedding_dim=64, base_channels=16)
    model.load_state_dict(
        torch.load(args.model, map_location="cpu", weights_only=True)
    )
    model.eval()

    clean, identifiers, inference_seconds = embed_dataset(model, dataset)
    fit_rows = []
    codebooks = {}
    clean_labels = {}
    for size in CANDIDATES:
        started = perf_counter()
        codebooks[size] = QuantileCodebook.fit(clean, size)
        clean_labels[size] = codebooks[size].predict(clean)
        fit_rows.append(
            {
                "clusters": size,
                "fit_seconds": perf_counter() - started,
                "embedding_bytes": int(clean.nbytes),
            }
        )

    stable = {size: np.ones(len(dataset), dtype=bool) for size in codebooks}
    suite = attack_suite(args.image_size, args.seed)
    calibration_seconds = {}
    for attack_name in CALIBRATION:
        started = perf_counter()
        attack_stable = update_stability(
            model,
            dataset,
            codebooks,
            clean_labels,
            suite[attack_name],
        )
        for size in stable:
            stable[size] &= attack_stable[size]
        calibration_seconds[attack_name] = perf_counter() - started

    rng = np.random.default_rng(args.seed)
    payload_key = rng.bytes(32)
    messages = [
        (
            sequence,
            rng.bytes(8),
        )
        for sequence in range(3)
    ]
    encrypted = [
        (
            sequence,
            plaintext,
            encrypt_payload(
                plaintext,
                payload_key,
                sequence,
                nonce=rng.bytes(12),
            ),
        )
        for sequence, plaintext in messages
    ]

    trials = []
    selected = None
    selected_index = None
    selected_protocol = None
    for size in CANDIDATES:
        positions = np.flatnonzero(stable[size])
        labels = clean_labels[size][positions]
        paths = [identifiers[position] for position in positions]
        index = CoverIndex.build(paths, labels)
        counts = [len(index.buckets.get(label, [])) for label in range(size)]
        protocol = NarcisProtocol(
            index,
            size,
            f"large-scale-{args.seed}".encode(),
            fec="reed_solomon",
            rs_parity=args.rs_parity,
        )
        feasible = all(
            protocol.feasibility(ciphertext)[0]
            for _, _, ciphertext in encrypted
        )
        trial = {
            "clusters": size,
            "bits_per_cover": int(math.log2(size)),
            "stable_images": int(len(positions)),
            "stable_fraction": float(len(positions) / len(dataset)),
            "minimum_bucket": int(min(counts)),
            "median_bucket": float(np.median(counts)),
            "maximum_bucket": int(max(counts)),
            "tested_messages_feasible": feasible,
        }
        trials.append(trial)
        if selected is None and feasible and min(counts) >= 1:
            selected = trial
            selected_index = index
            selected_protocol = protocol

    if selected is None:
        raise RuntimeError("No large-scale configuration is feasible")

    offsets = {name: offset for offset, name in enumerate(identifiers)}
    attack_rows = []
    for sequence, plaintext, ciphertext in encrypted:
        transmission = selected_protocol.encode(ciphertext)
        selected_images = torch.stack(
            [dataset[offsets[name]][0] for name in transmission.covers]
        )
        clean_received = np.array(
            [selected_index.labels[name] for name in transmission.covers]
        )
        for attack_name, attack in suite.items():
            attacked = torch.stack([attack(image) for image in selected_images])
            with torch.no_grad():
                attacked_embeddings = model(attacked).cpu().numpy()
            labels = codebooks[selected["clusters"]].predict(attacked_embeddings)
            try:
                recovered_ciphertext, corrections = selected_protocol.decode_labels(
                    labels.tolist(), transmission.padding_bits
                )
                recovered = decrypt_payload(
                    recovered_ciphertext, payload_key, sequence
                )
                success = recovered == plaintext
            except Exception:
                corrections = -1
                success = False
            attack_rows.append(
                {
                    "sequence": sequence,
                    "attack": attack_name,
                    "covers": len(transmission.covers),
                    "symbol_accuracy": float(
                        np.mean(labels == clean_received)
                    ),
                    "message_success": int(success),
                    "rs_corrections": corrections,
                }
            )

    report = {
        "seed": args.seed,
        "index_images": len(dataset),
        "embedding_inference_seconds": inference_seconds,
        "images_per_second": len(dataset) / inference_seconds,
        "fit_profiles": fit_rows,
        "calibration_seconds": calibration_seconds,
        "trials": trials,
        "selected": selected,
        "attack_results": attack_rows,
        "all_messages_recovered": all(
            row["message_success"] for row in attack_rows
        ),
        "worst_symbol_accuracy": min(
            row["symbol_accuracy"] for row in attack_rows
        ),
    }
    (args.output / "large_scale_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
