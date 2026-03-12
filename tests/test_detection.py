import numpy as np
from src.detection import compute_vector_displacements, detect_peaks


def test_compute_vector_displacements():
    z = np.array([0, 1, 0, -1, 0])
    v = compute_vector_displacements(z)
    assert v.shape == z.shape
    assert np.all(np.isfinite(v))


def test_detect_peaks_simple():
    z = np.array([0, 1, 0, 1, 0])
    peaks = detect_peaks(z, window=1)
    # function marks peaks with 10000
    assert peaks[1] == 10000
