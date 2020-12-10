from typing import NamedTuple

from hwt.hdl.types.bits import Bits
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, HandshakeSync
from hwt.interfaces.structIntf import HdlType_to_Interface
from hwt.synthesizer.param import Param
from hwtLib.types.ctypes import uint8_t
from pycocotb.hdlSimulator import HdlSimulator
from hwt.synthesizer.interface import Interface


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

    def __init__(self, index, name: str, parent: "OutOfOrderCummulativeOp"):
        self.index = index
        self.name = name
        r = parent._reg
        self.id = r("%s_id" % name, parent.m.ar.id._dtype)
        self.addr = r("%s_addr" % name, Bits(parent.MAIN_STATE_INDEX_WIDTH))

        if parent.TRANSACTION_STATE_T is not None:
            self.transaction_state = r("%s_transaction_state" % name, parent.TRANSACTION_STATE_T)
        self.data = r("%s_data" % name, parent.MAIN_STATE_T)

        self.valid = r("%s_valid" % name, def_val=0)
        self.ready = parent._sig("%s_ready" % name)
        self.load_en = parent._sig("%s_load_en" % name)

        # :note: constructed later
        self.collision_detect = None

    def __repr__(self):
        return "<%s %s 0x%x>" % (self.__class__.__name__, self.name, id(self))


def does_collinde(st0: OOOOpPipelineStage, st1: OOOOpPipelineStage):
    if st0 is None or st1 is None:
        # to cover the ends of pipeline where next/prev stage does not exists
        return 0

    return st0.valid & st1.valid & st0.addr._eq(st1.addr)


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
    WAIT_FOR_WRITE_ACK : int
    # data which was written in to main memory, used to udate
    # the data which was read in that same time
    WRITE_HISTORY: int

    WRITE_HISTORY_SIZE: int

    @classmethod
    def new_config(cls, WRITE_HISTORY_SIZE=4):
        READ_DATA_RECEIVE = 0
        STATE_LOAD = READ_DATA_RECEIVE + 2
        WRITE_BACK = STATE_LOAD + 1
        WAIT_FOR_WRITE_ACK = WRITE_BACK + 1
        WRITE_HISTORY = WAIT_FOR_WRITE_ACK

        return cls(
            READ_DATA_RECEIVE,
            STATE_LOAD,
            WRITE_BACK,
            WAIT_FOR_WRITE_ACK,
            WRITE_HISTORY,
            WRITE_HISTORY_SIZE
        )


class OutOfOrderCummulativeOpIntf(Handshaked):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.TRANSACTION_STATE_T = Param(uint8_t)
        self.MAIN_STATE_T = Param(uint8_t)
        self.MAIN_STATE_INDEX_WIDTH = Param(8)

    def _declr(self):
        self.addr = VectSignal(self.MAIN_STATE_INDEX_WIDTH)
        if self.MAIN_STATE_T is not None:
            self.data = HdlType_to_Interface(self.MAIN_STATE_T)
        if self.TRANSACTION_STATE_T is not None:
            self.transaction_state = HdlType_to_Interface(self.TRANSACTION_STATE_T)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = OutOfOrderCummulativeOpIntfAgent(sim, self)


class OutOfOrderCummulativeOpIntfAgent(HandshakedAgent):
    """
    :note: if TRANSACTION_STATE_T is None the data should be only int for address
        else data should be tuple of int for address and a value of the state
        state value depends on state type, for simple bit vector it is just int,
        for struct it is tuple, ...
    """

    def __init__(self, sim:HdlSimulator, intf: OutOfOrderCummulativeOpIntf, allowNoReset=False):
        HandshakedAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)
        if intf.TRANSACTION_STATE_T is not None:
            t_st = intf.transaction_state
            t_st._initSimAgent(sim)
            self.t_st_is_primitive = not isinstance(t_st, Interface)

        if intf.MAIN_STATE_T is not None:
            m_st = intf.data
            m_st._initSimAgent(sim)
            self.m_st_is_primitive = not isinstance(m_st, Interface)

    def getDrivers(self):
        yield from HandshakedAgent.getDrivers(self)
        if self.intf.TRANSACTION_STATE_T is not None:
            yield from self.intf.transaction_state._ag.getDrivers()

    def getMonitors(self):
        yield from HandshakedAgent.getMonitors(self)
        if self.intf.TRANSACTION_STATE_T is not None:
            yield from self.intf.transaction_state._ag.getMonitors()

    def get_data(self):
        i = self.intf

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

    def set_data(self, d):
        i = self.intf

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

