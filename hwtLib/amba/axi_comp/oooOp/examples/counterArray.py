#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp


class OooOpExampleCounterArray(OutOfOrderCummulativeOp):

    def _config(self):
        OutOfOrderCummulativeOp._config(self)
        # the transaction always just increments the counter
        # so there is no need for transaction state
        self.TRANSACTION_STATE_T = None

    def main_op(self,  dst_main_state: RtlSignal, src_main_state: RtlSignal):
        return dst_main_state.data(src_main_state.data + 1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # u = _example_OutOfOrderCummulativeOp()
    u = OooOpExampleCounterArray()
    u.ID_WIDTH = 2
    u.ADDR_WIDTH = 2 + 3
    u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()

    print(to_rtl_str(u))
