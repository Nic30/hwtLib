#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import If, Concat, SwitchLogic
from hwt.code_utils import rename_signal
from hwt.hdl.constants import WRITE, READ
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4, Axi4_addr, Axi4_r
from hwtLib.amba.axi_comp.lsu.fifo_oooread import FifoOutOfOrderRead
from hwtLib.amba.axi_comp.oooOp.utils import OutOfOrderCummulativeOpIntf, \
    OOOOpPipelineStage, does_collinde, OutOfOrderCummulativeOpPipelineConfig
from hwtLib.amba.constants import BURST_INCR, PROT_DEFAULT, BYTES_IN_TRANS, \
    LOCK_DEFAULT, CACHE_DEFAULT, QOS_DEFAULT
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtLib.types.ctypes import uint32_t, uint8_t
from pyMathBitPrecise.bit_utils import mask


class OutOfOrderCummulativeOp(Unit):
    """
    Out of order container of read-modify-write cummulative operation.

    This is a component template for cumulative Out of Order operations with hihgh latency AXI.
    Suitable for counter arrays, hash tables and other data structures which are acessing data randomly
    and potential collision due read-modify-write operations may occure.

    This component stores info about currently executed memory transactions which may be finished out of order.
    Potential memory access colisions are solved by write forwarding in main pipeline.
    In order to compensate for memory write latency the write history is utilised.
    The write history is a set of registers on the end of the pipeline.

    Note that the write history is not meant as a main mechanism for write latency compensation.
    It is meant to be used for 3-4 items to componsate for latency of the cache/LSU.

    If the main operation requires multiple clock cycles the operation is performed speculatively.

    The most up-to-date version of the data is always selected on the input of WRITE_BACK stage.

    :ivar MAIN_STATE_T: a type of the state in main memory which is being updated by this component
    :note: If MAIN_STATE_T.bit_length() is smaller than DATA_WIDTH each item is allocated in
        a signle bus word separately in order to avoid alignment logic
    :ivar TRANSACTION_STATE_T: a type of the transaction state, used to store additional data
        for transaction and can be used to modify the behavior of the pipeline
    :type TRANSACTION_STATE_T: Optional[HdlType]
    :type PIPELINE_CONFIG: OutOfOrderCummulativeOpPipelineConfig
    """

    def _config(self):
        # number of items in main array is resolved from ADDR_WIDTH and size of STATE_T
        # number of concurent thread is resolved as 2**ID_WIDTH
        self.MAIN_STATE_T = Param(uint32_t)
        self.TRANSACTION_STATE_T = Param(uint8_t)
        self.PIPELINE_CONFIG = Param(
            OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_HISTORY_SIZE=4 + 1)
        )
        Axi4._config(self)

    def _init_constants(self):
        MAIN_STATE_T = self.MAIN_STATE_T
        # constant precomputation
        self.ADDR_OFFSET_W = log2ceil(max(MAIN_STATE_T.bit_length(), self.DATA_WIDTH) // 8)
        self.MAIN_STATE_INDEX_WIDTH = self.ADDR_WIDTH - self.ADDR_OFFSET_W
        self.MAIN_STATE_ITEMS_CNT = (2 ** self.MAIN_STATE_INDEX_WIDTH)

    def _declr(self):
        addClkRstn(self)
        self._init_constants()

        with self._paramsShared():
            self.m = Axi4()._m()

        self.ooo_fifo = FifoOutOfOrderRead()
        self.ooo_fifo.ITEMS = 2 ** self.ID_WIDTH

        sa = self.state_array = RamSingleClock()
        sa.PORT_CNT = (WRITE, READ)
        sa.ADDR_WIDTH = self.ID_WIDTH

        TRANSACTION_STATE_T = self.TRANSACTION_STATE_T
        # address + TRANSACTION_STATE_T
        sa.DATA_WIDTH = self.MAIN_STATE_INDEX_WIDTH + (
            0 if TRANSACTION_STATE_T is None else
            TRANSACTION_STATE_T.bit_length()
        )

        self._declr_io()

    def _declr_io(self):
        # index of the item to increment
        din = self.dataIn = OutOfOrderCummulativeOpIntf()
        dout = self.dataOut = OutOfOrderCummulativeOpIntf()._m()
        for i in [din, dout]:
            i.MAIN_STATE_INDEX_WIDTH = self.MAIN_STATE_INDEX_WIDTH
            i.TRANSACTION_STATE_T = self.TRANSACTION_STATE_T
        din.MAIN_STATE_T = None
        dout.MAIN_STATE_T = self.MAIN_STATE_T

    def main_op(self, main_state: RtlSignal) -> RtlSignal:
        raise NotImplementedError("Override this in your implementation of this abstract component")

    def _axi_addr_defaults(self, a: Axi4_addr, word_cnt: int):
        """
        Set default values for AXI address channel signals
        """
        a.len(word_cnt - 1)
        a.burst(BURST_INCR)
        a.prot(PROT_DEFAULT)
        a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        a.lock(LOCK_DEFAULT)
        a.cache(CACHE_DEFAULT)
        a.qos(QOS_DEFAULT)

    def ar_dispatch(self):
        """
        Send read request on AXI and store transaction in to state array and ooo_fifo for later wake up
        """
        ooo_fifo = self.ooo_fifo
        ar = self.m.ar
        din = self.dataIn
        assert din.addr._dtype.bit_length() == self.ADDR_WIDTH - self.ADDR_OFFSET_W, (
            din.addr._dtype.bit_length(), self.ADDR_WIDTH, self.ADDR_OFFSET_W)
        dataIn_reg = HandshakedReg(din.__class__)
        dataIn_reg._updateParamsFrom(din)
        self.dataIn_reg = dataIn_reg
        StreamNode(
            [din],
            [dataIn_reg.dataIn, ooo_fifo.write_confirm]
        ).sync()
        dataIn_reg.dataIn(din, exclude=[din.rd, din.vld])

        ar_node = StreamNode(
            [dataIn_reg.dataOut, ooo_fifo.read_execute],
            [ar]
        )
        ar_node.sync()

        state_arr = self.state_array
        state_write = state_arr.port[0]
        state_write.en(ar_node.ack())
        state_write.addr(ooo_fifo.read_execute.index)

        din_data = dataIn_reg.dataOut

        state_write.din(packIntf(din_data, exclude=[din_data.rd, din_data.vld]))

        ar.id(ooo_fifo.read_execute.index)
        ar.addr(Concat(din_data.addr, Bits(self.ADDR_OFFSET_W).from_py(0)))
        self._axi_addr_defaults(ar, 1)

    def instruction_supports_forwarding(self, st: OOOOpPipelineStage):
        return True

    def collision_detector(self, pipeline: List[OOOOpPipelineStage]) -> List[List[RtlSignal]]:
        """
        Search for address access collisions in pipeline and store the result of colision check to registers for
        data write forwarding in next clock tick
        """
        PIPELINE_CONFIG = self.PIPELINE_CONFIG

        for dst in pipeline:
            # construct colision detector flags
            dst.collision_detect = [
                0
                # because we do not know the address in first stage
                # and write history stages do not require an update
                if (dst.index <= 1 or
                    src_i < PIPELINE_CONFIG.WRITE_BACK or
                    dst.index >= PIPELINE_CONFIG.WRITE_BACK or
                    src_i == dst.index)
                else
                self._reg(f"{dst.name:s}_collision_detect_from_{src_i:d}", def_val=0)

                for src_i in range(len(pipeline))
            ]

            if dst.index <= 1:
                # because we do not know the address in first stage
                continue
            elif dst.index >= PIPELINE_CONFIG.WRITE_BACK:
                # we can not update write history
                break

            dst_prev = pipeline[dst.index - 1] if dst.index > 1 else None

            # for each stage which can potentially update a data in this stage
            for src_i in range(PIPELINE_CONFIG.WRITE_BACK, len(pipeline)):
                src = pipeline[src_i] if src_i > 0 else None
                src_prev = pipeline[src_i - 1] if src_i > 1 else None

                # :attention: the cd is a register and its value will be checked in next clock cycle
                # that means that we need to resolve its value for next clock cycle
                cd = dst.collision_detect[src_i]
                c = self._sig(f"{cd.name:s}_tmp")
                # Resolve if dst stage should load from src stage in next clock cycle
                If(~dst.load_en & ~src.load_en,
                    c(does_collinde(dst, src) & self.instruction_supports_forwarding(dst)),
                ).Elif(~dst.load_en & src.load_en,
                    c(does_collinde(dst, src_prev) & self.instruction_supports_forwarding(dst))
                ).Elif(dst.load_en & ~src.load_en,
                    c(does_collinde(dst_prev, src) & self.instruction_supports_forwarding(dst_prev))
                ).Elif(dst.load_en & src.load_en,
                    c(does_collinde(dst_prev, src_prev) & self.instruction_supports_forwarding(dst_prev))
                ).Else(
                    c(0)
                )

                cd(c & dst.valid.next)

    def apply_data_write_forwarding(self, st: OOOOpPipelineStage,
                           st_load_en: RtlSignal,
                           data_modifier=lambda dst_st, src_st: dst_st.data(src_st.data)):
        """
        :param st_collision_detect: in format stages X pipeline[WRITE_BACK-1:], if bit = 1 it means
            that the stage data should be updated from stage on that index
        """
        st_prev = self.pipeline[st.index - 1]

        def is_not_0(sig):
            return not (isinstance(sig, int) and sig == 0)

        # we can write forward to a stages from STATE_LOAD to WRITE_BACK
        # however we can not replace the valid value in WRITE_BACK stage
        # and we need to wait on load_en
        res = SwitchLogic([
                (
                    # the previous which is beeing loaded into this is colliding with src
                    (st_load_en & st_prev.collision_detect[src_i]) |
                    (~st_load_en & st.collision_detect[src_i]),
                    # forward data instead of data from previous stage
                    data_modifier(st, src_st)
                )
                for src_i, src_st in enumerate(self.pipeline) if (
                        # filter out stage combinations which do not have forwarding
                        is_not_0(st.collision_detect[src_i]) or
                        is_not_0(st_prev.collision_detect[src_i])
                    )
            ],
            default=\
            If(st_load_en,
               data_modifier(st, st_prev)
            )
        )

        return res

    def data_load(self, r: Axi4_r, st0: OOOOpPipelineStage):
        w = self.MAIN_STATE_T.bit_length()
        assert w <= r.data._dtype.bit_length(), (w, r.data._dtype)
        return st0.data(r.data[w:]._reinterpret_cast(self.MAIN_STATE_T))

    def propagate_trans_st(self, stage_from: OOOOpPipelineStage, stage_to: OOOOpPipelineStage):
        HAS_TRANS_ST = self.TRANSACTION_STATE_T is not None
        if HAS_TRANS_ST:
            return stage_to.transaction_state(stage_from.transaction_state)
        else:
            return ()

    def write_cancel(self, st: OOOOpPipelineStage):
        """
        :returns: A signal/value which if it is 1 it means that the write back
            of this state should not be performed.
        """
        return BIT.from_py(0)

    def main_pipeline(self):
        PIPELINE_CONFIG = self.PIPELINE_CONFIG
        self.pipeline = pipeline = [
            OOOOpPipelineStage(i, f"st{i:d}", self)
            for i in range(PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK + 1)
        ]

        state_read = self.state_array.port[1]
        self.collision_detector(pipeline)
        HAS_TRANS_ST = self.TRANSACTION_STATE_T is not None

        for i, st in enumerate(pipeline):
            if i > 0:
                st_prev = pipeline[i - 1]

            if i < len(pipeline) - 1:
                st_next = pipeline[i + 1]

            # :note: pipeline stages described in PIPELINE_CONFIG enum
            if i == PIPELINE_CONFIG.READ_DATA_RECEIVE:
                # :note: we can not apply forward write data there because we do not know the original address yet
                r = self.m.r
                state_read.addr(r.id)
                st.addr = state_read.dout[self.MAIN_STATE_INDEX_WIDTH:]
                if HAS_TRANS_ST:
                    low = self.MAIN_STATE_INDEX_WIDTH
                    st.transaction_state = state_read.dout[:low]._reinterpret_cast(self.TRANSACTION_STATE_T)

                r.ready(st.in_ready)
                st.in_valid(r.valid)
                st.out_ready(st_next.in_ready)
                state_read.en(st.load_en)
                If(st.load_en,
                    st.id(r.id),
                    self.data_load(r, st),
                )

            elif i <= PIPELINE_CONFIG.STATE_LOAD:
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, st),
                )
                self.apply_data_write_forwarding(st, st.load_en)
                st.in_valid(st_prev.valid)
                st.out_ready(st_next.in_ready)

            elif i == PIPELINE_CONFIG.WRITE_BACK:
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, st),
                )
                self.apply_data_write_forwarding(st, st.load_en, self.main_op)
                aw = self.m.aw
                w = self.m.w

                cancel = rename_signal(self, self.write_cancel(st), "write_back_cancel")
                st.in_valid(st_prev.valid)
                st.out_ready(st_next.in_ready & ((aw.ready & w.ready) | cancel))

                StreamNode(
                    [], [aw, w],
                    extraConds={
                        aw: st.valid & st_next.in_ready & ~cancel,
                        w: st.valid & st_next.in_ready & ~cancel
                    },
                    skipWhen={
                        aw:cancel,
                        w:cancel,
                    }
                ).sync()

                self._axi_addr_defaults(aw, 1)
                aw.id(st.id)
                aw.addr(Concat(st.addr, Bits(self.ADDR_OFFSET_W).from_py(0)))

                st_data = st.data
                if not isinstance(st_data, RtlSignal):
                    st_data = packIntf(st_data)

                w.data(st_data._reinterpret_cast(w.data._dtype))
                w.strb(mask(self.DATA_WIDTH // 8))
                w.last(1)

            elif i > PIPELINE_CONFIG.WRITE_BACK and i != PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK:
                if i == PIPELINE_CONFIG.WRITE_BACK + 1:
                    st.in_valid(st_prev.valid & ((aw.ready & w.ready) | cancel))
                else:
                    st.in_valid(st_prev.valid)
                st.out_ready(st_next.in_ready)

                If(st.load_en,
                   st.id(st_prev.id),
                   st.addr(st_prev.addr),
                   st.data(st_prev.data),
                   self.propagate_trans_st(st_prev, st),
                )
            elif i == PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK:
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, st),
                    st.data(st_prev.data),
                )
                dout = self.dataOut
                b = self.m.b
                confirm = self.ooo_fifo.read_confirm
                cancel = self.write_cancel(st)

                # ommiting st_next.ready as there is no next
                w_ack_node = StreamNode(
                    [b],
                    [dout, confirm],
                    extraConds={
                        dout: st.valid,
                        b: st.valid & ~cancel,
                        confirm: st.valid,
                    },
                    skipWhen={
                        b: st.valid & cancel,
                    }
                )
                w_ack_node.sync()
                st.in_valid(st_prev.valid)
                st.out_ready((b.valid | cancel) & dout.rd & confirm.rd)

                dout.addr(st.addr)
                dout.data(st.data)
                if HAS_TRANS_ST:
                    dout.transaction_state(st.transaction_state)

                confirm.data(st.id)

    def _impl(self):
        self.ar_dispatch()
        self.main_pipeline()
        propagateClkRstn(self)
