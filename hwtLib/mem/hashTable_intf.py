from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, VectSignal, Signal, HandshakeSync
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class InsertIntfAgent(HandshakedAgent):
    """
    Simulation agent for `.InsertIntf` interface

    data format:
        * if interface has data signal,
          data format is tuple (hash, key, data, vldFlag)
        * if interface does not have data signal,
          data format is tuple (hash, key, vldFlag)
    """
    def __init__(self, sim: HdlSimulator, intf: "InsertIntf"):
        HandshakedAgent.__init__(self, sim, intf)
        self.hasData = bool(intf.DATA_WIDTH)

    def get_data(self):
        i = self.intf
        _hash = i.hash.read()
        key = i.key.read()
        vldFlag = i.vldFlag.read()

        if self.hasData:
            data = i.data.read()
            return hash, key, data, vldFlag
        else:
            return hash, key, vldFlag

    def set_data(self, data):
        i = self.intf

        if data is None:
            i.hash.write(None)
            i.key.write(None)
            if self.hasData:
                i.data.write(None)
            i.vldFlag.write(None)
        else:
            if self.hasData:
                _hash, key, _data, vldFlag = data
                i.data.write(_data)
            else:
                _hash, key, vldFlag = data

            i.hash.write(_hash)
            i.key.write(key)
            i.vldFlag.write(vldFlag)


class InsertIntf(HandshakeSync):
    def _config(self):
        self.HASH_WIDTH = Param(8)
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)

    def _declr(self):
        super(InsertIntf, self)._declr()
        self.hash = VectSignal(self.HASH_WIDTH)
        self.key = VectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)

        self.vldFlag = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = InsertIntfAgent(sim, self)


class LookupKeyIntfAgent(HandshakedAgent):
    """
    Simulation agent for LookupKeyIntf interface
    """
    def __init__(self, sim: HdlSimulator, intf: "LookupKeyIntf"):
        HandshakedAgent.__init__(self, sim, intf)
        self.HAS_LOOKUP_ID = bool(intf.LOOKUP_ID_WIDTH)

    def get_data(self):
        intf = self.intf
        if self.HAS_LOOKUP_ID:
            return intf.lookup_id.read(), intf.key.read()
        return intf.key.read()

    def set_data(self, data):
        intf = self.intf
        if self.HAS_LOOKUP_ID:
            _id, _key = data
            return intf.lookup_id.write(_id), intf.key.write(_key)

        self.intf.key.write(data)


class LookupKeyIntf(HandshakeSync):
    def _config(self):
        self.LOOKUP_ID_WIDTH = Param(0)
        self.KEY_WIDTH = Param(8)

    def _declr(self):
        HandshakeSync._declr(self)
        if self.LOOKUP_ID_WIDTH:
            self.lookupId = VectSignal(self.LOOKUP_ID_WIDTH)
        self.key = VectSignal(self.KEY_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = LookupKeyIntfAgent(sim, self)


class LookupResultIntfAgent(HandshakedAgent):
    """
    Simulation agent for `.LookupResultIntf`
    data is stored in .data
    data format is tuple (hash, key, data, found) but some items
    can be missing depending on configuration of interface
    """
    def __init__(self, sim, intf):
        HandshakedAgent.__init__(self, sim, intf)
        self.hasHash = bool(intf.LOOKUP_HASH)
        self.hasKey = bool(intf.LOOKUP_KEY)
        self.hasData = bool(intf.DATA_WIDTH)

    def get_data(self):
        d = []
        append = d.append
        intf = self.intf

        if self.hasHash:
            append(intf.hash.read())

        if self.hasKey:
            append(intf.key.read())

        if self.hasData:
            append(intf.data.read())

        append(intf.found.read())
        append(intf.occupied.read())

        return tuple(d)

    def set_data(self, data):
        intf = self.intf

        dIt = iter(data)

        if self.hasHash:
            intf.hash.write(next(dIt))

        if self.hasKey:
            intf.key.write(next(dIt))

        if self.hasData:
            intf.data.write(next(dIt))

        intf.found.write(next(dIt))
        intf.occupied.write(next(dIt))

        try:
            next(dIt)
            raise AssertionError("To many items in data %r" % data)
        except IndexError:
            return


class LookupResultIntf(Handshaked):
    """
    Interface for result of lookup in hash table

    :ivar HASH_WIDTH: width of the hash used by hash table
    :ivar KEY_WIDTH: width of the key used by hash table
    :ivar LOOKUP_HASH: flag if this interface should have hash signal
    :ivar LOOKUP_KEY: flag if this interface should have hash signal

    :ivar hash: hash for this key (= index in this table)
    :ivar key: original key which was searched for
    :ivar data: data under this key
    :ivar occupied: flag which tells if there is an valid item under this key
    """
    def _config(self):
        self.HASH_WIDTH = Param(8)
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)
        self.LOOKUP_ID_WIDTH = Param(0)
        self.LOOKUP_HASH = Param(False)
        self.LOOKUP_KEY = Param(False)

    def _declr(self):
        HandshakeSync._declr(self)
        if self.LOOKUP_ID_WIDTH:
            self.lookupId = VectSignal(self.LOOKUP_ID_WIDTH)

        if self.LOOKUP_HASH:
            self.hash = VectSignal(self.HASH_WIDTH)

        if self.LOOKUP_KEY:
            self.key = VectSignal(self.KEY_WIDTH)

        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)

        self.found = Signal()
        self.occupied = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = LookupResultIntfAgent(sim, self)
