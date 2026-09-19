from __future__ import annotations
import json
from pathlib import Path

EXPECTED = {
    "arcis_full": 1163,
    "random_groups": 1042,
    "uniform_group_scheduler": 1160,
    "fixed_mapping": 1166,
    "matched_bucket_baseline": 1038,
}
EXPECTED_PER_SEED = [240, 214, 240, 231, 238]

def main() -> None:
    path = Path("tomm_results/A5_CANONICAL_COMPONENT_ABLATION.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "PASS"
    assert data["canonical_reproduction"]["exact_match"] is True
    assert data["canonical_reproduction"]["expected_successes"] == 1163
    assert data["canonical_reproduction"]["observed_successes"] == 1163
    assert data["canonical_reproduction"]["per_seed_observed"] == EXPECTED_PER_SEED
    for name, successes in EXPECTED.items():
        row = data["variants"][name]
        assert row["trials"] == 1200
        assert row["successes"] == successes
    assert data["paired_descriptive_vs_arcis"]["random_groups"] == {
        "arcis_gain_other_fail": 121, "arcis_fail_other_gain": 0,
        "both_success": 1042, "both_fail": 37,
    }
    assert data["paired_descriptive_vs_arcis"]["matched_bucket_baseline"] == {
        "arcis_gain_other_fail": 125, "arcis_fail_other_gain": 0,
        "both_success": 1038, "both_fail": 37,
    }
    assert data["cycle_coverage"]["arcis_each_symbol_clusters"] == 8
    assert data["cycle_coverage"]["fixed_mapping_each_symbol_clusters"] == 1
    full_cv = data["variants"]["arcis_full"]["mean_label_emission_cv"]
    fixed_cv = data["variants"]["fixed_mapping"]["mean_label_emission_cv"]
    assert fixed_cv > 5 * full_cv
    print({"A5_static_consistency":"PASS","arcis":1163,"random_groups":1042,"matched_bucket":1038,"fixed_mapping":1166})

if __name__ == "__main__":
    main()
