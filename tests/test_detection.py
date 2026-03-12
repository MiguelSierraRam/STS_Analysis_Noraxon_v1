import numpy as np
from src.detection import (
    compute_vector_displacements,
    compute_windows,
    detect_peaks,
    detect_conc_starts,
    detect_ecc_ends,
    pair_repetitions,
    compute_phase_events,
    compute_acc_phases,
)


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


def test_window_and_detect_functions():
    z = np.array([0, 1, 2, 1, 0])
    v = compute_vector_displacements(z)
    future, prev = compute_windows(v, window=2)
    assert future.shape == v.shape and prev.shape == v.shape

    # test conc_start detection
    vel_flag = np.array([1, 1, np.nan, 1, 1])
    conc = detect_conc_starts(future, vel_flag, n_positive=1)
    assert conc[0] == 10000 or conc[1] == 10000

    # test ecc end detection
    ecc = detect_ecc_ends(prev, vel_flag, n_positive=1)
    assert ecc.dtype == int

    # pair reps simple
    reps, pid, plabel = pair_repetitions([0], [1], [3], n=5)
    assert reps == [(0, 1, 3)]
    assert pid[0] == 1 or pid[3] == 2

    # phase event graphs
    peaks = detect_peaks(z, window=1)
    conc_ev, conc_g, ecc_ev, ecc_g, any_ev = compute_phase_events(conc, peaks, ecc)
    assert conc_ev.shape == z.shape

    # acc phases
    start = np.zeros(5, dtype=int); start[0] = 10000
    peak = np.zeros(5, dtype=int); peak[1] = 10000
    end = np.zeros(5, dtype=int); end[3] = 10000
    t = np.arange(5, dtype=float)
    acc, m2t, rep_events = compute_acc_phases(start, peak, end, t)
    assert acc.max() > 0
    assert isinstance(m2t, dict)
    assert rep_events and rep_events[0].start_idx == 0

