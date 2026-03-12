import numpy as np
from src.metrics import compute_metrics, RepResult


def test_compute_metrics_basic():
    # simple rep with start at 0, peak at 2, end at 4
    z = np.linspace(0, 10, 5)
    vel = np.gradient(z)
    acc = np.gradient(vel)
    power = vel * acc
    t = np.linspace(0, 4, 5)
    dt = 1.0
    n = len(z)
    rep = compute_metrics(1, 0, 2, 4, 5, n, z, vel, acc, power, t, dt)
    assert isinstance(rep, RepResult)
    assert rep.amp_up_mm == z[2] - z[0]
