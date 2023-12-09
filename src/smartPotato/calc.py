import numpy as np


def vecDiff(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calculates the difference between two vectors.

    Args:
        a: The first vector.
        b: The second vector.

    Returns:
        The difference between the two vectors.
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
