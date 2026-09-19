# ARCIS-PERM-RRNS v1 — Focused SOTA Re-audit

Status: **preliminary novelty-scope audit, not an exhaustive priority search**.

This audit was opened after the local-permutation/RRNS design was frozen. It is intended to prevent overclaiming novelty before the fresh experimental campaign is incorporated into a manuscript.

## Directly relevant precedents

1. X. Xiang, Y. Tan, J. Qin, and Y. Tan, “Advancements and challenges in coverless image steganography: A survey,” *Signal Processing*, vol. 228, 109761, 2025, DOI: 10.1016/j.sigpro.2024.109761. This establishes the contemporary mapping-/feature-based CIS landscape and must be used to frame the contribution.

2. B. Guo and P. Ping, “Towards robust and high-capacity coverless image steganography,” *Knowledge-Based Systems*, vol. 338, 115472, 2026, DOI: 10.1016/j.knosys.2026.115472. This is a direct recent capacity/robustness comparator. ARCIS-PERM-RRNS must not claim generic high-capacity or robust CIS as new.

3. “A Coverless Text Steganography by Encoding the Chinese Characters’ Component Structures,” *International Journal of Digital Crime and Forensics*, 2021, DOI: 10.4018/IJDCF.20211101.oa4. This work explicitly uses systems of linear remainder equations and the Chinese Remainder Theorem in a coverless-steganography setting. Therefore **CRT in coverless steganography is not a novelty claim available to this work**.

4. “A multi-image steganography: ISS,” *Cybersecurity*, 2024, DOI: 10.1186/s42400-024-00333-6. ISS uses permutation-coded chromosomes to reorder multiple images, although its permutation is an optimization representation for image merging rather than a local order channel that itself carries message symbols. Therefore **the generic use of permutations in multi-image steganography is not novel by itself**.

5. Q. Liu et al., “Coverless steganography based on image retrieval of DenseNet features and DWT sequence mapping,” *Knowledge-Based Systems*, vol. 192, 105375, 2020, DOI: 10.1016/j.knosys.2019.105375. This is relevant prior art for ordered image transmission and sequence mapping in retrieval-based CIS.

## Novelty boundary currently defensible

The contribution must not be framed as:
- the first use of CRT in coverless steganography;
- the first use of permutations in multi-image steganography;
- the first robust/high-capacity CIS system;
- a claim that CRT creates information beyond the physical channel capacity.

The candidate scientific object to test is narrower: a **local order channel over unchanged cover groups, jointly decoded with the ARCIS label channel, whose composite symbols are protected by a redundant residue-number representation and accepted only after authenticated reconstruction**. The experimentally important question is whether this construction changes the robustness–traffic frontier under an unchanged-image selection channel.

No priority wording (“first”, “novel”, “state of the art”) is frozen at this stage. A broader bibliographic search is still required before submission, including permutation/ordering channels in steganography, permutation codes under channel errors, redundant residue number systems for communication, and recent 2025–2026 CIS methods.
