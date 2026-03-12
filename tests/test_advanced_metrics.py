import numpy as np
import pandas as pd
from src.advanced_metrics import (
    trapz_manual,
    PhaseComputer,
    detect_column_variants,
    detect_emg_columns,
    detect_cop_columns,
)

def test_trapz_manual_empty():
    assert trapz_manual(np.array([]), 0.1) == 0.0

def test_trapz_manual_linear():
    y = np.array([0, 1, 2, 3], dtype=float)
    # area should be approx 0+3 * length /2 = 4.5 when dx=1
    assert trapz_manual(y, 1.0) == 4.5

def make_df():
    t = np.linspace(0, 1, 11)
    df = pd.DataFrame({'time': t, 'a': t * 1000, 'p': t * 2})
    return df

def test_phasecomputer_slicing_and_stats():
    df = make_df()
    pc = PhaseComputer(df, 'time')
    sl = pc._slice(0.2, 0.5)
    assert isinstance(sl, slice)
    mean, mx, mn = pc.stats('a', None, 0.2, 0.5)
    assert np.isclose(mean, (0.2 + 0.5) / 2 * 1000, atol=1e-6)
    assert mx >= mn

def test_range_and_mean_max_min():
    df = make_df()
    pc = PhaseComputer(df, 'time')
    rng = pc.range_mm_to_m('a', 0.0, 1.0)
    assert rng == (1.0, 0.0, 1.0)
    # data in column 'a' are in mm, mean should reflect that
    assert pc.mean('a', 0.0, 1.0) == 500.0
    # mean, max, min use original units (mm)
    assert pc.max_val('a', 0.0, 1.0) == 1000.0
    assert pc.min_val('a', 0.0, 1.0) == 0.0

def test_power_work_use_power_col():
    df = make_df()
    pc = PhaseComputer(df, 'time')
    meanp, maxp, work = pc.power_work('p', None, None, 0, 1)
    assert np.isclose(meanp, 1.0)
    assert np.isclose(maxp, 2.0)
    assert work >= 0

def test_power_work_approximation():
    df = make_df()
    pc = PhaseComputer(df, 'time')
    meanp, maxp, work = pc.power_work(None, 'p', 1.0, 0, 1)
    assert meanp is not None

def test_detect_column_variants():
    df = pd.DataFrame({'Body Center Of Mass-Z': [1]})
    assert detect_column_variants(df, ['body', 'mass-z']) == 'Body Center Of Mass-Z'
    assert detect_column_variants(df, ['not', 'present']) is None

def test_detect_emg_columns():
    df = pd.DataFrame({'RT TIB.ANT. (%)': [0], 'RT UNKNOWN': [1]})
    assert detect_emg_columns(df) == ['RT TIB.ANT. (%)']

def test_detect_cop_columns_raw_and_sd():
    df = pd.DataFrame({
        'CoP_SD Displ_AP': [0],
        'CoP_Disp_X': [1],
        'CoP_Disp_Y': [2],
        'CoP_Disp_R': [3],
    })
    res = detect_cop_columns(df)
    assert res['CoP_SD Displ_AP'] == 'CoP_SD Displ_AP'
    assert res['raw_AP'] == 'CoP_Disp_X'
    assert res['raw_ML'] == 'CoP_Disp_Y'
    assert res['raw_Result'] == 'CoP_Disp_R'
