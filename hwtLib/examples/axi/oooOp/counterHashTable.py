#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, In, SwitchLogic
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.structIntf import StructIntf
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage


class OooOpExampleCounterHashTable(OutOfOrderCummulativeOp):
    """
    This components mantains the hash table where value is a counter.
    This hash table is accesed throught the axi interface.
    These counters are incremented using "dataIn" interface in a coherent way.
    The operation may finish out of order but the data on "dataOut" and in the memory
    will be correct. The same applies for the swap operations (all operations).

    .. hwt-autodoc:: _example_OooOpExampleCounterHashTable
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
            # must be computed in WRITE_BACK -1 stage because we need it for main_op which takes place before
            # WRITE_BACK
            (BIT, "key_match"),
            (Bits(2), "operation"),  # :see: :class:`~.OPERATION`
        )

    def _declr(self):
        OutOfOrderCummulativeOp._declr(self)
        swap_container_type = self.TRANSACTION_STATE_T.field_by_name["original_data"].dtype
        assert swap_container_type is self.MAIN_STATE_T, (swap_container_type, self.MAIN_STATE_T)

    def key_compare(self, st0: OOOOpPipelineStage, st1: OOOOpPipelineStage):
        return (
            st0.valid.next & 
            st1.valid.next & 
            st0.addr.next._eq(st1.addr.next) &
            st0.transaction_state.original_data.item_valid._sig.next & 
            st1.data.item_valid._sig.next & 
            st0.transaction_state.original_data.key._sig.next._eq(st1.data.key._sig.next)
        )

    def get_latest_key_match(self, st: OOOOpPipelineStage):
        """
        :return: a signal which is flag which signalizes that in this clock cycle
            the st has the key which match with latest colliding item or with transactional data of this state
        
        """
        assert st.index == self.PIPELINE_CONFIG.WRITE_BACK, (st.index, self.PIPELINE_CONFIG.WRITE_BACK)
        latest_key_match = getattr(st, "latest_key_match", None)
        if latest_key_match is not None:
            return latest_key_match

        latest_key_match = self._sig(f"st{st.index:d}_latest_key_match")
        st.latest_key_match = latest_key_match

        # :note: stage itself may contain outdated data that is why we have to check colliding items first
        prev_st:OOOOpPipelineStage = self.pipeline[st.index - 1]
        SwitchLogic([
            (prev_st.collision_detect[coli_src.index],
                # the item for this stage was updated, we need to use the updated version of it
                
                # if the source of collision is WRITE_BACK we need to also check if the data and data from transactional_state were swapped
                # we need to also check if the item was swapped or not or where it was update from
                latest_key_match(prev_st.key_matches[coli_src.index])
            )
            for coli_src in self.pipeline[st.index:]
        ], default=[
            # :note: the stage has latest data 
            latest_key_match(prev_st.key_matches[prev_st.index]),
        ])
        return latest_key_match

    def do_swap_original_and_current_state(self, src_st: OOOOpPipelineStage, dst_st: OOOOpPipelineStage):
        """
        :return: a signal which is a flag which is 1 if the data in transactional state and the data from/to memory should be swapped
        """
        
        P = self.PIPELINE_CONFIG
        prev_stage = self.pipeline[P.WRITE_BACK - 1]
        if dst_st.index == P.WRITE_BACK:
            OP = self.OPERATION
            # this is during the write forwarding real operation lays in the previous stage
            # just the data are forwarded from elsewhere

            op = prev_stage.transaction_state.operation

            res = (
                src_st.valid & 
                # dst_st.valid.next & 
                prev_stage.valid & 
                (
                    op._eq(OP.SWAP) | (
                        op._eq(OP.LOOKUP_OR_SWAP) & ~self.get_latest_key_match(dst_st)
                    )
                )
            )
            return rename_signal(self, res,
                f"do_swap_original_and_current_state_{src_st.index:d}to{dst_st.index:d}")

        else:
            return BIT.from_py(0)

    def propagate_trans_st(self, src_st: OOOOpPipelineStage, dst_st: OOOOpPipelineStage):
        """
        Pass the state of operation (lookup/swap) in pipeline
        in state before write_back chech if the key matches and

        :note: The trasaction can potentially collide with anything back in pipeline
            The pipeline supports flushing that implies that each data word has individual condition for moving
            to the next stage.
        """
        PIPELINE_CONFIG = self.PIPELINE_CONFIG
        src:StructIntf[self.TRANSACTION_STATE_T] = src_st.transaction_state
        dst:StructIntf[self.TRANSACTION_STATE_T] = dst_st.transaction_state
        if dst_st.index == PIPELINE_CONFIG.WRITE_BACK - 1:
            # here we are loading the word into a stage WRITE_BACK - 1
            # we must compute key matching for main_op
            # but there we do not have the collicions precomputed yet and
            # we must compare the item which will be in WRITE_BACK - 1 in next clock cycle
            # with all successor items
            dst_st.key_matches = key_matches = []
            for i, st in enumerate(self.pipeline):
                if i < dst_st.index:
                    km = BIT.from_py(0)
                else:
                    km = self._reg(f"key_matches_trans{dst_st.index}_and_data{i}", def_val=0)
                    km(self.key_compare(dst_st, st))

                key_matches.append(km)

            # key match logic not part of return because this must be updated with every clock cycle independently
            return [
                dst(src),
            ]

        elif dst_st.index == PIPELINE_CONFIG.WRITE_BACK:
            # handled in main_op
            return []
        else:
            return dst(src)

    def write_cancel(self, write_back_st: OOOOpPipelineStage):
        """
        :return: signal which if it is 1 the transaction state update is not writen back to memory
            (e.g. 1 if key does not match and we do not want to update counters)
        """
        ts = write_back_st.transaction_state
        return write_back_st.valid & \
               ~write_back_st.transaction_state.key_match & \
               ts.operation._eq(self.OPERATION.LOOKUP)

    def main_op_on_lookup_match_update(self, dst_st: OOOOpPipelineStage, src_st: OOOOpPipelineStage):
        return [
            dst_st.data(src_st.data, exclude=[src_st.data.value ]),
            dst_st.data.value(src_st.data.value + 1)
        ]

    def main_op(self, dst_st: OOOOpPipelineStage, src_st: OOOOpPipelineStage):
        """
        A main opration of counter incrementation

        :note: This function is called for write back state and its predecessor.
            However because of write bypass this function is called multiple times for each bypass as well.
        """
        dst = dst_st.data
        src = src_st.data
        OP = self.OPERATION
        P = self.PIPELINE_CONFIG
        assert dst_st.index == P.WRITE_BACK
        prev_st = self.pipeline[dst_st.index - 1]

        do_swap_original_and_current_state = self.do_swap_original_and_current_state(src_st, dst_st)
        latest_key_match = self.get_latest_key_match(dst_st)
        match_found = rename_signal(
            self,
            In(prev_st.transaction_state.operation, [OP.LOOKUP, OP.LOOKUP_OR_SWAP]) & 
            latest_key_match,
            f"exec_main_op_on_lookup_match_update_{dst_st.index:d}from{src_st.index:d}")

        dst_tr:StructIntf[self.TRANSACTION_STATE_T] = dst_st.transaction_state
        return  [
            If(prev_st.valid,
                *(
                    (
                        # if we are comparing with state < P.WRITE_BACK we are interested
                        # in transactional data because these are the data we are comparing the key from ram with
                        If(do_swap_original_and_current_state,
                            # swap or lookup_or_swap with not found, we need to store original record from table
                            # as specified by :attr:`OooOpExampleCounterHashTable.OPERATION`
                            dst_tr.original_data(src_st.data),
                        ).Else(
                            dst_tr.original_data(src_st.transaction_state.original_data),
                        ),
                    )
                    if src_st.index < P.WRITE_BACK else
                    (
                        # if state >= P.WRITE_BACK we are interested only in data which were written to ram
                        If(do_swap_original_and_current_state,
                            dst_tr.original_data(src_st.data),
                        ).Else(
                            dst_tr.original_data(prev_st.transaction_state.original_data)
                        ),
                    )
                ),
                dst_tr.key_match(latest_key_match),
                dst_tr(prev_st.transaction_state, exclude=[dst_tr.key_match, dst_tr.original_data]),
                
                # Resolving of key_match
                # * The WRITE_BACK-1 stage does have collision detector prediction array
                #   it provides an information which stage has latest version of data of this address
                #   This stage also have the key_matches prediction array wich do have prediction matching
                #   of stage data.key with WRITE_BACK-1 transaction_state.key
                # * When resolving the key_match we need to select the key match for latest data.
                # * If there are no collisions the latest data is already in WRITE_BACK-1 stage.
                # enable register load only if previous data available

                If(do_swap_original_and_current_state,
                    # SWAP or LOOKUP_OR_SWAP with not found
                   # the data should be swapped from prev_st.data
                    dst(prev_st.transaction_state.original_data)
                ).Elif(match_found,
                    # lookup or lookup_or_swap with found with possible data forwarding
                    dst.item_valid(src.item_valid),
                    *self.main_op_on_lookup_match_update(dst_st, src_st),

                ).Else(
                    # not match not swap, keep as it is (and pass in the pipeline)
                    dst(src),
                ),
            ),
        ]


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
        (u.MAIN_STATE_T, "original_data"),
        (BIT, "key_match"),
        (Bits(2), "operation"),  # :see: :class:`~.OPERATION`
    )
    u.DATA_WIDTH = u.MAIN_STATE_T.bit_length()
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_OooOpExampleCounterHashTable()
    print(to_rtl_str(u))
