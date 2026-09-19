from __future__ import annotations
from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon

SEEDS=(131,157,181,211,241)
PAYLOADS=(8,32,64)
ATTACKS=(
    "gaussian_7","gaussian_18","blur_1.0","blur_2.1","crop_06","crop_09",
    "crop_14","rotate_4","rotate_6","rotate_11","jpeg_65",
    "crop_09_jpeg_65","crop_14_blur_1.0",
)
EXPECTED_IMAGES={8:205,32:335,64:580}


def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()


def locate_seed_dirs(root:Path):
    found={}
    for p in root.rglob("manifest.json"):
        try:d=json.loads(p.read_text())
        except Exception:continue
        seed=d.get("seed")
        if seed in SEEDS and (p.parent/"fresh_payload_results.csv").exists():
            found[seed]=p.parent
    return found


def safe_smd(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    v=(np.var(a,ddof=1)+np.var(b,ddof=1))/2
    return float((np.mean(a)-np.mean(b))/math.sqrt(v)) if v>0 else 0.0


def main():
    ap=ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    dirs=locate_seed_dirs(args.input)
    missing=sorted(set(SEEDS)-set(dirs))
    if missing:raise RuntimeError(f"missing seed artifacts: {missing}")

    payload=[];ablation=[];network=[];sequence=[];manifests=[]
    for seed in SEEDS:
        d=dirs[seed]
        payload.append(pd.read_csv(d/"fresh_payload_results.csv"))
        ablation.append(pd.read_csv(d/"ablation_results.csv"))
        network.append(pd.read_csv(d/"network_stress.csv"))
        sequence.append(pd.read_csv(d/"sequential_features.csv"))
        manifests.append(json.loads((d/"manifest.json").read_text()))

    payload=pd.concat(payload,ignore_index=True)
    ablation=pd.concat(ablation,ignore_index=True)
    network=pd.concat(network,ignore_index=True)
    sequence=pd.concat(sequence,ignore_index=True)
    payload.to_csv(args.output/"fresh_payload_all.csv",index=False)
    ablation.to_csv(args.output/"ablation_all.csv",index=False)
    network.to_csv(args.output/"network_stress_all.csv",index=False)
    sequence.to_csv(args.output/"sequential_features_all.csv",index=False)

    expected_trials=len(SEEDS)*len(PAYLOADS)*len(ATTACKS)*10
    if len(payload)!=expected_trials:raise RuntimeError((len(payload),expected_trials))
    if sorted(payload.seed.unique())!=list(SEEDS):raise RuntimeError("seed mismatch")
    if sorted(payload.payload_bytes.unique())!=list(PAYLOADS):raise RuntimeError("payload mismatch")
    if sorted(payload.attack.unique())!=sorted(ATTACKS):raise RuntimeError("attack mismatch")
    for p,n in EXPECTED_IMAGES.items():
        observed=set(payload.loc[payload.payload_bytes==p,"perm_rrns_images"].astype(int))
        if observed!={n}:raise RuntimeError(f"traffic invariant {p}: {observed}")

    summary=(payload.groupby(["payload_bytes","attack"],as_index=False)
      .agg(trials=("perm_rrns_success","size"),successes=("perm_rrns_success","sum"),
           images=("perm_rrns_images","first"),mean_states=("perm_rrns_candidate_states","mean"),
           max_states=("perm_rrns_candidate_states","max"),mean_decode_s=("perm_rrns_decode_seconds","mean"),
           mean_crop_top1_errors=("crop_top1_residue_errors","mean"),
           mean_general_top1_errors=("general_top1_residue_errors","mean"),
           arcis_trials=("arcis_rs128_success","size"),arcis_successes=("arcis_rs128_success","sum"),
           arcis_images=("arcis_rs128_images","first")))
    summary["success_rate"]=summary.successes/summary.trials
    summary["arcis_success_rate"]=summary.arcis_successes/summary.arcis_trials
    summary["useful_bits_per_image"]=summary.payload_bytes*8/summary.images
    summary.to_csv(args.output/"fresh_summary_all.csv",index=False)

    by_payload=(payload.groupby("payload_bytes",as_index=False)
       .agg(trials=("perm_rrns_success","size"),successes=("perm_rrns_success","sum"),images=("perm_rrns_images","first"),
            arcis_successes=("arcis_rs128_success","sum"),arcis_images=("arcis_rs128_images","first")))
    by_payload["success_rate"]=by_payload.successes/by_payload.trials
    by_payload["arcis_success_rate"]=by_payload.arcis_successes/by_payload.trials
    by_payload["useful_bits_per_image"]=by_payload.payload_bytes*8/by_payload.images
    by_payload.to_csv(args.output/"fresh_by_payload.csv",index=False)

    abl=(ablation.groupby(["payload_bytes","attack","variant"],as_index=False)
         .agg(trials=("success","size"),successes=("success","sum"),mean_states=("tested_states","mean")))
    abl["success_rate"]=abl.successes/abl.trials
    abl.to_csv(args.output/"ablation_summary.csv",index=False)

    net=(network.groupby(["payload_bytes","stress","outcome"],as_index=False).size().rename(columns={"size":"count"}))
    net.to_csv(args.output/"network_stress_summary.csv",index=False)
    unsafe=int((network.outcome=="unexpected_plaintext").sum())

    trans_cols=[f"transition_{i}_{j}" for i in range(8) for j in range(8)]
    seq_metrics={}
    for p in PAYLOADS:
        subset=sequence[sequence.payload_bytes==p]
        new=subset[subset.method=="perm_rrns"]
        old=subset[subset.method=="arcis_rs128"]
        a=new[trans_cols].mean().to_numpy(float);b=old[trans_cols].mean().to_numpy(float)
        a=a/max(a.sum(),1e-12);b=b/max(b.sum(),1e-12)
        seq_metrics[str(p)]={
          "transition_js_distance":float(jensenshannon(a,b,base=2.0)),
          "adjacent_cosine_mean_smd":safe_smd(new.adjacent_cosine_mean,old.adjacent_cosine_mean),
          "within_group_cosine_mean_smd":safe_smd(new.within_group_cosine_mean,old.within_group_cosine_mean),
          "cluster_entropy_smd":safe_smd(new.cluster_entropy,old.cluster_entropy),
          "sequence_classifier_status":"BLOCKED_PENDING_FROZEN_DEVELOPMENT_ONLY_CLASSIFIER"
        }
    (args.output/"sequential_detectability.json").write_text(json.dumps(seq_metrics,indent=2))

    overall={
      "fresh_protocol":"ARCIS-PERM-RRNS-v1",
      "seeds":list(SEEDS),
      "attacks":list(ATTACKS),
      "payload_sizes":list(PAYLOADS),
      "expected_trials":expected_trials,
      "observed_trials":len(payload),
      "successes":int(payload.perm_rrns_success.sum()),
      "success_rate":float(payload.perm_rrns_success.mean()),
      "arcis_rs128_successes":int(payload.arcis_rs128_success.sum()),
      "arcis_rs128_success_rate":float(payload.arcis_rs128_success.mean()),
      "unsafe_network_plaintexts":unsafe,
      "checkpoint_sha256":{str(m["seed"]):m["checkpoint_sha256"] for m in manifests},
      "evidence_status":"COMPLETE" if len(payload)==expected_trials and unsafe==0 else "FAIL",
      "statistical_note":"Five seeded resamplings are not independent population replications; pooled values are descriptive."
    }
    (args.output/"fresh_aggregate.json").write_text(json.dumps(overall,indent=2))

    gates={
      "Gate1":{"status":"PASS","basis":"Scientific object is the authenticated robust cover-selection channel with local permutation/RRNS coding, not repository tooling."},
      "Gate2":{"status":"PASS_WITH_SCOPE","basis":"Fresh payload, ablation, network and sequence-distribution evidence are directly recorded; claims must remain bounded to measured conditions."},
      "Gate3":{"status":"PENDING_MANUSCRIPT","basis":"Development history must be removed from any revised submission narrative."},
      "Gate4":{"status":"PENDING_SOTA_REAUDIT","basis":"The combined local-permutation/RRNS contribution requires a fresh prior-art search before novelty wording is frozen."},
      "Gate5":{"status":"PARTIAL","basis":"Fresh visual holdout, ablations and network stress are complete if aggregate evidence is COMPLETE; the preregistered development-only sequential classifier is still pending."},
      "Gate6":{"status":"PENDING_MANUSCRIPT","basis":"No revised manuscript/PDF has yet been produced from this branch."},
      "Gate7":{"status":"PASS_WITH_SCOPE","basis":"Results are experimental and do not establish deployment or universal channel robustness."},
      "Gate8":{"status":"PASS","basis":"Per-seed manifests, hashes, raw CSV outputs and frozen protocol are retained."},
      "Gate9":{"status":"PENDING_MANUSCRIPT_AND_REFERENCES","basis":"Bibliographic and cross-artifact editorial consistency require the later manuscript rewrite."},
      "Gate10":{"status":"BLOCKED","basis":"Submission readiness cannot pass before the development-only sequence classifier, SOTA re-audit, manuscript rewrite, claim/code/data reconciliation and rendered-PDF inspection."}
    }
    (args.output/"Q1_GATE_AUDIT.json").write_text(json.dumps(gates,indent=2))
    lines=["# ARCIS-PERM-RRNS v1 — Fresh Campaign Audit","",f"Fresh trials: **{len(payload)}**; authenticated successes: **{int(payload.perm_rrns_success.sum())}**.",f"Original ARCIS RS128 successes on the same fresh attacks: **{int(payload.arcis_rs128_success.sum())}/{len(payload)}**.","",f"Network unsafe plaintext outcomes: **{unsafe}**.","","## Q1 gates"]
    for name,item in gates.items():lines.append(f"- **{name}: {item['status']}** — {item['basis']}")
    lines+=["","## Current submission status","","**Gate 10 is deliberately BLOCKED.** The fresh experimental chain can close before the manuscript is rewritten, but submission readiness cannot be inherited from the older TOMM snapshot."]
    (args.output/"FRESH_Q1_AUDIT.md").write_text("\n".join(lines)+"\n")
    manifest={p.name:sha256(p) for p in sorted(args.output.iterdir()) if p.is_file()}
    (args.output/"aggregate_sha256.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(overall,indent=2))

if __name__=="__main__":main()
