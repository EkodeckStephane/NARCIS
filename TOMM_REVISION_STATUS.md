# NARCIS — ACM TOMM Final Revision Status

## Target and frozen title

**ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**  
**NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction**

## Status

**SCIENTIFIC CLOSURE COMPLETE — GATE-10 PASS.**

The TOMM manuscript has replaced the historical scaffold. Historical IEEE/Elsevier values are not reused as final evidence unless they belong to the canonical TOMM lineage. BOSSBase is development-only; Caltech-101 is the untouched external validation corpus for the final K=8/group-size-5/RS128 protocol.

## Closed experimental gates

- External calibration: **1,800/1,800** authenticated recoveries.
- External holdout: **1,163/1,200 = 96.92%**.
- Holdout failure localization: all **37 failures** under `crop_12_holdout`; seven other attacks **150/150** each.
- Final selection detectors: SRM-lite **0.504048**, GLCM **0.512833**, CNN **0.526603** mean macro-AUC over 100 repeated image-disjoint splits.
- DiffStega external execution: **100/100** official UniStega cases, 700 PNG outputs, zero evaluation errors, correct-recovery PSNR **23.274 dB** vs. **23.290 dB** published.
- Claim/code/data audit: **PASS**.
- Q1 gates: **1–10 PASS** under the bounded claims in the final manuscript.

## Mandatory wording boundaries

- Use **low but measurable selection leakage/detectability**; never “undetectable.”
- Do not claim universal robustness; preserve the 12% crop boundary.
- Do not call AES-GCM/RS/HMAC/Gray coding novel.
- Do not claim direct numerical superiority over DiffStega because its information object and metrics differ.
- Label DiffStega paper-facing metrics as **independently reproduced**.
- Preserve the two disclosed metric-environment version deviations.

## Final author order

1. Arthur Ulrich Ewane
2. Stéphane Gaël R. Ekodeck
3. Serge Alain Ebélé
4. Vivien Loïck Beyala Kamgang
5. Chantal Marguerite Mveh-Abia — corresponding author

René Ndoundam is not an author of the TOMM version.
