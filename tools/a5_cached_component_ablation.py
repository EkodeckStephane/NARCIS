from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

from narcis.benchmark import benchmark_workload, derive_subkey
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol
from tools.tomm_final_channel_recheck import (
    HOLDOUT_ATTACKS,
    EXPECTED_CHECKPOINT_SHA256,
    random_group_bank,
    encode_group_bank_uniform_scheduler,
    FixedMappingProtocol,
    evaluate_holdout_variant,
    symbol_cluster_cycle_coverage,
)
from run_bossbase_campaign import CALIBRATION_ATTACKS

EXPECTED_PER_SEED = {11:240,29:214,47:240,71:231,101:238}

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description="Canonical cached ARCIS A5 component ablation")
    ap.add_argument("--seed",type=int,required=True,choices=tuple(EXPECTED_PER_SEED))
    ap.add_argument("--cache",type=Path,required=True)
    ap.add_argument("--checkpoint",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)

    actual_sha=sha256_file(args.checkpoint)
    expected_sha=EXPECTED_CHECKPOINT_SHA256[args.seed]
    if actual_sha != expected_sha:
        raise SystemExit(f"checkpoint SHA mismatch {actual_sha} != {expected_sha}")

    clean=np.load(args.cache/"clean.npy")
    visual=np.load(args.cache/"visual_features.npy")
    identifiers=(args.cache/"identifiers.txt").read_text(encoding="utf-8").splitlines()
    if not (len(clean)==len(visual)==len(identifiers)==7000):
        raise SystemExit(f"cache alignment mismatch: {len(clean)}, {len(visual)}, {len(identifiers)}")
    calibration={name:np.load(args.cache/f"{name}.npy",mmap_mode="r") for name in CALIBRATION_ATTACKS}
    holdout={name:np.load(args.cache/f"{name}.npy",mmap_mode="r") for name in HOLDOUT_ATTACKS}

    choice,candidates=select_group_bank_projection(
        clean,calibration,visual,clusters=8,group_size=5,
        principal_components=16,random_directions=32,random_seed=20260828+args.seed,
    )
    banks, diagnostics=build_balanced_group_bank(
        choice.labels,choice.calibration_correct,label_count=8,group_size=5,
        seed=20260830+args.seed,restarts=10,swap_steps=6000,
    )
    signatures=majority_failure_signatures(banks,choice.calibration_correct)
    index=CoverIndex.build(identifiers,choice.labels)
    master_key,encryption_key,workload=benchmark_workload("Caltech-101",args.seed)
    metadata_key=derive_subkey(master_key,b"metadata-aead")
    protocol=NarcisProtocol(index,8,master_key,repetition=5,fec="reed_solomon",rs_parity=128)
    positions={identifier:i for i,identifier in enumerate(identifiers)}
    predicted={name:choice.codebook.predict(values) for name,values in holdout.items()}

    random_banks=random_group_bank(choice.labels,8,5,20260919+args.seed)
    random_signatures=majority_failure_signatures(random_banks,choice.calibration_correct)
    fixed_protocol=FixedMappingProtocol(index,8,master_key,repetition=5,fec="reed_solomon",rs_parity=128)
    variants=[
      ("arcis_full",protocol,lambda m:encode_group_bank(protocol,m.envelope,m.sequence,identifiers,banks,signatures)),
      ("random_groups",protocol,lambda m:encode_group_bank(protocol,m.envelope,m.sequence,identifiers,random_banks,random_signatures)),
      ("uniform_group_scheduler",protocol,lambda m:encode_group_bank_uniform_scheduler(protocol,m.envelope,m.sequence,identifiers,banks)),
      ("fixed_mapping",fixed_protocol,lambda m:encode_group_bank(fixed_protocol,m.envelope,m.sequence,identifiers,banks,signatures)),
      ("matched_bucket_baseline",protocol,lambda m:protocol.encode(m.envelope,sequence=m.sequence)),
    ]
    frames=[]; summaries={}
    for name,p,enc in variants:
        frame,summary=evaluate_holdout_variant(
          name=name,protocol=p,encoder=enc,workload=workload,identifiers=identifiers,
          positions=positions,predicted=predicted,encryption_key=encryption_key,metadata_key=metadata_key,
        )
        frame["resampling_seed"]=args.seed
        frames.append(frame); summaries[name]=summary

    full=summaries["arcis_full"]["holdout_successes"]
    if full != EXPECTED_PER_SEED[args.seed]:
        raise SystemExit(f"canonical holdout mismatch seed {args.seed}: got {full}, expected {EXPECTED_PER_SEED[args.seed]}")
    report={
      "status":"PASS",
      "seed":args.seed,
      "checkpoint_sha256":actual_sha,
      "canonical_holdout_successes_expected":EXPECTED_PER_SEED[args.seed],
      "projection":{"name":choice.name,"family":choice.family,"stable_images":int(choice.stable.sum()),"stable_fraction":float(choice.stable.mean())},
      "all_group_banks_reach_lower_bound":bool(all(x.reaches_lower_bound for x in diagnostics)),
      "variants":summaries,
      "cyclic_symbol_cluster_coverage":symbol_cluster_cycle_coverage(protocol),
      "fixed_symbol_cluster_coverage":symbol_cluster_cycle_coverage(fixed_protocol),
    }
    pd.concat(frames,ignore_index=True).to_csv(args.output/"component_ablation_raw.csv",index=False)
    candidates.to_csv(args.output/"projection_candidates.csv",index=False)
    (args.output/"component_ablation_summary.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
