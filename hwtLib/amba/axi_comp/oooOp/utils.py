from typing import NamedTuple, Optional, List, Union

from hwt.code import If
from hwt.hdl.types.bits import HBits
from hwt.hwIO import HwIO
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.hwIOStruct import HdlType_to_HwIO
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIORdVldSync
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSyncSignal import RtlSyncSignal
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.hdlSimulator import HdlSimulator


class OOOOpPipelineStage():
    """
    :ivar index: index of the register in pipeline
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

    def __init__(self, index, name: str, parent: "OutOfOrderCummulativeOp", has_transaction_state):
        self.index = index
        self.name = name
        r = parent._reg
        self.id = r(f"{name:s}_id", parent.m.ar.id._dtype)
        self.addr = r(f"{name:s}_addr", HBits(parent.MAIN_STATE_INDEX_WIDTH))

        if has_transaction_state and parent.TRANSACTION_STATE_T is not None:
            # data private to an algorim of the pipeline
            self.transaction_state = r(f"{name:s}_transaction_state", parent.TRANSACTION_STATE_T)

        # data loaded/store from/to main memory
        self.data = r(f"{name:s}_data", parent.MAIN_STATE_T)

        vld = self.valid = r(f"{name:s}_valid", def_val=0)
        self.out_valid = vld
        inVld = self.in_valid = parent._sig(f"{name:s}_in_valid")
        outRd = self.out_ready = parent._sig(f"{name:s}_out_ready")
        inRd = self.in_ready = parent._sig(f"{name:s}_in_ready")
        regs_we = self.load_en = parent._sig(f"{name:s}_load_en")

        If(self.valid,
            inRd(outRd),
            regs_we(inVld & outRd),
            If(outRd,
                vld(inVld)
            )
        ).Else(
            inRd(1),
            regs_we(inVld),
            vld(inVld),
        )

        # :note: constructed later
        self.collision_detect: Optional[List[Union[int, RtlSyncSignal]]] = None

    def __repr__(self):
        return f"<{self.__class__.__name__:s} {self.name:s} 0x{id(self):x}>"


class OutOfOrderCummulativeOpPipelineConfig(NamedTuple):
    # first stage of the pipeline, actually does not have registers
    # but the signals are directly connected to inputs instead
    READ_DATA_RECEIVE: int
    # read state from state array, read was executed in previous step
    STATE_LOAD: int

    # initiate write to main memory
    WRITE_BACK: int  # aw+w in first clock rest of data later
    # wait until the write acknowledge is received and block the pipeline if it is not and
    # previous stage has valid data
    # consume item from ooo_fifo in last beat of incomming data
    WAIT_FOR_WRITE_ACK: int
    # data which was written in to main memory, used to udate
    # the data which was read in that same time

    # nuber of stages between WRITE_BACK and WAIT_FOR_WRITE_ACK
    WRITE_HISTORY_SIZE: int

    @classmethod
    def new_config(cls,
                   WRITE_TO_WRITE_ACK_LATENCY: int,
                   WRITE_ACK_TO_READ_DATA_LATENCY: int):
        READ_DATA_RECEIVE = 0
        STATE_LOAD = READ_DATA_RECEIVE + 2
        WRITE_BACK = STATE_LOAD + 1
        WAIT_FOR_WRITE_ACK = WRITE_BACK + WRITE_TO_WRITE_ACK_LATENCY
        return cls(
            READ_DATA_RECEIVE,
            STATE_LOAD,
            WRITE_BACK,
            WAIT_FOR_WRITE_ACK,
            WRITE_ACK_TO_READ_DATA_LATENCY,
        )


class HwIOOutOfOrderCummulativeOp(HwIODataRdVld):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.TRANSACTION_STATE_T = HwParam(uint8_t)
        self.MAIN_STATE_T = HwParam(uint8_t)
        self.MAIN_STATE_INDEX_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.MAIN_STATE_INDEX_WIDTH)
        if self.MAIN_STATE_T is not None:
            self.data = HdlType_to_HwIO().apply(self.MAIN_STATE_T)
        if self.TRANSACTION_STATE_T is not None:
            self.transaction_state = HdlType_to_HwIO().apply(self.TRANSACTION_STATE_T)
        HwIORdVldSync.hwDeclr(self)

    @override
    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = HwIOOutOfOrderCummulativeOpAgent(sim, self)


class HwIOOutOfOrderCummulativeOpAgent(HwIODataRdVldAgent):
    """
    :note: if TRANSACTION_STATE_T is None the data should be only int for address
        else data should be tuple of int for address and a value of the state
        state value depends on state type, for simple bit vector it is just int,
        for struct it is tuple, ...
    """

    def __init__(self, sim:HdlSimulator, hwIO: HwIOOutOfOrderCummulativeOp, allowNoReset=False):
        HwIODataRdVldAgent.__init__(self, sim, hwIO, allowNoReset=allowNoReset)
        if hwIO.TRANSACTION_STATE_T is not None:
            t_st = hwIO.transaction_state
            t_st._initSimAgent(sim)
            self.t_st_is_primitive = not isinstance(t_st, HwIO)

        if hwIO.MAIN_STATE_T is not None:
            m_st = hwIO.data
            m_st._initSimAgent(sim)
            self.m_st_is_primitive = not isinstance(m_st, HwIO)

    @override
    def getDrivers(self):
        yield from HwIODataRdVldAgent.getDrivers(self)
        if self.hwIO.TRANSACTION_STATE_T is not None:
            yield from self.hwIO.transaction_state._ag.getDrivers()

    @override
    def getMonitors(self):
        yield from HwIODataRdVldAgent.getMonitors(self)
        if self.hwIO.TRANSACTION_STATE_T is not None:
            yield from self.hwIO.transaction_state._ag.getMonitors()

    @override
    def get_data(self):
        i = self.hwIO

        if i.TRANSACTION_STATE_T is not None:
            if i.MAIN_STATE_T is not None:
                return (
                    i.addr.read(),
                    i.data.read() if self.m_st_is_primitive else i.data._ag.get_data(),
                    i.transaction_state.read() if self.t_st_is_primitive else i.transaction_state._ag.get_data()
                )
            else:
                return (
                    i.addr.read(),
                    i.transaction_state.read() if self.t_st_is_primitive else i.transaction_state._ag.get_data()
                )
        elif i.MAIN_STATE_T is not None:
            return (
                i.addr.read(),
                i.data.read() if self.m_st_is_primitive else i.data._ag.get_data(),
            )
        else:
            return i.addr.read()

    @override
    def set_data(self, d):
        i = self.hwIO

        if i.TRANSACTION_STATE_T is not None:
            if i.MAIN_STATE_T is not None:
                if d is None:
                    a, m_st, t_st = None, None, None
                else:
                    a, m_st, t_st = d
                i.addr.write(a)
                if self.m_st_is_primitive:
                    i.data.write(m_st)
                else:
                    i.data._ag.set_data(m_st)

                if self.t_st_is_primitive:
                    i.transaction_state.write(t_st)
                else:
                    i.transaction_state._ag.set_data(t_st)

            else:
                if d is None:
                    a, t_st = None, None
                else:
                    a, t_st = d
                i.addr.write(a)
                if self.t_st_is_primitive:
                    i.transaction_state.write(t_st)
                else:
                    i.transaction_state._ag.set_data(t_st)

        elif i.MAIN_STATE_T is not None:
                a, m_st = d
                i.addr.write(a)
                if self.m_st_is_primitive:
                    i.data.write(m_st)
                else:
                    i.data._ag.set_data(m_st)
        else:
            a = d
            i.addr.write(a)

