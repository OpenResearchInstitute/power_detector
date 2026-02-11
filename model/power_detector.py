"""
Python model of power_detector.vhd — Signal power measurement.

RTL architecture:
  - Computes I^2, Q^2 as unsigned (2*DATA_W-1 bits)
  - Selects: IQ_MOD -> I^2+Q^2, I_USED -> I^2, else Q^2
  - Passes through one or two cascaded LowpassEma filters
  - data_ena is delayed 2 clocks before feeding first EMA

Pipeline:
  clk 1: di_sq, dq_sq computed; dsum_e1 <= data_ena
  clk 2: dsum selected; dsum_e2 <= dsum_e1
  Then EMA filters process dsum with dsum_e2 as enable
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from model_utils import signed, unsigned
from lowpass_ema.model.lowpass_ema import LowpassEma


class PowerDetector:
    def __init__(self, data_w=12, alpha_w=18, iq_mod=False,
                 i_used=True, q_used=False, ema_cascade=True, fixed_point=False):
        self.DATA_W = data_w
        self.ALPHA_W = alpha_w
        self.IQ_MOD = iq_mod
        self.I_USED = i_used
        self.Q_USED = q_used
        self.EMA_CASCADE = ema_cascade
        self.fixed_point = fixed_point

        self.OUT_W = 2 * data_w - 1

        if fixed_point:
            self.ema_1 = LowpassEma(alpha_w=alpha_w, data_w=self.OUT_W, fixed_point=True)
            if ema_cascade:
                self.ema_2 = LowpassEma(alpha_w=alpha_w, data_w=self.OUT_W, fixed_point=True)

        self.reset()

    def reset(self):
        if self.fixed_point:
            self.di_sq = 0
            self.dq_sq = 0
            self.dsum = 0
            self.dsum_e1 = 0
            self.dsum_e2 = 0
            self.ema_1.reset()
            if self.EMA_CASCADE:
                self.ema_2.reset()
        else:
            self.power = 0.0

    def step(self, data_I, data_Q, data_ena, alpha1, alpha2=0):
        """One clock cycle. Returns dict(power_squared)."""
        if not self.fixed_point:
            return self._step_float(data_I, data_Q, data_ena, alpha1, alpha2)
        else:
            return self._step_fixed(data_I, data_Q, data_ena, alpha1, alpha2)

    def _step_float(self, data_I, data_Q, data_ena, alpha1, alpha2):
        if self.IQ_MOD:
            self.power = data_I * data_I + data_Q * data_Q
        elif self.I_USED:
            self.power = data_I * data_I
        else:
            self.power = data_Q * data_Q
        return {'power_squared': self.power}

    def _step_fixed(self, data_I, data_Q, data_ena, alpha1, alpha2):
        DW = self.DATA_W
        OW = self.OUT_W

        # Pipeline stage 1: square and delay enable
        prev_dsum_e1 = self.dsum_e1
        prev_dsum_e2 = self.dsum_e2

        # di_sq <= resize(unsigned(signed(data_I) * signed(data_I)), 2*DATA_W-1)
        i_val = signed(data_I, DW)
        q_val = signed(data_Q, DW)
        new_di_sq = unsigned(i_val * i_val, OW)
        new_dq_sq = unsigned(q_val * q_val, OW)

        self.dsum_e1 = data_ena
        self.dsum_e2 = prev_dsum_e1

        if self.IQ_MOD:
            new_dsum = unsigned(self.di_sq + self.dq_sq, OW)
        elif self.I_USED:
            new_dsum = unsigned(self.di_sq, OW)
        else:
            new_dsum = unsigned(self.dq_sq, OW)

        # Update registers
        self.di_sq = new_di_sq
        self.dq_sq = new_dq_sq
        self.dsum = new_dsum

        # Feed through EMA filters
        ema1_out = self.ema_1.step(self.dsum, prev_dsum_e2, alpha1)

        if self.EMA_CASCADE:
            ema2_out = self.ema_2.step(
                ema1_out['average'],
                ema1_out['average_ena'],
                alpha2
            )
            return {'power_squared': ema2_out['average']}
        else:
            return {'power_squared': ema1_out['average']}


if __name__ == "__main__":
    import numpy as np

    print("Power detector fixed-point test:")
    pd = PowerDetector(data_w=12, iq_mod=True, fixed_point=True)

    for i in range(20):
        I = signed(int(500 * np.sin(2 * np.pi * i / 10)), 12)
        Q = signed(int(500 * np.cos(2 * np.pi * i / 10)), 12)
        out = pd.step(I, Q, 1, 0x8000, 0x8000)
        print(f"  [{i:2d}] I={I:6d} Q={Q:6d}  power={out['power_squared']:10d}")
