import numpy as np
import pandas as pd
import pytest

from src.analysis import trapz_manual, PhaseComputer, generate_phase_dataframe
from src.detection import RepEvents


class TestTrapzManual:
    """Test trapz_manual integration function."""

    def test_empty_array(self):
        assert trapz_manual(np.array([]), 0.1) == 0.0

    def test_single_element(self):
        assert trapz_manual(np.array([5.0]), 0.1) == 0.0

    def test_linear_ramp(self):
        # integral of line y=2*x from x=0 to x=1 with 11 points
        y = np.linspace(0, 2, 11)
        result = trapz_manual(y, 0.1)
        # exact integral: 2*1^2/2 = 1.0
        assert np.isclose(result, 1.0, atol=0.01)

    def test_constant(self):
        y = np.array([5.0, 5.0, 5.0, 5.0])
        result = trapz_manual(y, 0.5)
        # area = 5 * 1.5 = 7.5
        assert np.isclose(result, 7.5)

    def test_with_nans(self):
        y = np.array([1.0, 2.0, np.nan, 3.0, 4.0])
        result = trapz_manual(y, 1.0)
        # should skip nan segment
        assert np.isfinite(result)


class TestPhaseComputerInit:
    """Test PhaseComputer initialization and slicing."""

    def make_df(self):
        t = np.linspace(0, 10, 101)
        df = pd.DataFrame({
            'time': t,
            'bcm_z': np.sin(t),
            'velocity': np.cos(t),
            'power': np.sin(t)**2
        })
        return df

    def test_init(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        assert pc.df is df
        assert len(pc.time) == len(df)
        assert np.isclose(pc.dt, 0.1, atol=0.01)

    def test_slice_basic(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        sl = pc._slice(2.0, 5.0)
        assert isinstance(sl, slice)
        # slice should include indices for t≈2 to t≈5
        assert sl.start >= 0 and sl.stop <= len(df)

    def test_slice_reversed_times(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        sl1 = pc._slice(2.0, 5.0)
        sl2 = pc._slice(5.0, 2.0)  # reversed
        # should be handled gracefully
        assert sl1.start >= 0 and sl2.start >= 0


class TestPhaseComputerMetrics:
    """Test metric computation methods."""

    def make_df(self):
        t = np.linspace(0, 10, 101)
        df = pd.DataFrame({
            'time': t,
            'bcm_z_mm': np.sin(t) * 100,  # mm scale
            'velocity_m_s': np.abs(np.cos(t)),
            'power_w': np.sin(t)**2 * 50
        })
        return df

    def test_range_mm_to_m(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        # test valid range
        mx, mn, rg = pc.range_mm_to_m('bcm_z_mm', 0, 5)
        assert mx is not None and mn is not None
        assert rg is not None
        # range should be max - min
        assert np.isclose(rg, mx - mn)

    def test_range_missing_column(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        mx, mn, rg = pc.range_mm_to_m('nonexistent', 0, 5)
        assert (mx, mn, rg) == (None, None, None)

    def test_stats_from_column(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        mean, mx, mn = pc.stats('velocity_m_s', None, 0, 5)
        assert mean is not None and mx is not None and mn is not None
        assert mn <= mean <= mx

    def test_stats_from_array(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        arr = np.array([1, 2, 3, 4, 5], dtype=float)
        mean, mx, mn = pc.stats(None, arr, 0, 1)
        assert mean == 3.0
        assert mx == 5.0
        assert mn == 1.0

    def test_mean_valid_column(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        val = pc.mean('velocity_m_s', 2, 5)
        assert val is not None
        assert 0 <= val <= 1  # cos values

    def test_mean_missing_column(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        val = pc.mean('missing', 0, 5)
        assert val is None

    def test_stdev(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        std = pc.stdev('velocity_m_s', 0, 10)
        assert std is not None
        assert std > 0

    def test_power_work_from_column(self):
        df = self.make_df()
        pc = PhaseComputer(df, 'time')
        mean_p, max_p, work = pc.power_work('power_w', None, None, 0, 5)
        assert mean_p is not None and max_p is not None
        assert work >= 0  # work should be non-negative


class TestGeneratePhaseDataframe:
    """Test generate_phase_dataframe function."""

    def make_test_data(self):
        # create minimal test dataframe
        n = 101
        t = np.linspace(0, 10, n)
        df = pd.DataFrame({
            'time': t,
            'Body Center of Mass-Z (mm)': np.sin(t) * 100,
            'velocity (m/s)': np.cos(t),
            'acceleration (m/s2)': -np.sin(t),
            'power (W)': np.abs(np.sin(t)) * 100,
        })
        return df, t, np.sin(t) * 100, np.cos(t), -np.sin(t), np.abs(np.sin(t)) * 100

    def test_empty_rep_events(self):
        df, t, z, v, a, p = self.make_test_data()
        marker_to_time = {}
        rep_events = []
        
        result = generate_phase_dataframe(
            df, 'time', rep_events, marker_to_time,
            z, v, a, p, mass_kg=75.0, dt=0.1, half_window_derivative=3
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_repetition(self):
        df, t, z, v, a, p = self.make_test_data()
        
        # create a simple rep event
        rep_ev = RepEvents(rep=1, start_idx=10, peak_idx=30, ecc_end_idx=60)
        marker_to_time = {1: 1.0, 2: 3.0, 3: 6.0, 4: 7.0}
        
        result = generate_phase_dataframe(
            df, 'time', [rep_ev], marker_to_time,
            z, v, a, p, mass_kg=75.0, dt=0.1, half_window_derivative=3
        )
        
        assert isinstance(result, pd.DataFrame)
        # should have columns for repetition, phase, times, etc
        assert 'Repeticion' in result.columns
        assert 'Fase' in result.columns
        assert 'Tiempo fase' in result.columns

    def test_bcm_z_metrics_present(self):
        df, t, z, v, a, p = self.make_test_data()
        rep_ev = RepEvents(rep=1, start_idx=10, peak_idx=30, ecc_end_idx=60)
        marker_to_time = {1: 1.0, 2: 3.0, 3: 6.0, 4: 7.0}
        
        result = generate_phase_dataframe(
            df, 'time', [rep_ev], marker_to_time,
            z, v, a, p, mass_kg=75.0, dt=0.1, half_window_derivative=3
        )
        
        # check BCM Z columns are present
        expected_cols = [
            'BCM_Z_Max (m)', 'BCM_Z_Min (m)', 'BCM_Z_Range (m)',
            'BCM_Z_Vel_Mean (m/s)', 'BCM_Z_Vel_Max (m/s)', 'BCM_Z_Vel_Min (m/s)',
            'BCM_Z_Power_Mean (W)', 'BCM_Z_Power_Max (W)', 'BCM_Z_Work (J)'
        ]
        for col in expected_cols:
            assert col in result.columns
