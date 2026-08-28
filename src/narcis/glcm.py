import numpy as np


DIRECTIONS = ((0, 1), (-1, 1), (-1, 0), (-1, -1))
TEXTURE_WEIGHTS = np.asarray(
    [7.0 / 60.0, 11.0 / 20.0, 1.0 / 5.0, 2.0 / 15.0],
    dtype=np.float64,
)


def _to_gray(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image, dtype=np.float64)
    if array.ndim == 3:
        if array.shape[0] in {1, 3}:
            array = array.mean(axis=0)
        elif array.shape[-1] in {1, 3}:
            array = array.mean(axis=-1)
        else:
            raise ValueError("unsupported three-dimensional image layout")
    if array.ndim != 2:
        raise ValueError("image must be two-dimensional after grayscale conversion")
    if array.size == 0:
        raise ValueError("image must not be empty")
    minimum = float(array.min())
    maximum = float(array.max())
    if minimum < 0.0 or maximum > 1.0:
        if minimum >= 0.0 and maximum <= 255.0:
            array = array / 255.0
        else:
            span = maximum - minimum
            array = np.zeros_like(array) if span <= 1e-12 else (array - minimum) / span
    return np.clip(array, 0.0, 1.0)


def _quantize(image: np.ndarray, levels: int) -> np.ndarray:
    if levels < 2:
        raise ValueError("levels must be at least two")
    scaled = np.floor(_to_gray(image) * levels).astype(np.int64)
    return np.clip(scaled, 0, levels - 1)


def _paired_views(
    quantized: np.ndarray, dy: int, dx: int, distance: int
) -> tuple[np.ndarray, np.ndarray]:
    if distance < 1:
        raise ValueError("distance must be positive")
    sy = dy * distance
    sx = dx * distance
    height, width = quantized.shape
    if abs(sy) >= height or abs(sx) >= width:
        raise ValueError("distance exceeds image dimensions")

    y1_start = max(0, -sy)
    y1_end = min(height, height - sy)
    x1_start = max(0, -sx)
    x1_end = min(width, width - sx)
    first = quantized[y1_start:y1_end, x1_start:x1_end]
    second = quantized[
        y1_start + sy : y1_end + sy,
        x1_start + sx : x1_end + sx,
    ]
    return first, second


def glcm_matrix(
    image: np.ndarray,
    direction: tuple[int, int],
    levels: int = 16,
    distance: int = 1,
    symmetric: bool = True,
) -> np.ndarray:
    quantized = _quantize(image, levels)
    first, second = _paired_views(quantized, *direction, distance)
    matrix = np.zeros((levels, levels), dtype=np.float64)
    np.add.at(matrix, (first.ravel(), second.ravel()), 1.0)
    if symmetric:
        matrix += matrix.T
    total = float(matrix.sum())
    if total <= 0.0:
        raise ValueError("GLCM contains no pixel pairs")
    return matrix / total


def _contribution_matrices(matrix: np.ndarray) -> tuple[np.ndarray, ...]:
    levels = matrix.shape[0]
    i = np.arange(levels, dtype=np.float64)[:, None]
    j = np.arange(levels, dtype=np.float64)[None, :]

    energy = np.square(matrix)
    contrast = np.square(i - j) * matrix
    entropy = np.zeros_like(matrix)
    positive = matrix > 0.0
    entropy[positive] = -matrix[positive] * np.log2(matrix[positive])

    row = matrix.sum(axis=1)
    col = matrix.sum(axis=0)
    mu_i = float(np.sum(np.arange(levels) * row))
    mu_j = float(np.sum(np.arange(levels) * col))
    sigma_i = float(
        np.sqrt(np.sum(np.square(np.arange(levels) - mu_i) * row))
    )
    sigma_j = float(
        np.sqrt(np.sum(np.square(np.arange(levels) - mu_j) * col))
    )
    denominator = sigma_i * sigma_j
    if denominator <= 1e-12:
        correlation = np.zeros_like(matrix)
    else:
        correlation = ((i - mu_i) * (j - mu_j) / denominator) * matrix
    return energy, contrast, entropy, correlation


def _direction_fusion(contributions: list[np.ndarray]) -> float:
    stack = np.stack(contributions, axis=0)
    mean = stack.mean(axis=0)
    norms = np.linalg.norm(stack - mean[None, :, :], axis=(1, 2))
    norm_sum = float(norms.sum())
    if norm_sum <= 1e-12:
        directional_weights = np.full(len(contributions), 1.0 / len(contributions))
    else:
        directional_weights = norms / norm_sum
    values = np.asarray([matrix.sum() for matrix in contributions])
    return float(np.dot(directional_weights, values))


def glcm_texture_features(
    image: np.ndarray,
    levels: int = 16,
    distance: int = 1,
) -> np.ndarray:
    """Return fused [energy, contrast, entropy, correlation, complexity].

    The implementation follows the four-direction GLCM construction and the
    published feature weights of Cao, Wang, and Zhang (Cybersecurity, 2025,
    DOI 10.1186/s42400-025-00423-z). Directional weights are derived from the
    Frobenius (2-) norm of each per-feature contribution matrix relative to
    the four-direction mean contribution matrix, matching the paper's matrix
    fusion description.
    """
    per_feature: list[list[np.ndarray]] = [[], [], [], []]
    for direction in DIRECTIONS:
        matrix = glcm_matrix(
            image,
            direction,
            levels=levels,
            distance=distance,
            symmetric=True,
        )
        contributions = _contribution_matrices(matrix)
        for index, contribution in enumerate(contributions):
            per_feature[index].append(contribution)

    fused = np.asarray(
        [_direction_fusion(contributions) for contributions in per_feature],
        dtype=np.float64,
    )
    complexity = float(np.dot(TEXTURE_WEIGHTS, fused))
    return np.concatenate([fused, np.asarray([complexity])])


def glcm_texture_complexity(
    image: np.ndarray,
    levels: int = 16,
    distance: int = 1,
) -> float:
    return float(glcm_texture_features(image, levels, distance)[-1])
