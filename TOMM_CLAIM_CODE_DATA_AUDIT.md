# NARCIS — Final Claim / Code / Data Audit for ACM TOMM

Canonical title: **NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction**

Canonical author order: Arthur Ulrich Ewane; Stéphane Gaël R. Ekodeck; Serge Alain Ebélé; Vivien Loïck Beyala Kamgang; Chantal Marguerite Mveh-Abia (corresponding author).

## Audit rule

Every central manuscript statement is classified as **demonstrated**, **bounded by evidence**, **specified but not empirically demonstrated**, or **excluded from the final claim set**. Historical IEEE/Elsevier numbers are not promoted into the TOMM article when they do not belong to the canonical K=8/group-bank execution lineage.

## Promise-to-evidence matrix

| Manuscript promise | Status | Code / mechanism | Persisted evidence | Final wording boundary |
|---|---|---|---|---|
| Sender communicates by selecting unchanged natural images from a shared index | Demonstrated | `src/narcis/protocol.py`, `src/narcis/group_bank_protocol.py` return identifiers from the index; no pixel write operation occurs | canonical schedules and index manifests | “unchanged selected covers”; not “information-theoretically invisible” |
| Protected byte strings are authenticated and confidential under the declared symmetric-key model | Demonstrated at implementation/protocol level | AES-GCM in `src/narcis/security.py` and deterministic reproducible benchmark workload in `src/narcis/benchmark.py` | authenticated plaintext recovery is the success criterion in channel campaign | Security is inherited from AES-GCM under secret keys and nonce uniqueness; NARCIS does not claim a new primitive/proof |
| Nonces are unique within each frozen benchmark key domain | Demonstrated | 32-bit derived prefix + 64-bit globally unique sequence; explicit collision check | sequences 0..29 for each partition | Benchmark derivation is for reproducibility, not production key management |
| Replay/out-of-order sessions can be rejected | Implemented | `ReplayGuard` stores highest accepted sequence per sender | unit-test/code path | Stateful replay rejection is claimed; distributed persistence/crash recovery is outside scope |
| Canonical mapping balances a fixed Gray symbol across any K consecutive sessions | Demonstrated analytically and by code construction | `keyed_permutation()` and `TOMM_BALANCED_SESSION_MAPPING_FREEZE.md` | K=8 sequences 0..29 | Exact mapping property only; this is not a proof of detector indistinguishability |
| Error correction tolerates substantial symbol errors | Demonstrated under evaluated channel | RSCodec with parity=128 plus group majority | calibration/holdout correction counts | Observed maximum successful correction count is reported; no universal channel bound beyond RS semantics |
| External calibration generalizes across five Caltech-101 partitions | Demonstrated | canonical K=8 group-bank protocol | `tomm_results/caltech_external_calibration_aggregate.json`: 1800/1800 | Bounded to declared calibration attacks and partitions |
| External holdout robustness remains high under unseen transformations | Demonstrated, bounded | same frozen schedule and holdout-only attacks | `tomm_results/caltech_external_holdout_summary.json`: 1163/1200 = 96.92% | Seven attacks are 150/150; 12% crop is 113/150 and all 37 failures occur there; no universal robustness claim |
| Selection leakage is low under multiple detector families | Demonstrated, bounded | image-disjoint multi-session detector audit | `tomm_results/final_detector_summary.json` | SRM-lite 0.5040, GLCM 0.5128, CNN 0.5266 mean macro-AUC. Use “low detectability / weak measurable signal”, never “undetectable” |
| CNN detector result is stable across partition seeds | Demonstrated descriptively | 5 seeds × 20 image-disjoint repeated splits, 30 heads | workflow run 33987707681; 100 macro-AUCs; 3000 head AUC rows | Descriptive mean/SD/range only; no naive repeated-split one-sample t-test p-value |
| BOSSBase establishes the final method without external tuning | Development evidence only | development campaigns | `tomm_results/bossbase_final_v2_development.json` | K/grouping choices were inspected on BOSSBase; therefore Caltech-101, not BOSSBase, carries the external-validation claim |
| DiffStega was faithfully executed | Demonstrated | external repo frozen at `73cd7cb...`, official UniStega commands, frozen CUDA environment | `tomm_results/diffstega_reproduction_summary.json`; 100/100 cases, 700 outputs, exit 0 | DiffStega execution is reproduced; perceptual metrics are independently implemented because upstream provides no evaluator |
| DiffStega perceptual metrics exactly reproduce IJCAI tables | Not claimed | independent evaluator | PSNR closely matches, other metrics differ | Report published and independently reproduced values separately |
| Independent DiffStega metric environment exactly equals the predeclared package lock | Contradicted by evidence and disclosed | metric runner | observed `huggingface-hub=0.36.2` vs 0.20.3 and `pyiqa=0.1.15` vs 0.1.13 | The deviation is isolated to post-execution metrics; NIQE/SSIM/LPIPS are not used to assert superiority |
| NARCIS numerically outperforms DiffStega on capacity/reconstruction quality | Excluded | different communication objects | comparison protocol | No cross-family “outperforms” claim; NARCIS finite-index byte signaling and DiffStega image reconstruction are not commensurate |
| Universal steganalysis resistance | Excluded | — | CNN AUC above chance directly rules out such language | Never use “undetectable”, “steganalysis-proof”, or universal resistance |
| Universal robustness to geometric transforms | Excluded | — | crop_12 holdout failures | Explicit crop boundary retained in abstract/results/limitations |
| Production key provisioning, rotation, compromise recovery | Not demonstrated | benchmark keys intentionally deterministic/public for reproducibility | code comments and benchmark module | Outside experimental claim set; production deployment requires an external key-management layer |
| Real-time deployment performance | Not demonstrated | — | no matched production latency campaign | No real-time/low-latency claim |

## Code-to-data lineage

The canonical channel and detector executions share the same machine-independent cover identifiers (`relative_path_from_dataset_root.as_posix()`), five Caltech-101 seeds, 1,500 representation-training images and 7,000 disjoint index images per partition, K=8 quantile codebooks, 16 principal plus 32 deterministic random projection candidates, group size five, 10 group-bank restarts, 6,000 swaps/restart, RS parity 128, 30 sessions and global sequences 0..29. The detector target is a 7000×30 binary session-membership matrix. No detector outcome is an optimization input to NARCIS.

The final detector protocol uses 20 image-disjoint 65/35 splits per partition. SRM-lite uses 52 residual features with balanced multi-output ExtraTrees; GLCM uses five texture features with standardized balanced logistic regression per head; CNN uses the frozen 30-head 64×64 architecture for eight epochs. The hierarchy SRM < GLCM < CNN is therefore an observed sensitivity result under one frozen threat model, not an outcome-tuned comparison.

## DiffStega closure

The uploaded evidence bundle has SHA-256 `32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`. Preflight records the exact upstream commit, no tracked source changes, Python 3.11.5, PyTorch 2.1.0+cu121, CUDA availability on a Tesla T4, all required models/assets, and all 100 UniStega cases. Similar/content/style completed with 210/294/196 PNG outputs respectively (700 total). The independent metric evaluator consumed all 100 cases with zero evaluation errors and zero face-detection failures among 22 face cases.

Correct-password recovery PSNR is 23.274 dB versus 23.290 dB reported by IJCAI 2024, providing a useful external sanity check. SSIM, LPIPS, and NIQE show larger implementation-sensitive differences and are therefore labelled independently reproduced values rather than exact table replications.

## Final Q1 scientific gates

1. **Scientific object before artifact description — PASS.** The article is organized around authenticated cover-selection signaling, robustness, finite-index scheduling, and detectability rather than around repository components.
2. **Claim/evidence alignment — PASS.** Every headline number maps to persisted JSON/evidence; adverse crop and CNN results are retained.
3. **Final scientific narrative — PASS.** Historical submission chronology and exploratory phase labels are excluded from the manuscript.
4. **Novelty and related work — PASS.** Positioning separates selection-based finite-index signaling from diffusion-generation CIS and recent stability/restoration/hash approaches; recent ACM TOMM work is cited.
5. **Experimental validity — PASS.** Method-development and external-validation datasets are separated; projection/group banks use calibration attacks only; eight holdout attacks remain evaluation-only; detector splits are image-disjoint and outcome-frozen.
6. **Article structure and prose — PASS subject to successful ACM CI compilation.** The definitive manuscript replaces the placeholder scaffold.
7. **Scope and operational claims — PASS.** Universal robustness, undetectability, production KMS, and real-time claims are explicitly excluded.
8. **Reproducibility — PASS WITH DISCLOSED EXCEPTION.** Dataset hashes, seeds, commits, model revisions, schedules, scripts and result hashes are recorded. The two independently evaluated DiffStega metric-package version deviations are preserved as an audit exception rather than rewritten post hoc.
9. **Bibliographic/editorial hygiene — PASS.** TOMM-specific and 2024–2026 CIS/steganalysis references are included; externally reported results are labelled as such.
10. **Submission readiness — PENDING ONLY FINAL CI COMPILE at the time of this audit record.** Gate 10 becomes PASS only when the definitive ACM manuscript compiles and repository tests/preflight remain green after the final edits.

## Senior-reviewer prescreen verdict before final CI

**Scientific verdict: Minor-revision level / potentially publishable, not reject-on-evidence.** The strongest residual reviewer objection is the visible 12% crop boundary and the weak but measurable CNN selection signal; both are reported transparently and delimit the claims. The previous critical gaps — fresh external holdout, repeated residual/texture/CNN threat model, executable recent comparator, and claim/code/data traceability — are now closed.
