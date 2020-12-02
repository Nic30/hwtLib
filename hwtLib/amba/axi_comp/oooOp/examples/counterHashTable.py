#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import connect, If, In
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage


class OooOpExampleCounterHashTable(OutOfOrderCummulativeOp):
    """
    This components mantains the hash table where value is a counter.
    This hash table is accesed throught the axi interface.
    These counters are incremented using "dataIn" interface in a coherent way.
    The operation may finish out of order but the data on "dataOut" and in the memory
    will be correct. The same applays for the swap operations (all operations).

    .. hwt-schematic:: _example_OooOpExampleCounterHashTable
    """

    class OPERATION():
        # if swap the original item from main memory will be stored in transaction_state.original_data
        # (the place where original insert/lookup key was stored)
        # and the item which was in initial swap transaction will be stored in main state
        SWAP = 0  # insert and return original key, item_valid, value (can be also used to delete the item)
        LOOKUP_OR_SWAP = 1  # lookup and update if key found or swap key, item_valid, value
        LOOKUP = 2  # lookup and update if key found else perfor no state update

    def _config(self):
        OutOfOrderCummulativeOp._config(self)
        # state in main memory
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
            # container of original key and data for insert or match
            (self.MAIN_STATE_T, "original_data"),
            # for output 1 if key was same as key in lookup transaction
            (BIT, "key_match"),
            (Bits(2), "operation"),  # :see: :class:`~.OPERATION`
        )

    def _declr(self):
        OutOfOrderCummulativeOp._declr(self)
        swap_container_type = self.TRANSACTION_STATE_T.field_by_name["original_data"].dtype
        assert swap_container_type is self.MAIN_STATE_T, (swap_container_type, self.MAIN_STATE_T)

    def key_compare(self, k0, k1):
        return k0._eq(k1)

    def propagate_trans_st(self, stage_from: OOOOpPipelineStage, stage_to: OOOOpPipelineStage):
        """
        Pass the state of operation (lookup/swap) in pipeline
        in state before write_back chech if the key matches and
        """
        PIPELINE_CONFIG = self.PIPELINE_CONFIG
        src = stage_from.transaction_state
        dst = stage_to.transaction_state
        if stage_to.index == PIPELINE_CONFIG.WRITE_BACK - 1:
            key_match = rename_signal(self, stage_from.data.item_valid & self.key_compare(stage_from.data.key, src.original_data.key), "key_match")
            op = stage_from.transaction_state.operation
            return [
                dst.key_match(key_match),
                If(stage_from.valid & (op._eq(self.OPERATION.SWAP) | (op._eq(self.OPERATION.LOOKUP_OR_SWAP) & ~key_match)),
                    # swap or lookup_or_swap with not found, wee need to store original key
                    # as specified by :attr:`OooOpExampleCounterHashTable.OPERATION`
                    connect(stage_from.data, dst.original_data),
                    connect(src, dst, exclude=[dst.original_data, dst.key_match])
                ).Else(
                    connect(src, dst, exclude=[dst.key_match])
                )
            ]
        else:
            return dst(src)

    def write_cancel(self, write_back_st: OOOOpPipelineStage):
        """
        :return: signal which if it is 1 the transaction state update is not writen back to memory
            (e.g. 1 if key does not match and we do not want to update counters)
        """
        return write_back_st.valid & \
               ~write_back_st.transaction_state.key_match & \
               write_back_st.transaction_state.operation._eq(self.OPERATION.LOOKUP)

    def main_op_on_lookup_match_update(self, dst_stage: OOOOpPipelineStage, src_stage: OOOOpPipelineStage):
        return [
            dst_stage.data.value(src_stage.data.value + 1)
        ]

    def main_op(self, dst_stage: OOOOpPipelineStage, src_stage: OOOOpPipelineStage):
        """
        A main opration of counter incrementation

        :note: This function is called for write back state and its predecessor.
            However because of write bypass this function is called multiple times for each bypass as well.
        """
        dst = dst_stage.data
        src = src_stage.data
        prev_st = self.pipeline[dst_stage.index - 1]
        OP = self.OPERATION
        prev_st_op = prev_st.transaction_state.operation

        return If(prev_st.valid & prev_st.transaction_state.key_match & In(prev_st_op, [OP.LOOKUP, OP.LOOKUP_OR_SWAP]),
            # lookup or lookup_or_swap with found
            dst.item_valid(src.item_valid),
            dst.key(src.key),
            self.main_op_on_lookup_match_update(dst_stage, src_stage),
        ).Elif(prev_st.valid & prev_st_op._eq(OP.SWAP),
            # swap or lookup_or_swap with not found
            dst(prev_st.data),
        ).Elif(prev_st.valid & ~prev_st.transaction_state.key_match,
            #  not match not swap, keep as it is
            dst(src),
        )

def _example_OooOpExampleCounterHashTable():
    u = OooOpExampleCounterHashTable()
    u.ID_WIDTH = 6
    u.ADDR_WIDTH = 16 + 3
    u.MAIN_STATE_T = HStruct(
        (BIT, "item_valid"),
        (Bits(256), "key"),
        (Bits(32), "value"),
        (Bits(512 - 256 - 32 - 1), "padding"),
    )
    u.TRANSACTION_STATE_T = HStruct(
        (BIT, "reset"),
        (u.MAIN_STATE_T, "data"),
        (BIT, "key_match"),
        (Bits(2), "operation"),  # :see: :class:`~.OPERATION`
    )
    u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_OooOpExampleCounterHashTable()
    print(to_rtl_str(u))
