from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import math
from collections import defaultdict

import numpy as np


@dataclass(frozen=True)
class DistributionMatchedScheduler:
    """Keyed, reliability-aware scheduler with clean-stratum quota matching.

    Stratum proportions are computed conditionally on each clean codebook label.
    Reliability changes the order of covers only inside a stratum; it never
    changes the target stratum mixture. This keeps the scheduling objective
    independent of any steganalyzer output.
    """

    labels: dict[str, int]
    strata: dict[str, int]
    reliability: dict[str, float]
    gamma: float

    @classmethod
    def build(
        cls,
        paths: list[str],
        labels: np.ndarray,
        strata: np.ndarray,
        reliability: np.ndarray,
        gamma: float,
    ) -> "DistributionMatchedScheduler":
        labels = np.asarray(labels)
        strata = np.asarray(strata)
        reliability = np.asarray(reliability, dtype=np.float64)
        if not (len(paths) == len(labels) == len(strata) == len(reliability)):
            raise ValueError("paths, labels, strata, and reliability must align")
        if gamma < 0:
            raise ValueError("gamma must be non-negative")
        if np.any(~np.isfinite(reliability)) or np.any(reliability < 0) or np.any(reliability > 1):
            raise ValueError("reliability must contain finite values in [0, 1]")
        return cls(
            labels={path: int(label) for path, label in zip(paths, labels, strict=True)},
            strata={path: int(stratum) for path, stratum in zip(paths, strata, strict=True)},
            reliability={path: float(value) for path, value in zip(paths, reliability, strict=True)},
            gamma=float(gamma),
        )

    def _race_score(
        self,
        path: str,
        cluster: int,
        selection_key: bytes,
        payload_context: bytes,
    ) -> tuple[float, bytes, str]:
        cluster_bytes = int(cluster).to_bytes(4, "big", signed=False)
        digest = hmac.new(
            selection_key,
            b"candidate:" + payload_context + cluster_bytes + path.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        integer = int.from_bytes(digest[:8], "big")
        uniform = (integer + 1.0) / (2**64 + 1.0)
        weight = (0.05 + self.reliability[path]) ** self.gamma
        score = -math.log(uniform) / max(weight, 1e-18)
        return score, digest, path

    @staticmethod
    def _fair_interleave(
        groups: dict[int, list[str]],
        tie_rank: dict[int, int],
    ) -> list[str]:
        sizes = {stratum: len(paths) for stratum, paths in groups.items()}
        total = sum(sizes.values())
        if total == 0:
            return []
        proportions = {
            stratum: count / total for stratum, count in sizes.items() if count
        }
        used = {stratum: 0 for stratum in proportions}
        cursor = {stratum: 0 for stratum in proportions}
        output: list[str] = []
        for step in range(1, total + 1):
            available = [
                stratum
                for stratum in proportions
                if cursor[stratum] < len(groups[stratum])
            ]
            if not available:
                break
            stratum = max(
                available,
                key=lambda item: (
                    step * proportions[item] - used[item],
                    -tie_rank[item],
                ),
            )
            output.append(groups[stratum][cursor[stratum]])
            cursor[stratum] += 1
            used[stratum] += 1
        return output

    def order(
        self,
        cluster: int,
        candidates: list[str],
        selection_key: bytes,
        payload_context: bytes,
    ) -> list[str]:
        groups: dict[int, list[tuple[float, bytes, str]]] = defaultdict(list)
        for path in candidates:
            if self.labels.get(path) != int(cluster):
                raise ValueError("candidate label does not match requested cluster")
            stratum = self.strata[path]
            groups[stratum].append(
                self._race_score(path, cluster, selection_key, payload_context)
            )

        ordered_groups: dict[int, list[str]] = {}
        tie_rank: dict[int, int] = {}
        cluster_bytes = int(cluster).to_bytes(4, "big", signed=False)
        for stratum, rows in groups.items():
            rows.sort(key=lambda row: (row[0], row[1], row[2]))
            ordered_groups[stratum] = [path for _, _, path in rows]
            digest = hmac.new(
                selection_key,
                b"stratum:"
                + payload_context
                + cluster_bytes
                + int(stratum).to_bytes(4, "big", signed=False),
                hashlib.sha256,
            ).digest()
            tie_rank[stratum] = int.from_bytes(digest[:8], "big")

        return self._fair_interleave(ordered_groups, tie_rank)
