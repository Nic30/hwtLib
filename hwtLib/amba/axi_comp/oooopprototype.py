#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwt.code import If, log2ceil, Concat, connect, SwitchLogic
from hwt.hdl.constants import WRITE, READ
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4, Axi4_r, Axi4_addr
from hwtLib.amba.axi_comp.lsu.fifo_oooread import FifoOutOfOrderRead
from hwtLib.amba.constants import BURST_INCR, PROT_DEFAULT, BYTES_IN_TRANS, \
    LOCK_DEFAULT, CACHE_DEFAULT, QOS_DEFAULT
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtLib.types.ctypes import uint64_t
from pyMathBitPrecise.bit_utils import mask, apply_set_and_clear
from typing import List

    
class OOOOpPrototype(Unit):

    class Stage():
        """
        :ivar id: an id of an axi transaction (and index of item in state_array)
        :ivar addr: an address which is beeing processed in this stage
        :ivar state: state loaded from the state_array (current meta state)
        :ivar data: currently loaded data from the bus
        :ivar accumulator: stacked update of the data
        :ivar valid: validity flag for whole stage
        :ivar ready: if 1 the stage can recieve data on next clock edge, otherwise
            the stage stalls
        """

        def __init__(self, name: str, parent: Unit):
            self.name = name
            r = parent._reg
            self.id = r("%s_id" % name, parent.m.ar.id._dtype)
            self.addr = r("%s_addr" % name, Bits(parent.COUNTER_ARRAY_INDEX_WIDTH))

            self.state = r("%s_state" % name, parent.STATE_T)
            self.data = r("%s_data" % name, parent.m.r.data._dtype)
            self.accumulator = r("%s_accumulator" % name, parent.m.r.data._dtype)

            self.valid = r("%s_valid" % name, def_val=0)
            self.ready = parent._sig("%s_ready" % name)

        def __repr__(self):
            return "<%s %s 0x%x>" % (self.__class__.__name__, self.name, id(self))

    class PIPELINE_REG():
        # first stage of the pipeline, actually does not have registers
        # but the signals are directly connected to inputs instead
        READ_DATA_RECEIVE = 0
        # read state from state array, read was executed in previous step
        STATE_LOAD = READ_DATA_RECEIVE + 1
        # initiate write to main memory
        WRITE_BACK = STATE_LOAD + 1  # aw+w in first clock rest of data later
        # wait until the write acknowledge is received and block the pipeline if it is not and
        # previous stage has valid data 
        # consume item from ooo_fifo in last beat of incomming data
        WAIT_FOR_WRITE_ACK = WRITE_BACK + 1
        # data which was written in to main memory, used to udate
        # the data which was read in that same time
        WRITE_HISTORY = WAIT_FOR_WRITE_ACK

        WRITE_HISTORY_SIZE = 4

    def _config(self):
        # number of items in main array is resolved from ADDR_WIDTH and size of STATE_T
        # number of concurent thread is resolved as 2**ID_WIDTH
        self.MAX_OP_DELAY = Param(4)
        self.STATE_T = Param(uint64_t)
        Axi4._config(self)

    def _declr(self) -> None:
        addClkRstn(self)
        # index of the item to increment
        self.dataIn = Handshaked()
        self.COUNTER_ARRAY_ITEMS_CNT = (2 ** self.ADDR_WIDTH) // (self.STATE_T.bit_length() // 8)
        self.COUNTER_ARRAY_INDEX_WIDTH = log2ceil(self.COUNTER_ARRAY_ITEMS_CNT - 1)
        self.ADDR_OFFSET_W = log2ceil(self.STATE_T.bit_length() // 8 - 1)
        self.dataIn.DATA_WIDTH = self.COUNTER_ARRAY_INDEX_WIDTH
        # last value of the counter
        self.dataOut = Handshaked()._m()
        self.dataOut.DATA_WIDTH = self.STATE_T.bit_length()

        with self._paramsShared():
            self.m = Axi4()._m()
            self.ooo_fifo = FifoOutOfOrderRead()
            self.ooo_fifo.ITEMS = 2 ** self.ID_WIDTH

        sa = self.state_array = RamSingleClock()
        sa.PORT_CNT = (WRITE, READ)
        sa.ADDR_WIDTH = self.ID_WIDTH
        sa.DATA_WIDTH = self.STATE_T.bit_length() + self.dataIn.DATA_WIDTH

    def _axi_addr_defaults(self, a: Axi4_addr, words: int):
        a.len(words - 1)
        a.burst(BURST_INCR)
        a.prot(PROT_DEFAULT)
        a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))
        a.lock(LOCK_DEFAULT)
        a.cache(CACHE_DEFAULT)
        a.qos(QOS_DEFAULT)
    
    def ar_dispatch(self):
        ooo_fifo = self.ooo_fifo
        ar = self.m.ar
        din = self.dataIn
        
        dataIn_reg = HandshakedReg(din.__class__)
        dataIn_reg._updateParamsFrom(din)
        self.dataIn_reg = dataIn_reg
        StreamNode([din], [dataIn_reg.dataIn, ooo_fifo.write_confirm]).sync()
        connect(din, dataIn_reg.dataIn, exclude=[din.rd, din.vld])
        
        ar_node = StreamNode([dataIn_reg.dataOut, ooo_fifo.read_execute], [ar])
        ar_node.sync()

        din_data = dataIn_reg.dataOut.data
        state_arr = self.state_array
        state_write = state_arr.port[0]
        state_write.en(ar_node.ack())
        state_write.addr(ooo_fifo.read_execute.index)
        state_write.din(Concat(self.STATE_T.from_py(0), din_data))

        ar.id(ooo_fifo.read_execute.index)
        ar.addr(Concat(din_data[self.COUNTER_ARRAY_INDEX_WIDTH:], vec(0, self.ADDR_OFFSET_W)))
        self._axi_addr_defaults(ar, 1)
    
    def apply_write_bypass(self, st: "Stage", st_prev: "Stage", ack: RtlSignal, bypass_from: List["Stage"], data_modifier=lambda x: x):
        res = \
        If(ack,
            SwitchLogic(
                [
                    (
                        confirmed_st.valid & st_prev.valid & st_prev.addr._eq(confirmed_st.addr),
                        # use bypass instead of from previous stage 
                        [st.data(data_modifier(confirmed_st.data)), ]
                    )
                    for confirmed_st in bypass_from
                ],
                st.data(data_modifier(st_prev.data)),
            )
        )
        
        if st not in bypass_from:
            # this condition is meet only for a write state, there value of input may be bypassed
            # but the value in this stage can not be updated because it is already feed to memory
            res.Else(
                SwitchLogic([
                        (
                            confirmed_st.valid & st_prev.valid & st.addr._eq(confirmed_st.addr),
                            # replace current data from bypass
                            [st.data(data_modifier(confirmed_st.data)), ]
                        )
                    for confirmed_st in bypass_from
                ])
            )
        
        return res

    def main_pipeline(self):
        PIPELINE_REG = self.PIPELINE_REG
        pipeline = [
            self.Stage("reg%d" % i, self)
            for i in range(PIPELINE_REG.WRITE_HISTORY + PIPELINE_REG.WRITE_HISTORY_SIZE)
        ]
        
        state_read = self.state_array.port[1]
        bypass_from = pipeline[PIPELINE_REG.WRITE_BACK:]

        for i, st in enumerate(pipeline):
            if i > 0:
                st_prev = pipeline[i - 1]
                ack = st_prev.valid & st.ready

            if i < len(pipeline) - 1:
                st_next = pipeline[i + 1]

            # bypass_to = i > 0 and i < PIPELINE_REG.WAIT_FOR_WRITE_ACK
            if i == PIPELINE_REG.READ_DATA_RECEIVE:
                r = self.m.r
                state_read.addr(r.id)
                
                st.addr = state_read.dout[self.COUNTER_ARRAY_INDEX_WIDTH:]
                st.state = state_read.dout[:self.COUNTER_ARRAY_INDEX_WIDTH]
                st.accumulator = 1

                st.ready = r.ready
                st.ready(~st.valid | st_next.ready)
                If(r.valid,
                   st.valid(1)
                ).Elif(st.ready,
                   st.valid(0)
                )
                ack = r.valid & st.ready

                state_read.en(ack)
                If(ack,
                    st.id(r.id),
                    st.data(r.data),
                )

            elif i == PIPELINE_REG.STATE_LOAD:
                If(ack,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    st.accumulator(st_prev.accumulator),
                    st.state(st_prev.state),
                )
                self.apply_write_bypass(st, st_prev, ack, bypass_from)
                If(st_prev.valid,
                   st.valid(1)
                ).Elif(st_next.ready,
                   st.valid(0)
                )
                st.ready(~st.valid | st_next.ready)

            elif i == PIPELINE_REG.WRITE_BACK:
                If(ack,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    st.accumulator(st_prev.accumulator),
                    st.state(st_prev.state),
                )
                self.apply_write_bypass(st, st_prev, ack, bypass_from, lambda x: x + st_prev.accumulator)
                aw = self.m.aw
                w = self.m.w
                
                If(st_prev.valid,
                   st.valid(1)
                ).Elif(st_next.ready & aw.ready & w.ready,
                   st.valid(0)
                )
                
                st.ready(~st.valid | (aw.ready & w.ready & st_next.ready))

                StreamNode(
                    [], [aw, w],
                    extraConds={
                        aw: st.valid & st_next.ready,
                        w: st.valid & st_next.ready
                    }
                ).sync()

                self._axi_addr_defaults(aw, 1)
                aw.id(st.id)
                aw.addr(Concat(st.addr, vec(0, self.ADDR_OFFSET_W)))

                w.data(st.data)
                w.strb(mask(self.DATA_WIDTH // 8))
                w.last(1)

            elif i == PIPELINE_REG.WAIT_FOR_WRITE_ACK:
                If(ack,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
    
                    st.state(st_prev.state),
                    st.accumulator(st_prev.accumulator),
                    st.data(st_prev.data),
                )
                dout = self.dataOut
                b = self.m.b
                confirm = self.ooo_fifo.read_confirm

                # ommiting st_next.ready as WRITE_HISTORY is always ready
                If(st_prev.valid & st_prev.ready,
                   st.valid(1)
                ).Elif(b.valid & dout.rd & confirm.rd,
                   st.valid(0)
                )
                
                st.ready(~st.valid | (b.valid & dout.rd & confirm.rd))

                StreamNode(
                    [b],
                    [dout, confirm],
                    extraConds={
                        dout: st.valid,
                        b: st.valid,
                        confirm: st.valid,
                    }
                ).sync()

                dout.data(st.data)
                confirm.data(b.id)

            elif i >= PIPELINE_REG.WRITE_HISTORY:
                ack = st_prev.valid & st_prev.ready
                If(ack,
                   st.addr(st_prev.addr),
                   st.data(st_prev.data),
                   st.valid(st_prev.valid)
                )
                st.ready = st_prev.ready

    def _impl(self):
        self.ar_dispatch()
        self.main_pipeline()
        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # u = _example_OutOfOrderCummulativeOp()
    u = OOOOpPrototype()
    u.ID_WIDTH = 2
    u.ADDR_WIDTH = 2 + 3
    u.DATA_WIDTH = u.STATE_T.bit_length()

    print(to_rtl_str(u))
