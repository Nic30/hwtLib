#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Tuple

from hwt.code import If, In, SwitchLogic
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.structIntf import StructIntf
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axi_comp.oooOp.outOfOrderCummulativeOp import OutOfOrderCummulativeOp
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage


class OooOpExampleCounterHashTable(OutOfOrderCummulativeOp):
    """
    This components mantains the hash table where value is a counter.
    This hash table is accesed throught the axi interface.
    These counters are incremented using "dataIn" interface in a coherent way.
    The operation may finish out of order but the data on "dataOut" and in the memory
    will be correct. The same applays for the swap operations (all operations).

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

        self._key_cmp_cache: Dict[Tuple[OOOOpPipelineStage, OOOOpPipelineStage], RtlSignal] = {}

    def key_compare_cached(self, st0: OOOOpPipelineStage, st1: OOOOpPipelineStage):
        try:
            return self._key_cmp_cache[(st0, st1)]
        except KeyError:
            pass
        km = self.key_compare(st0, st1)
        self._key_cmp_cache[(st0, st1)] = km
        return km

    def key_compare(self, st0: OOOOpPipelineStage, st1: OOOOpPipelineStage):
        """
        This function is called on the entry to PIPELINE_CONFIG.WRITE_BACK - 1 (STATE_LOAD) register
        In this register data is loaded and present in st.data,
        the st.transaction_state.original_data contains the key which is beeing searched for.
        If the register is loaded from predecessor the data is in same format and fully loaded.

        There are several special cases which need to be handled.
        * If we are checking STATE_LOAD with its predecessor we need to precompute also
          the variant for the case that the .transaction_state.original_data and .data was swapped.
        * Later in pipeline we always checking STATE_LOAD and some of its successors
          for STATE_LOAD we need to pick .transaction_state.original_data for sucessor .data
        """
        if st1.index < self.PIPELINE_CONFIG.WRITE_BACK:
            assert st0.index >= self.PIPELINE_CONFIG.READ_DATA_RECEIVE, st0.index

            return rename_signal(self, (
                st0.valid &
                st0.data.item_valid &
                st0.addr._eq(st1.addr) &

                st1.valid &
                # using st1.transaction_state.original_data because we want to compare
                # the data from ram and the data which we are searching
                st1.transaction_state.original_data.item_valid &
                st0.data.key._eq(st1.transaction_state.original_data.key)
            ), f"key_cmp_data{st0.index:d}_trans_data{st1.index:d}")

        else:
            raise NotImplementedError()

    def get_latest_key_match(self, st: OOOOpPipelineStage):
        assert st.index == self.PIPELINE_CONFIG.WRITE_BACK, (st.index, self.PIPELINE_CONFIG.WRITE_BACK)
        latest_key_match = getattr(st, "latest_key_match", None)
        if latest_key_match is not None:
            return latest_key_match

        latest_key_match = self._sig(f"latest_key_match_for_{st.index:d}")
        st.latest_key_match = latest_key_match

        prev_st:OOOOpPipelineStage = self.pipeline[st.index - 1]
        SwitchLogic([
            (prev_st.collision_detect[coli_src.index] & prev_st.key_matches[coli_src.index],
             latest_key_match(1)
             )
            for coli_src in self.pipeline[st.index:]
        ], default=\
            latest_key_match(prev_st.key_matches[prev_st.index]),
        )
        return latest_key_match

    def do_swap_original_and_current_state(self, src_st: OOOOpPipelineStage, dst_st: OOOOpPipelineStage):
        P = self.PIPELINE_CONFIG
        prev_stage = self.pipeline[P.WRITE_BACK - 1]
        if dst_st.index == P.WRITE_BACK:
            OP = self.OPERATION
            # this is during the write forwarding real operation lays in the previous stage
            # just the data are forwarded from elsewhere

            op = prev_stage.transaction_state.operation

            return prev_stage.valid & (
                op._eq(OP.SWAP) | (
                op._eq(OP.LOOKUP_OR_SWAP) & ~self.get_latest_key_match(dst_st)
                )
            )
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
                    # not for each index representing an index of pipeline stage we compute
                    # the key match for a key which will apear in this register in next clock cycle
                    prev_st = self.pipeline[i - 1]
                    km = self._reg(f"key_matches_trans{dst_st.index}_and_data{i}", def_val=0)
                    dst_prev_st = self.pipeline[dst_st.index - 1]
                    If(dst_st.load_en,
                        # the stage will receive new data
                        If(st.load_en,
                            km(self.key_compare_cached(prev_st, dst_prev_st)),
                        ).Else(
                            km(self.key_compare_cached(st, dst_prev_st)),
                        )
                    ).Elif(dst_st.out_ready,
                        # the stage will be flushed
                        km(0),
                    ).Else(
                        # the stage will keeep its data
                        If(st.load_en,
                            km(self.key_compare_cached(prev_st, dst_st)),
                        ).Else(
                            km(self.key_compare_cached(st, dst_st)),
                        )
                    )
                key_matches.append(km)

            # not part of return because this must be updated with every clock cycle
            return [
                dst(src),
            ]
        elif dst_st.index == PIPELINE_CONFIG.WRITE_BACK:
            prev_st = self.pipeline[dst_st.index - 1]
            do_swap_original_and_current_state = rename_signal(
                self, src_st.valid & self.do_swap_original_and_current_state(src_st, dst_st),
                f"do_swap_original_and_current_state_{src_st.index:d}to{dst_st.index:d}"
            )
            return [
                # Resolving of key_match
                # * The WRITE_BACK-1 stage does have collision detector prediction array
                #   it provides an information which stage has latest version of data of this address
                #   This stage also have the key_matches prediction array wich do have prediction matching
                #   of stage data.key with WRITE_BACK-1 transaction_state.key
                # * When resolving the key_match we need to select the key match for latest data.
                # * If there are no collisions the latest data is already in WRITE_BACK-1 stage.
                If(do_swap_original_and_current_state,
                    # swap or lookup_or_swap with not found, we need to store original record from table
                    # as specified by :attr:`OooOpExampleCounterHashTable.OPERATION`
                    # :note: in this function we handle only transaction_state
                    dst.original_data(src_st.data),
                    dst(src, exclude=[dst.original_data, dst.key_match]),
                ).Else(
                    dst(src, exclude=[dst.key_match])
                ),
                dst.key_match(self.get_latest_key_match(dst_st)),
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
        key_match = self.get_latest_key_match(dst_st)

        do_swap_original_and_current_state = rename_signal(
            self, self.do_swap_original_and_current_state(src_st, dst_st),
            f"do_swap_original_and_current_state_{src_st.index:d}to{dst_st.index:d}"
        )
        return  If(prev_st.valid,
                    # enable register load only if previous data available
                    If(rename_signal(self,
                                     prev_st.valid &
                                     prev_st.addr._eq(src_st.addr) &
                                     # src_st.valid &
                                     # src_st.data.item_valid &
                                     In(prev_st.transaction_state.operation, [OP.LOOKUP, OP.LOOKUP_OR_SWAP]) &
                                     key_match,
                                     f"exec_main_op_on_lookup_match_update_from{src_st.index:d}"),
                        # lookup or lookup_or_swap with found with possible data forwarding
                        dst.item_valid(src.item_valid),
                        self.main_op_on_lookup_match_update(dst_st, src_st),

                    ).Elif(do_swap_original_and_current_state,
                        # swap or lookup_or_swap with not found
                        dst(prev_st.transaction_state.original_data)  # the data should be swapped from prev_st.data

                    ).Else(
                        #  not match not swap, keep as it is (and pass in the pipeline)
                        dst(src),
                    )
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
