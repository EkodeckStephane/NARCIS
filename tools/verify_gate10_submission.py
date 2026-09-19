from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLE = "ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints"
SNAPSHOT = "254f31e7c44e43f104509c117b0efb4c414dcdcd"
RUN = "35460375489"

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def main() -> None:
    p00 = read("paper/ACM_TOMM/ARCIS_TOMM_part00.tex")
    parts = "\n".join(read(f"paper/ACM_TOMM/ARCIS_TOMM_part0{i}.tex") for i in range(6))
    cover = read("paper/ACM_TOMM/COVER_LETTER_ARCIS_TOMM.tex")
    meta = read("paper/ACM_TOMM/SCHOLARONE_METADATA.txt")
    bib = read("paper/ACM_TOMM/ARCIS_references.bib")
    fact = read("FACT_CHECK.md")
    status = read("SESSION_STATUS.md")
    checklist = read("paper/ACM_TOMM/SUBMISSION_CHECKLIST.md")
    dclose = read("paper/ACM_TOMM/D1_D7_CLOSURE.md")

    for blob, name in [(p00, "manuscript"), (cover, "cover letter"), (meta, "ScholarOne metadata")]:
        assert TITLE in blob, f"title mismatch in {name}"
    for blob, name in [(p00, "manuscript"), (cover, "cover letter"), (meta, "ScholarOne metadata")]:
        assert "Chantal Marguerite Mveh-Abia" in blob and "cmmveh@yahoo.fr" in blob, f"corresponding-author mismatch in {name}"

    a3 = json.loads(read("tomm_results/A3_AUTHENTICATED_CONTROL_PLANE_AUDIT.json"))
    a4 = json.loads(read("tomm_results/A4_CANONICAL_LINEAGE_AUDIT.json"))
    a5 = json.loads(read("tomm_results/A5_CANONICAL_COMPONENT_ABLATION.json"))
    gp = json.loads(read("tomm_results/GUO_PING_2026_SOURCE_AUDIT.json"))
    hold = json.loads(read("tomm_results/caltech_external_holdout_aggregate.json"))

    assert a3["status"] == "PASS"
    assert a4["status"] == "PASS"
    assert a5["status"] == "PASS" and a5["canonical_reproduction"]["exact_match"] is True
    assert hold["aggregate"]["successes"] == 1163 and hold["aggregate"]["trials"] == 1200
    expected = {"arcis_full":1163, "random_groups":1042, "uniform_group_scheduler":1160, "fixed_mapping":1166, "matched_bucket_baseline":1038}
    for name, n in expected.items():
        assert a5["variants"][name]["successes"] == n
    assert a5["variants"]["fixed_mapping"]["mean_label_emission_cv"] > 5 * a5["variants"]["arcis_full"]["mean_label_emission_cv"]
    assert a5["raw_evidence"]["rows"] == 6000 and len(a5["raw_evidence"]["sha256"]) == 64

    assert gp["status"] == "PRIMARY_SOURCE_REVIEWED"
    assert gp["source"]["doi"] == "10.1016/j.knosys.2026.115472"
    assert (gp["published_parameters"]["N"], gp["published_parameters"]["J"], gp["published_parameters"]["Delta"]) == (18,128,40)
    assert gp["published_parameters"]["datasets"]["Holidays"]["average_robustness_percent"] == 99.54
    assert gp["published_parameters"]["datasets"]["VOC2012"]["average_robustness_percent"] == 98.64
    assert gp["published_parameters"]["datasets"]["ImageNet2012_validation_subset"]["average_robustness_percent"] == 97.19
    assert "10.1016/j.knosys.2026.115472" in bib

    lower = parts.lower()
    assert "mcnemar" not in lower
    assert "five independent" not in lower
    assert "later retraining under a different runtime" not in lower
    assert "diagnostic retraining" not in lower

    for blob, name in [(p00, "abstract"), (cover, "cover letter"), (meta, "ScholarOne metadata")]:
        assert "1,042/1,200" in blob and "1,038/1,200" in blob, f"A5 missing in {name}"

    for blob, name in [(fact,"FACT_CHECK"), (status,"SESSION_STATUS"), (checklist,"SUBMISSION_CHECKLIST"), (dclose,"D1_D7_CLOSURE")]:
        assert SNAPSHOT in blob, f"snapshot missing in {name}"
        assert RUN in blob, f"validation run missing in {name}"

    cite_keys=set()
    for group in re.findall(r"\\cite\{([^}]+)\}", parts):
        cite_keys.update(k.strip() for k in group.split(","))
    bib_keys=set(re.findall(r"@\w+\{([^,]+),", bib))
    missing=sorted(cite_keys-bib_keys)
    assert not missing, f"missing BibTeX keys: {missing}"

    labels=re.findall(r"\\label\{([^}]+)\}", parts)
    assert len(labels) == len(set(labels)), "duplicate LaTeX labels"
    refs=re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", parts)
    missing_refs=sorted(set(refs)-set(labels))
    assert not missing_refs, f"unresolved labels in source: {missing_refs}"

    for i in range(1,8):
        row=dclose.split(f"**D{i}",1)[1].split("\n",1)[0]
        assert "CLOSED" in row, f"D{i} not closed"

    print(json.dumps({
        "gate10_static_verifier":"PASS",
        "title_sync":"PASS",
        "A3":"PASS","A4":"PASS","A5":"PASS",
        "snapshot":SNAPSHOT,"validation_run":RUN,
        "citations":len(cite_keys),"labels":len(labels),"refs":len(refs)
    }, indent=2))

if __name__ == "__main__":
    main()
