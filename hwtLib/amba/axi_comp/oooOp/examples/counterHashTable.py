#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect, If
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage
from hwt.code_utils import rename_signal


class OooOpExampleCounterHashTable(OutOfOrderCummulativeOp):

    class OPERATION():
        # if swap the original item from main memory will be stored in transaction_state.data (the place where original insert key was stored)
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
        if stage_to.index == PIPELINE_CONFIG.WRITE_BACK - 1:
            key_match = rename_signal(self, stage_from.data.item_valid & stage_from.data.key._eq(src.data.key), "key_match")
            return [
                dst.key_match(key_match),
                If(stage_from.valid & stage_from.transaction_state.operation._eq(self.OPERATION.SWAP),
                    # swap or lookup_or_swap with not found
                    connect(stage_from.data, stage_to.transaction_state.data, exclude=[src.data.value]),
                    If(key_match,
                       dst.data.value(src.data.value + 1)
                    ).Else(
                       dst.data.value(src.data.value)
                    ),
                    connect(src, dst, exclude=[dst.data, dst.key_match])
                ).Else(
                    connect(src, dst, exclude=[dst.key_match])
                ),
            ]
        else:
            return dst(src)

    def write_cancel(self, st:OOOOpPipelineStage):
        return st.valid & ~st.transaction_state.key_match & st.transaction_state.operation._eq(self.OPERATION.LOOKUP)

    def main_op(self, dst_stage: OOOOpPipelineStage, src_stage: OOOOpPipelineStage):
        # if operation==SWAP or operation == LOOKUP_OR_SWAP and not key_match use data from input instead
        dst = dst_stage.data
        src = src_stage.data
        prev_st = self.pipeline[dst_stage.index - 1]
        return If(prev_st.valid & prev_st.transaction_state.key_match & (prev_st.transaction_state.operation != self.OPERATION.SWAP),
            # lookup or lookup_or_swap with found
            dst.item_valid(src.item_valid),
            dst.key(src.key),
            dst.value(src.value + 1),
        ).Elif(prev_st.valid & prev_st.transaction_state.operation._eq(self.OPERATION.SWAP),
            # swap or lookup_or_swap with not found
            dst(prev_st.data),
        ).Elif(prev_st.valid & ~prev_st.transaction_state.key_match,
            #  not match not swap, keep as it is
            dst(src),
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # u = _example_OutOfOrderCummulativeOp()
    u = OooOpExampleCounterHashTable()
    u.ID_WIDTH = 2
    u.ADDR_WIDTH = 2 + 3
    u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()

    print(to_rtl_str(u))
