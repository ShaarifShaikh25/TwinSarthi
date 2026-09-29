import unittest
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

from causal_analysis.signal_contribution import analyze_event_signals, COMPOSITE_SIGNALS

class TestSignalContribution(unittest.TestCase):
    def setUp(self):
        self.medians = pd.Series({
            'load_adjusted_fuel_deviation': 0.0,
            'fuel_efficiency_proxy': 1.0,
            'exhaust_temp_dev_c': 0.0,
            'exhaust_temp_rate_c_per_min': 0.0,
            'vibration_trend': 0.0,
            'vibration_mm_s': 2.0,
            'load_pct': 90.0,
            'rpm': 1500.0,
            'coolant_temp_c': 85.0,
            'oil_pressure_bar': 4.0
        })
        self.mad = pd.Series({
            'load_adjusted_fuel_deviation': 1.0,
            'fuel_efficiency_proxy': 0.05,
            'exhaust_temp_dev_c': 2.0,
            'exhaust_temp_rate_c_per_min': 1.0,
            'vibration_trend': 0.1,
            'vibration_mm_s': 0.2,
            'load_pct': 0.0, # Will trigger MAD floor
            'rpm': 5.0,
            'coolant_temp_c': 1.0,
            'oil_pressure_bar': 0.1
        })
        
    def test_1_normal_signal(self):
        # Normal signal below threshold -> NOT_EVIDENCE_POSITIVE
        df = pd.DataFrame({
            'load_adjusted_fuel_deviation': [0.5, 0.2, -0.5], # Deviation < 2.0
            'data_quality_warning': [False]*3
        })
        res = analyze_event_signals(df, self.medians, self.mad)
        s = next(x for x in res['signals'] if x['signal'] == 'load_adjusted_fuel_deviation')
        self.assertEqual(s['evidence_status'], 'NOT_EVIDENCE_POSITIVE')

    def test_2_above_threshold(self):
        # Signal above threshold -> EVIDENCE_POSITIVE
        df = pd.DataFrame({
            'load_adjusted_fuel_deviation': [2.5, 3.0, 2.1], # Deviation > 2.0
            'data_quality_warning': [False]*3
        })
        res = analyze_event_signals(df, self.medians, self.mad)
        s = next(x for x in res['signals'] if x['signal'] == 'load_adjusted_fuel_deviation')
        self.assertEqual(s['evidence_status'], 'EVIDENCE_POSITIVE')
        
    def test_3_large_deviation_strength(self):
        # Large deviation -> higher evidence strength
        df1 = pd.DataFrame({'load_adjusted_fuel_deviation': [2.5, 3.0], 'data_quality_warning': [False]*2})
        df2 = pd.DataFrame({'load_adjusted_fuel_deviation': [8.0, 9.0], 'data_quality_warning': [False]*2})
        res1 = analyze_event_signals(df1, self.medians, self.mad)
        res2 = analyze_event_signals(df2, self.medians, self.mad)
        s1 = next(x for x in res1['signals'] if x['signal'] == 'load_adjusted_fuel_deviation')
        s2 = next(x for x in res2['signals'] if x['signal'] == 'load_adjusted_fuel_deviation')
        self.assertGreater(s2['evidence_strength'], s1['evidence_strength'])

    def test_4_missing_signal(self):
        # Missing signal -> unavailable, not zero
        df = pd.DataFrame({
            'load_adjusted_fuel_deviation': [2.5, 3.0],
            'data_quality_warning': [False]*2
        }) # fuel_efficiency_proxy is missing entirely
        res = analyze_event_signals(df, self.medians, self.mad)
        s = next(x for x in res['signals'] if x['signal'] == 'fuel_efficiency_proxy')
        self.assertFalse(s['available'])
        self.assertEqual(s['evidence_status'], 'UNAVAILABLE')
        self.assertTrue('mean_deviation' not in s)

    def test_5_zero_mad(self):
        # Zero MAD -> no division-by-zero failure
        df = pd.DataFrame({
            'load_pct': [95.0, 95.0], # baseline median is 90, MAD is 0
            'data_quality_warning': [False]*2
        })
        res = analyze_event_signals(df, self.medians, self.mad)
        s = next(x for x in res['signals'] if x['signal'] == 'load_pct')
        self.assertTrue(s['available'])
        self.assertFalse(np.isnan(s['mean_deviation']))
        
    def test_6_communication_gap(self):
        # Communication gap sample -> no mechanical evidence
        df = pd.DataFrame({
            'load_adjusted_fuel_deviation': [10.0, 10.0],
            'data_quality_warning': [True, True]
        })
        res = analyze_event_signals(df, self.medians, self.mad)
        self.assertEqual(res['event_status'], 'INSUFFICIENT_TELEMETRY')
        
    def test_7_composite_feature(self):
        # Composite feature -> does not independently increase evidence
        df = pd.DataFrame({
            'combustion_signature_proxy': [10.0, 10.0],
            'data_quality_warning': [False]*2
        })
        res = analyze_event_signals(df, self.medians, self.mad)
        signals = [x['signal'] for x in res['signals']]
        self.assertNotIn('combustion_signature_proxy', signals)
        
    def test_8_deterministic(self):
        # Deterministic output
        df = pd.DataFrame({
            'load_adjusted_fuel_deviation': [2.5, 3.0],
            'data_quality_warning': [False]*2
        })
        res1 = analyze_event_signals(df, self.medians, self.mad)
        res2 = analyze_event_signals(df, self.medians, self.mad)
        self.assertEqual(json.dumps(res1), json.dumps(res2))

def run_controlled_example():
    medians = pd.Series({
        'load_adjusted_fuel_deviation': 0.0,
        'exhaust_temp_dev_c': 0.0,
        'vibration_trend': 0.0,
        'coolant_temp_c': 85.0
    })
    mad = pd.Series({
        'load_adjusted_fuel_deviation': 1.0,
        'exhaust_temp_dev_c': 2.0,
        'vibration_trend': 0.1,
        'coolant_temp_c': 1.0
    })
    
    # One normal signal (coolant), one strong fuel deviation, one thermal deviation, 
    # one mechanical deviation, one missing value (fuel_efficiency_proxy), 
    # data_quality_warning = False.
    df = pd.DataFrame({
        'load_adjusted_fuel_deviation': [4.0, 4.5, 4.2],  # MAD=4+
        'exhaust_temp_dev_c': [5.0, 6.0, 5.5],             # MAD=2.5+
        'vibration_trend': [0.4, 0.45, 0.42],              # MAD=4+
        'coolant_temp_c': [85.5, 85.2, 86.0],              # MAD<1 (Normal)
        'data_quality_warning': [False, False, False]
    })
    
    res = analyze_event_signals(df, medians, mad)
    print("\n" + "="*50)
    print("CONTROLLED EXAMPLE RESULTS")
    print("="*50)
    print(json.dumps(res, indent=2))
    
    # One communication-gap case
    df_gap = pd.DataFrame({
        'load_adjusted_fuel_deviation': [4.0, 4.5, 4.2],
        'data_quality_warning': [True, True, True]
    })
    res_gap = analyze_event_signals(df_gap, medians, mad)
    print("\n" + "="*50)
    print("COMMUNICATION GAP EXAMPLE RESULTS")
    print("="*50)
    print(json.dumps(res_gap, indent=2))

if __name__ == '__main__':
    print("Running Unit Tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    run_controlled_example()
