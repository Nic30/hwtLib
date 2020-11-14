#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from hwt.code import If, log2ceil, Concat, connect, SwitchLogic
from hwt.hdl.constants import WRITE, READ
from hwt.hdl.typeShortcuts import vec
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi_comp.lsu.fifo_oooread import FifoOutOfOrderRead
from hwtLib.amba.constants import BURST_INCR, PROT_DEFAULT, BYTES_IN_TRANS, \
    LOCK_DEFAULT, CACHE_DEFAULT, QOS_DEFAULT
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.mem.ram import RamSingleClock
from hwtLib.types.ctypes import uint8_t, uint32_t
from pyMathBitPrecise.bit_utils import mask


class OOOOpPrototypePipelineStage():
    """
    :ivar id: an id of an axi transaction (and index of item in state_array)
    :ivar addr: an address which is beeing processed in this stage
    :ivar state: state loaded from the state_array (current meta state)
    :ivar data: currently loaded data from the bus
    :ivar valid: validity flag for whole stage
    :ivar ready: if 1 the stage can recieve data on next clock edge, otherwise
        the stage stalls
    :ivar collision_detect: the list of flags (sotored in register) if flag is 1
        it means that the value should be updated from stage on that index
    :ivar load_en: if 1 the stage will load the data from previous stage
        in this clock cycle
    """

    def __init__(self, name: str, parent: "OOOOpPrototype"):
        self.name = name
        r = parent._reg
        self.id = r("%s_id" % name, parent.m.ar.id._dtype)
        self.addr = r("%s_addr" % name, Bits(parent.COUNTER_ARRAY_INDEX_WIDTH))

        self.transaction_state = r("%s_transaction_state" % name, parent.STATE_T)
        self.data = r("%s_data" % name, parent.m.r.data._dtype)

        self.valid = r("%s_valid" % name, def_val=0)
        self.ready = parent._sig("%s_ready" % name)
        self.load_en = parent._sig("%s_load_en" % name)

        # :note: constructed later
        self.collision_detect = None

    def __repr__(self):
        return "<%s %s 0x%x>" % (self.__class__.__name__, self.name, id(self))


class OOOOpPrototype(Unit):
    """
    This is a component template for cumulative Out of Order operations with hihgh latency AXI.
    Suitable for counter arrays, hash tables and other data structures which are acessing data randomly
    and potential collision due read-modify-write operations may occure.
    
    This component stores info about currently executed memory transactions which may be finished out of order.
    Potential memory access colisions are solved by bypasses in main pipeline.
    In order to compensate for memory write latency the write history is utilised.
    The write history is a set of registers on the end of the pipeline.
    
    Note that the write history is not meant as a main mechanism for write latency compensation.
    It is meant to be used for 3-4 items to componsate for latency of the cache/LSU.

    If the main operation requires multiple clock cycles the operation is performed speculatively.
    
    The most up-to-date version of the data is always selected on the input of WRITE_BACK stage.
    
    :ivar STATE_T: a type of the state in main memory which is being updated by this component
    :ivar TRANSACTION_STATE_T: a type of the transaction state, used to store additional data
        for transaction and can be used to modify the behavior of the pipeline
    """

    class PIPELINE_REG():
        # first stage of the pipeline, actually does not have registers
        # but the signals are directly connected to inputs instead
        READ_DATA_RECEIVE = 0
        # read state from state array, read was executed in previous step
        STATE_LOAD = READ_DATA_RECEIVE + 2
        
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
        self.STATE_T = Param(uint32_t)
        self.TRANSACTION_STATE_T = Param(uint8_t)
        Axi4._config(self)

    def _declr(self):
        addClkRstn(self)
        # constant precomputation
        self.COUNTER_ARRAY_ITEMS_CNT = (2 ** self.ADDR_WIDTH) // (self.STATE_T.bit_length() // 8)
        self.COUNTER_ARRAY_INDEX_WIDTH = log2ceil(self.COUNTER_ARRAY_ITEMS_CNT - 1)
        self.ADDR_OFFSET_W = log2ceil(self.STATE_T.bit_length() // 8 - 1)
        
        # index of the item to increment
        self.dataIn = Handshaked()
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
        
        dataIn_reg = HandshakedReg(din.__class__)
        dataIn_reg._updateParamsFrom(din)
        self.dataIn_reg = dataIn_reg
        StreamNode(
            [din],
            [dataIn_reg.dataIn, ooo_fifo.write_confirm]
        ).sync()
        connect(din, dataIn_reg.dataIn, exclude=[din.rd, din.vld])
        
        ar_node = StreamNode(
            [dataIn_reg.dataOut, ooo_fifo.read_execute],
            [ar]
        )
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

    def collision_detector(self, pipeline: List[OOOOpPrototypePipelineStage]) -> List[List[RtlSignal]]:
        """
        Search for address access collisions in pipeline and store the result of colision check to registers for
        data write bypass in next clock tick
        """
        PIPELINE_REG = self.PIPELINE_REG
        def does_collinde(st0: OOOOpPrototypePipelineStage, st1: OOOOpPrototypePipelineStage):
            if st0 is None or st1 is None:
                # to cover the ends of pipeline where next/prev stage does not exists 
                return 0

            return st0.valid & st1.valid & st0.addr._eq(st1.addr)

        for dst_i, dst in enumerate(pipeline):
            # construct colision detector flags
            dst.collision_detect = [
                0
                # because we do not know the address in first stage
                # and write history stages do not require an update
                if (dst_i <= 1 or
                    src_i < PIPELINE_REG.WRITE_BACK or
                    dst_i >= PIPELINE_REG.WRITE_BACK or
                    src_i == dst_i)
                else
                self._reg("%s_collision_detect_from_%d" % (dst.name, src_i), def_val=0)

                for src_i in range(len(pipeline))
            ]
            
            if dst_i <= 1:
                # because we do not know the address in first stage
                continue
            elif dst_i >= PIPELINE_REG.WRITE_BACK:
                # we can not update write history
                break

            dst_prev = pipeline[dst_i - 1] if dst_i > 1 else None

            # for each stage which can potentially update a data in this stage
            for src_i in range(PIPELINE_REG.WRITE_BACK, len(pipeline)):
                if src_i == dst_i:
                    # disallow to load  data from WRITE_BACK to WRITE_BACK on stall 
                    continue

                src = pipeline[src_i] if src_i > 0 else None
                src_prev = pipeline[src_i - 1] if src_i > 1 else None

                cd = dst.collision_detect[src_i]
                c = self._sig("%s_tmp" % cd.name)
                # Resolve if src stage should load from dst stage in next clock cycle
                SwitchLogic([
                    (~dst.load_en & ~src.load_en,
                       c(does_collinde(dst, src))
                    ),
                    (~dst.load_en & src.load_en,
                       c(does_collinde(dst, src_prev))
                    ),
                    (dst.load_en & ~src.load_en,
                       c(does_collinde(dst_prev, src))
                    ),
                    (dst.load_en & src.load_en,
                       c(does_collinde(dst_prev, src_prev))
                    )],
                    default=c(0))
                #print(dst_i, src_i)
                cd(c & dst.valid.next)
    
    def apply_write_bypass(self, st_i: int, pipeline: OOOOpPrototypePipelineStage,
                           st_load_en: RtlSignal,
                           data_modifier=lambda x: x):
        """
        :param st_collision_detect: in format stages X pipeline[WRITE_BACK-1:], if bit = 1 it means
            that the stage data should be updated from stage on that index
        """
        st = pipeline[st_i]
        st_prev = pipeline[st_i - 1]
        
        def is_not_0(sig):
            return not (isinstance(sig, int) and sig == 0)
        
        res = SwitchLogic([
                (
                    (st_load_en & st_prev.collision_detect[src_i]) |
                    (~st_load_en & st.collision_detect[src_i]),
                    # use bypass instead of data from previous stage 
                    [st.data(data_modifier(src_st.data)), ]
                )
                for src_i, src_st in enumerate(pipeline) if (
                        # filter out stage combinations which do not have bypass
                        is_not_0(st.collision_detect[src_i]) or
                        is_not_0(st_prev.collision_detect[src_i])
                    )
            ],
            If(st_load_en,
               st.data(data_modifier(st_prev.data)),
            )
        )
        
        return res
       
    def main_pipeline(self):
        PIPELINE_REG = self.PIPELINE_REG
        pipeline = [
            OOOOpPrototypePipelineStage("st%d" % i, self)
            for i in range(PIPELINE_REG.WRITE_HISTORY + PIPELINE_REG.WRITE_HISTORY_SIZE)
        ]
        
        state_read = self.state_array.port[1]
        self.collision_detector(pipeline)
        for i, st in enumerate(pipeline):
            if i > 0:
                st_prev = pipeline[i - 1]
                st_load_en = st_prev.valid & st.ready

            if i < len(pipeline) - 1:
                st_next = pipeline[i + 1]

            # :note: pipeline stages described in PIPELINE_REG enum
            if i == PIPELINE_REG.READ_DATA_RECEIVE:
                # :note: we can not apply bypass there because we do not know the original address yet
                r = self.m.r
                state_read.addr(r.id)
                st.addr = state_read.dout[self.COUNTER_ARRAY_INDEX_WIDTH:]
                st.transaction_state = state_read.dout[:self.COUNTER_ARRAY_INDEX_WIDTH]

                st.ready = r.ready
                st.ready(~st.valid | st_next.ready)
                If(r.valid,
                   st.valid(1)
                ).Elif(st.ready,
                   st.valid(0)
                )
                st.load_en(r.valid & st.ready)
                state_read.en(st.load_en)
                If(st.load_en,
                    st.id(r.id),
                    st.data(r.data),
                )

            elif i <= PIPELINE_REG.STATE_LOAD:
                st.load_en(st_load_en)
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    st.transaction_state(st_prev.transaction_state),
                )
                self.apply_write_bypass(i, pipeline, st_load_en)
                If(st_prev.valid,
                   st.valid(1)
                ).Elif(st_next.ready,
                   st.valid(0)
                )
                st.ready(~st.valid | st_next.ready)

            elif i == PIPELINE_REG.WRITE_BACK:
                st.load_en(st_load_en)
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
                    st.transaction_state(st_prev.transaction_state),
                )
                self.apply_write_bypass(i, pipeline, st_load_en, lambda x: x + 1)
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
                st.load_en(st_load_en)
                If(st.load_en,
                    st.id(st_prev.id),
                    st.addr(st_prev.addr),
    
                    st.transaction_state(st_prev.transaction_state),
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
                st.ready = st_prev.valid & st_prev.ready

                st.load_en(st_prev.valid & st_prev.ready)
                If(st.load_en,
                   st.addr(st_prev.addr),
                   st.data(st_prev.data),
                   st.valid(st_prev.valid)
                )


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
