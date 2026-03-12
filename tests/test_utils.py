import numpy as np
from src.utils import centered_slope, cumulative_trapezoid, detect_column


def test_centered_slope_linear():
    x = np.linspace(0, 10, 11)
    dy = centered_slope(x, dt=1.0, half_window=1)
    # slope constant 1.0 except edges
    assert np.allclose(dy[1:-1], 1.0)


def test_cumulative_trapezoid_simple():
    y = np.array([0, 1, 2, 3])
    # manual trapezoid: 0.5+1.5+2.5 = 4.5
    assert np.isclose(cumulative_trapezoid(y, dx=1.0)[-1], 4.5)


def test_detect_column():
    import pandas as pd
    df = pd.DataFrame({"Disp_BCM_Z": [1,2,3], "other": [4,5,6]})
    assert detect_column(df, candidates=['Disp_BCM_Z'], contains_all=[]) == 'Disp_BCM_Z'
