#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage


class OooOpExampleCounterHashTable(OutOfOrderCummulativeOp):

    class OPERATION():
        SWAP = 0 # insert and return original key, item_valid, value (can be also used to delete the item)
        LOOKUP_OR_SWAP = 1 # lookup and update if key found or swap key, item_valid, value
        LOOKUP = 2 # lookup and update if key found else perfor no state update

    def _config(self):
        OutOfOrderCummulativeOp._config(self)
        self.MAIN_STATE_T = HStruct(
            (BIT, "item_valid"),
            (Bits(32), "key"),
            (Bits(self.DATA_WIDTH - 32 - 1), "value"),
        )
        # the transaction always just increments the counter
        # so there is no need for transaction state
        self.TRANSACTION_STATE_T = HStruct(
            # if true the key was modified during processing
            # and we need to recirculate the transaction in pipeline
            # (which should be done by parent component and it does not happen automatically)
            (BIT, "reset"),
            (self.MAIN_STATE_T, "data"),
            # for output 1 if key was same as key in lookup transaction
            (BIT, "key_match"),
            (Bits(2), "operation"), # :see: :class:`~.OPERATION`
        )
    def propagate_trans_st(self, stage_from: OOOOpPipelineStage, stage_to: OOOOpPipelineStage):
        PIPELINE_CONFIG = self.PIPELINE_CONFIG
        src = stage_from.transaction_state
        dst = stage_to.transaction_state
        if stage_to.index == PIPELINE_CONFIG.WRITE_BACK:
            return [
                dst.key_match(stage_from.data._eq(src.data)),
                connect(src, dst, exclude=[dst.key_match])
            ]
        else:
            return dst(src)

    def write_cancel(self, st:OOOOpPipelineStage):
        return ~st.transaction_state.key_match & st.transaction_state.operation._eq(self.OPERATION.LOOKUP)

    def main_op(self, dst_main_state: OOOOpPipelineStage, src_main_state: OOOOpPipelineStage):
        # [TODO] if operation==SWAP or operation == LOOKUP_OR_SWAP and not key_match use data from input instead
        dst = dst_main_state.data
        src = src_main_state.data
        return [
            dst.item_valid(src.item_valid),
            dst.key(src.key),
            dst.value(src.value + 1),
        ]


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # u = _example_OutOfOrderCummulativeOp()
    u = OooOpExampleCounterHashTable()
    u.ID_WIDTH = 2
    u.ADDR_WIDTH = 2 + 3
    u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()

    print(to_rtl_str(u))
