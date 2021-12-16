#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
from typing import List, Optional, Union

from hwt.code import If, Concat, SwitchLogic, Switch
from hwt.code_utils import rename_signal
from hwt.hdl.constants import WRITE, READ
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.hdlType import HdlType
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import packIntf
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4, Axi4_addr, Axi4_r, Axi4_w
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

    .. figure:: ./_static/OutOfOrderCummulativeOp_pipeline.png

    :ivar MAIN_STATE_T: a type of the state in main memory which is being updated by this component
    :note: If MAIN_STATE_T.bit_length() is smaller than DATA_WIDTH each item is allocated in
        a signle bus word separately in order to avoid alignment logic
    :ivar TRANSACTION_STATE_T: a type of the transaction state, used to store additional data
        for transaction and can be used to modify the behavior of the pipeline
    :note: provides axi aw and first w word in same clock cycle only
    """

    def _config(self):
        # number of items in main array is resolved from ADDR_WIDTH and size of STATE_T
        # number of concurent thread is resolved as 2**ID_WIDTH
        self.MAIN_STATE_T: Optional[HdlType] = Param(uint32_t)
        self.TRANSACTION_STATE_T: Optional[HdlType] = Param(uint8_t)
        self.PIPELINE_CONFIG: OutOfOrderCummulativeOpPipelineConfig = Param(
            OutOfOrderCummulativeOpPipelineConfig.new_config(
                WRITE_TO_WRITE_ACK_LATENCY=1,
                WRITE_ACK_TO_READ_DATA_LATENCY=1)
        )
        Axi4._config(self)

    def _init_constants(self):
        MAIN_STATE_T = self.MAIN_STATE_T
        # constant precomputation
        self.ADDR_OFFSET_W = log2ceil(max(MAIN_STATE_T.bit_length(), self.DATA_WIDTH) // 8)
        self.MAIN_STATE_INDEX_WIDTH = self.ADDR_WIDTH - self.ADDR_OFFSET_W
        self.MAIN_STATE_ITEMS_CNT = (2 ** self.MAIN_STATE_INDEX_WIDTH)
        self.BUS_WORD_CNT = ceil(self.MAIN_STATE_T.bit_length() / self.DATA_WIDTH)

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
        """
        Interpretation of main operatorion of the pipeline.
        """
        raise NotImplementedError("Override this in your implementation of this abstract component")

    def _axi_addr_defaults(self, a: Axi4_addr):
        """
        Set default values for AXI address channel signals
        """
        a.len(self.BUS_WORD_CNT - 1)
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
        self._axi_addr_defaults(ar)

    def can_write_forward(self, src_st: OOOOpPipelineStage,  dst_st: OOOOpPipelineStage):
        """
        Used when collision detector is build. (for next value of st WRITE_BACK-1)
        """
        return does_collinde(dst_st, src_st)

    def collision_detector(self, pipeline: List[OOOOpPipelineStage]) -> List[List[RtlSignal]]:
        """
        Search for address access collisions in pipeline and store the result of colision check
        to registers for data write forwarding in next clock cycle.
        The collision detector is build for DATA_LOAD (<P.WRITE_BACK) stages because we need to have
        collision information stored in registers in order to have enough time to do muxing
        in P.WRITE_BACK stage.
        """
        P = self.PIPELINE_CONFIG

        for dst in pipeline:
            # construct colision detector flags
            dst: OOOOpPipelineStage
            if dst.index <= 1:
                # because we do not know the address in first stage
                dst.collision_detect = [0 for _ in range(len(pipeline))]
                continue
            elif dst.index >= P.WRITE_BACK:
                # we can not update write history
                dst.collision_detect = [0 for _ in range(len(pipeline))]
                break

            dst.collision_detect = [
                0

                if (src_i < P.WRITE_BACK or # we can not update already writen data
                    src_i == dst.index or # we do not need update data with itsel
                    (
                       # because otherwise the previous data should be already updated
                       dst.index == P.WRITE_BACK and (src_i != P.WRITE_BACK)
                    )
                    )
                else
                self._reg(f"{dst.name:s}_collision_from_{src_i:d}", def_val=0)

                for src_i in range(len(pipeline))
            ]


            dst_prev = pipeline[dst.index - 1] if dst.index > 1 else None

            # for each stage which can potentially update a data in this stage
            for src_i in range(P.WRITE_BACK, len(pipeline)):
                src = pipeline[src_i] if src_i > 0 else None
                src_prev = pipeline[src_i - 1] if src_i > 1 else None

                # :attention: the cd is a register and its value will be checked in next clock cycle
                # that means that we need to resolve its value for next clock cycle
                # (for a new data which will be in stages of pipeline)
                cd = dst.collision_detect[src_i]
                c = self._sig(f"{cd.name:s}_tmp")
                # Resolve if dst stage should load from src stage in next clock cycle
                If(~dst.load_en & ~src.load_en,
                    c(self.can_write_forward(src, dst)),
                ).Elif(~dst.load_en & src.load_en,
                    c(self.can_write_forward(src_prev, dst))
                ).Elif(dst.load_en & ~src.load_en,
                    c(self.can_write_forward(src, dst_prev))
                ).Elif(dst.load_en & src.load_en,
                    c(self.can_write_forward(src_prev, dst_prev))
                ).Else(
                    # :note: all prev. cases should be covered
                    c(0)
                )

                cd(c & dst.valid.next)

    def write_forwarding_en(self, dst_st_load: RtlSignal,
                               dst_st: OOOOpPipelineStage,
                               dst_prev_st: OOOOpPipelineStage,
                               src_st_i: int):
        # the previous which is beeing loaded into this is colliding with src
        return (
            (dst_st_load & dst_prev_st.collision_detect[src_st_i]) |
            (~dst_st_load & dst_st.collision_detect[src_st_i])
        )

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
                    rename_signal(self, self.write_forwarding_en(st_load_en, st, st_prev, src_i),
                                  f"write_forwarding_en_{st.index}from{src_st.index}"),
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
        """
        Receive all data words from a bus and store them into stage of the pipeline.
        """
        if self.BUS_WORD_CNT > 1:
            LD_CNTR_MAX = self.BUS_WORD_CNT - 1
            cntr = self._reg("r_load_cntr", Bits(log2ceil(self.BUS_WORD_CNT)), def_val=0)
            If(r.valid & r.ready,
                If(cntr._eq(LD_CNTR_MAX),
                    cntr(0)
                ).Else(
                    cntr(cntr + 1)
                )
            )
        else:
            cntr = None

        data_w = r.data._dtype.bit_length()
        st_w = self.MAIN_STATE_T.bit_length()
        offset = 0
        cases = []
        st_data_flat = st0.data._reinterpret_cast(Bits(st_w))
        while offset < st_w:
            i = offset // data_w
            end = min(st_w, offset + data_w)
            w = end - offset
            cases.append((i, st_data_flat[end:offset](r.data[w:])))
            offset += data_w

        If(st0.load_en,
            st0.id(r.id),
        )
        if cntr is None:
            assert len(cases) == 1, cases
            ld_stm = cases[0][1]
        else:
            ld_stm = Switch(cntr)\
                .add_cases(cases)

        If(~st0.valid | st0.out_ready,
           ld_stm
        )

    def data_store(self, st_data: Union[StructIntf, RtlSignal], w: Axi4_w, ack: RtlSignal):
        """
        Transceive all data words from stage of pipeline to the bus.

        :param ack: signal which is 1 if the data word is transfered on this write channel
        """
        if not isinstance(st_data, RtlSignal):
            st_data = packIntf(st_data)

        data_w = self.DATA_WIDTH
        w.strb(mask(self.DATA_WIDTH // 8))
        st_w = self.MAIN_STATE_T.bit_length()
        word_cnt = self.BUS_WORD_CNT
        if word_cnt > 1:
            w_word_cntr = self._reg("w_word_cntr", Bits(log2ceil(word_cnt)), def_val=0)
            st_data_flat = st_data._reinterpret_cast(Bits(st_w))
            offset = 0
            cases = []
            while offset < st_w:
                i = offset // data_w
                end = min(st_w, offset + data_w)
                src = st_data_flat[end:offset]
                padding = (offset + data_w) - end
                if padding:
                    assert padding > 0
                    src = Concat(Bits(padding).from_py(0), src)
                cases.append((i, w.data(src)))
                offset += data_w
            If(ack,
                If(w.last,
                   w_word_cntr(0)
                ).Else(
                   w_word_cntr(w_word_cntr + 1)
                ),
            )
            Switch(w_word_cntr)\
                .add_cases(cases)\
                .Default(w.data(None))
            w.last(w_word_cntr._eq(word_cnt - 1))

        else:
            w.data(st_data._reinterpret_cast(w.data._dtype))
            w.last(1)

    def propagate_trans_st(self, stage_from: OOOOpPipelineStage, stage_to: OOOOpPipelineStage):
        """
        Propagate transaction state between two pipeline stages.
        """
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
        """
        Create all pipeline stages and connect them together.
        """
        P = self.PIPELINE_CONFIG
        self.pipeline = pipeline = [
            OOOOpPipelineStage(i, f"st{i:d}", self)
            for i in range(P.WAIT_FOR_WRITE_ACK + P.WRITE_HISTORY_SIZE + 1)
        ]

        state_read = self.state_array.port[1]
        self.collision_detector(pipeline)
        HAS_TRANS_ST = self.TRANSACTION_STATE_T is not None

        for i, dst_st in enumerate(pipeline):
            dst_st: OOOOpPipelineStage
            if i > 0:
                # if not first
                st_prev = pipeline[i - 1]
            else:
                st_prev = None

            if i < len(pipeline) - 1:
                # if not last
                st_next = pipeline[i + 1]
            else:
                st_next = None

            # :note: pipeline stages described in P enum
            if i == P.READ_DATA_RECEIVE:
                # :note: we can not apply forward write data there because we do not know the original address yet
                r = self.m.r
                state_read.addr(r.id)
                dst_st.addr = state_read.dout[self.MAIN_STATE_INDEX_WIDTH:]
                if HAS_TRANS_ST:
                    low = self.MAIN_STATE_INDEX_WIDTH
                    dst_st.transaction_state = state_read.dout[:low]._reinterpret_cast(self.TRANSACTION_STATE_T)

                dst_st.in_valid(r.valid & r.last)
                r.ready(dst_st.in_ready)
                dst_st.out_ready(st_next.in_ready)
                state_read.en(dst_st.load_en)

                self.data_load(r, dst_st)

            elif i <= P.STATE_LOAD:
                If(dst_st.load_en,
                    dst_st.id(st_prev.id),
                    dst_st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, dst_st),
                )
                # update the data to a latest value from all successor stages
                self.apply_data_write_forwarding(dst_st, dst_st.load_en)
                dst_st.in_valid(st_prev.out_valid)
                dst_st.out_ready(st_next.in_ready)

            elif i == P.WRITE_BACK:
                # :note: the data in this stage is waiting to be written and leaves this stage after it was written
                If(dst_st.load_en,
                    dst_st.id(st_prev.id),
                    dst_st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, dst_st),
                )
                # Because the previous value of this registr could have been resolved
                # to be also colliding we need to check it. We can safely check just the collision
                # with next stage because forwarding is not blocking and will update the current stage if not stalling
                # or if stalling the previous stage (our inputs) will be updated.
                self.apply_data_write_forwarding(dst_st, dst_st.load_en, self.main_op)
                aw = self.m.aw
                w = self.m.w

                cancel = rename_signal(self, self.write_cancel(dst_st), "write_back_cancel")
                dst_st.in_valid(st_prev.out_valid)

                w_first_data_word = self._reg("w_first_data_word", def_val=1)
                # this stage has to have data, last word must wait on next stage ready
                w_channel_en = dst_st.valid & (st_next.in_ready | ~w.last) & ~cancel
                w_channel_ack = (w.valid & w.ready & w.last) | cancel
                dst_st.out_valid = dst_st.valid & w_channel_ack
                dst_st.out_ready(st_next.in_ready & w_channel_ack)
                w_sync = StreamNode(
                    [], [aw, w],
                    extraConds={
                        aw: w_channel_en & w_first_data_word,
                        w: w_channel_en
                    },
                    skipWhen={
                        aw:cancel | ~w_first_data_word,
                        w:cancel,
                    }
                )
                w_sync.sync()

                self._axi_addr_defaults(aw)
                aw.id(dst_st.id)
                aw.addr(Concat(dst_st.addr, Bits(self.ADDR_OFFSET_W).from_py(0)))

                st_data = dst_st.data
                w_ack = w_sync.ack() & w_channel_en
                If(w_ack,
                   w_first_data_word(w.last)
                )
                self.data_store(st_data, w, w_ack)

            elif i > P.WRITE_BACK and i != P.WAIT_FOR_WRITE_ACK:
                # just pass data between WRITE_BACK -> WAIT_FOR_WRITE_ACK and WAIT_FOR_WRITE_ACK -> end of write history
                dst_st.in_valid(st_prev.out_valid)
                if i > P.WAIT_FOR_WRITE_ACK:
                    # this is a last stage, we need to consume the item only if there is some new
                    dst_st.out_ready(pipeline[P.WAIT_FOR_WRITE_ACK].out_valid)
                else:
                    assert i > P.WRITE_BACK, i
                    assert i < P.WAIT_FOR_WRITE_ACK, i
                    # next is ready to accept data or this stage has no data
                    dst_st.out_ready(st_next.in_ready | ~dst_st.valid)

                If(dst_st.load_en,
                   dst_st.id(st_prev.id),
                   dst_st.addr(st_prev.addr),
                   dst_st.data(st_prev.data),
                   self.propagate_trans_st(st_prev, dst_st),
                )

            elif i == P.WAIT_FOR_WRITE_ACK:
                If(dst_st.load_en,
                    dst_st.id(st_prev.id),
                    dst_st.addr(st_prev.addr),
                    self.propagate_trans_st(st_prev, dst_st),
                    dst_st.data(st_prev.data),
                )
                dout = self.dataOut
                b = self.m.b
                confirm = self.ooo_fifo.read_confirm
                cancel = rename_signal(self, self.write_cancel(dst_st), "wait_for_ack_cancel")

                # ommiting st_next.ready as there is no next
                w_ack_node = StreamNode(
                    [b],
                    [dout, confirm],
                    extraConds={
                        dout: dst_st.valid,
                        b: dst_st.valid & ~cancel,
                        confirm: dst_st.valid,
                    },
                    skipWhen={
                        b: dst_st.valid & cancel,
                    }
                )
                w_ack_node.sync()
                dst_st.in_valid(st_prev.out_valid)
                dst_st.out_ready((b.valid | cancel) & dout.rd & confirm.rd & dout.rd)
                dst_st.out_valid = dst_st.valid & b.valid & dout.rd & confirm.rd & dout.rd

                dout.addr(dst_st.addr)
                dout.data(dst_st.data)
                if HAS_TRANS_ST:
                    dout.transaction_state(dst_st.transaction_state)

                confirm.data(dst_st.id)
            else:
                raise NotImplementedError("Unknown stage of pipeline")

    def _impl(self):
        self.ar_dispatch()
        self.main_pipeline()
        propagateClkRstn(self)
