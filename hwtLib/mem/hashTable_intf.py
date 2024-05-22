from hwt.hwIO import HwIO
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIOVectSignal, HwIOSignal, HwIORdVldSync
from hwt.hwParam import HwParam
from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class HwIOInsertAgent(HwIODataRdVldAgent):
    """
    Simulation agent for `.HwIOInsert` interface

    data format:
        * if interface has data signal,
          data format is tuple (hash, key, data, item_vld)
        * if interface does not have data signal,
          data format is tuple (hash, key, item_vld)
    """

    def __init__(self, sim: HdlSimulator, hwIO: "HwIOInsert"):
        HwIODataRdVldAgent.__init__(self, sim, hwIO)
        self.hasData = bool(hwIO.DATA_WIDTH)

    @override
    def get_data(self):
        i = self.hwIO
        _hash = i.hash.read()
        key = i.key.read()
        item_vld = i.item_vld.read()

        if self.hasData:
            data = i.data.read()
            return hash, key, data, item_vld
        else:
            return hash, key, item_vld

    @override
    def set_data(self, data):
        i = self.hwIO

        if data is None:
            i.hash.write(None)
            i.key.write(None)
            if self.hasData:
                i.data.write(None)
            i.item_vld.write(None)
        else:
            if self.hasData:
                _hash, key, _data, item_vld = data
                i.data.write(_data)
            else:
                _hash, key, item_vld = data

            i.hash.write(_hash)
            i.key.write(key)
            i.item_vld.write(item_vld)


class HwIOInsert(HwIORdVldSync):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.HASH_WIDTH = HwParam(8)
        self.KEY_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(0)

    @override
    def hwDeclr(self):
        super(HwIOInsert, self).hwDeclr()
        self.hash = HwIOVectSignal(self.HASH_WIDTH)
        self.key = HwIOVectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = HwIOVectSignal(self.DATA_WIDTH)

        self.item_vld = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOInsertAgent(sim, self)


class HwIOLookupKeyAgent(HwIODataRdVldAgent):
    """
    Simulation agent for HwIOLookupKey interface
    """

    def __init__(self, sim: HdlSimulator, hwIO: "HwIOLookupKey"):
        HwIODataRdVldAgent.__init__(self, sim, hwIO)
        self.HAS_LOOKUP_ID = bool(hwIO.LOOKUP_ID_WIDTH)

    @override
    def get_data(self):
        hwIO = self.hwIO
        if self.HAS_LOOKUP_ID:
            return hwIO.lookup_id.read(), hwIO.key.read()
        return hwIO.key.read()

    @override
    def set_data(self, data):
        hwIO = self.hwIO
        if self.HAS_LOOKUP_ID:
            _id, _key = data
            return hwIO.lookup_id.write(_id), hwIO.key.write(_key)

        self.hwIO.key.write(data)


class HwIOLookupKey(HwIORdVldSync):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.LOOKUP_ID_WIDTH = HwParam(0)
        self.KEY_WIDTH = HwParam(8)

    @override
    def hwDeclr(self):
        HwIORdVldSync.hwDeclr(self)
        if self.LOOKUP_ID_WIDTH:
            self.lookupId = HwIOVectSignal(self.LOOKUP_ID_WIDTH)
        self.key = HwIOVectSignal(self.KEY_WIDTH)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOLookupKeyAgent(sim, self)


class HwIOLookupResultAgent(HwIODataRdVldAgent):
    """
    Simulation agent for `.HwIOLookupResult`
    data is stored in .data
    data format is tuple (hash, key, data, found) but some items
    can be missing depending on configuration of interface
    """

    def __init__(self, sim, hwIO):
        HwIODataRdVldAgent.__init__(self, sim, hwIO)
        self.hasHash = bool(hwIO.LOOKUP_HASH)
        self.hasKey = bool(hwIO.LOOKUP_KEY)
        self.hasData = bool(hwIO.DATA_WIDTH)

    @override
    def get_data(self):
        d = []
        append = d.append
        hwIO = self.hwIO

        if self.hasHash:
            append(hwIO.hash.read())

        if self.hasKey:
            append(hwIO.key.read())

        if self.hasData:
            append(hwIO.data.read())

        append(hwIO.found.read())
        append(hwIO.occupied.read())

        return tuple(d)

    @override
    def set_data(self, data):
        hwIO = self.hwIO

        dIt = iter(data)

        if self.hasHash:
            hwIO.hash.write(next(dIt))

        if self.hasKey:
            hwIO.key.write(next(dIt))

        if self.hasData:
            hwIO.data.write(next(dIt))

        hwIO.found.write(next(dIt))
        hwIO.occupied.write(next(dIt))

        try:
            next(dIt)
            raise AssertionError(f"To many items in data {data}")
        except IndexError:
            return


class HwIOLookupResult(HwIODataRdVld):
    """
    HwIO for result of lookup in hash table

    :ivar ~.HASH_WIDTH: width of the hash used by hash table
    :ivar ~.KEY_WIDTH: width of the key used by hash table
    :ivar ~.LOOKUP_HASH: flag if this interface should have hash signal
    :ivar ~.LOOKUP_KEY: flag if this interface should have hash signal

    :ivar ~.hash: hash for this key (= index in this table)
    :ivar ~.key: original key which was searched for
    :ivar ~.data: data under this key
    :ivar ~.occupied: flag which tells if there is an valid item under this key

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.HASH_WIDTH = HwParam(8)
        self.KEY_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(0)
        self.LOOKUP_ID_WIDTH = HwParam(0)
        self.LOOKUP_HASH = HwParam(False)
        self.LOOKUP_KEY = HwParam(False)

    @override
    def hwDeclr(self):
        HwIORdVldSync.hwDeclr(self)
        if self.LOOKUP_ID_WIDTH:
            self.lookupId = HwIOVectSignal(self.LOOKUP_ID_WIDTH)

        if self.LOOKUP_HASH:
            self.hash = HwIOVectSignal(self.HASH_WIDTH)

        if self.LOOKUP_KEY:
            self.key = HwIOVectSignal(self.KEY_WIDTH)

        if self.DATA_WIDTH:
            self.data = HwIOVectSignal(self.DATA_WIDTH)

        self.found = HwIOSignal()
        self.occupied = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOLookupResultAgent(sim, self)


class HwIOHashTable(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ITEMS_CNT = HwParam(32)
        self.KEY_WIDTH = HwParam(16)
        self.DATA_WIDTH = HwParam(8)
        self.LOOKUP_ID_WIDTH = HwParam(0)
        self.LOOKUP_HASH = HwParam(False)
        self.LOOKUP_KEY = HwParam(False)

    @override
    def hwDeclr(self):
        assert int(self.KEY_WIDTH) > 0
        assert int(self.DATA_WIDTH) >= 0
        assert int(self.ITEMS_CNT) > 1

        self.HASH_WIDTH = log2ceil(self.ITEMS_CNT)

        assert self.HASH_WIDTH < int(self.KEY_WIDTH), (
            "It makes no sense to use hash table when you can use key directly as index",
            self.HASH_WIDTH, self.KEY_WIDTH)

        with self._hwParamsShared():
            self.insert = HwIOInsert()
            self.insert.HASH_WIDTH = self.HASH_WIDTH

            self.lookup = HwIOLookupKey()

            self.lookupRes = HwIOLookupResult(masterDir=DIRECTION.IN)
            self.lookupRes.HASH_WIDTH = self.HASH_WIDTH

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOHashTableAgent(sim, self)


class HwIOHashTableAgent(AgentBase):

    def __init__(self, sim:HdlSimulator, hwIO: HwIOHashTable):
        AgentBase.__init__(self, sim, hwIO)
        hwIO.insert._initSimAgent(sim)
        hwIO.lookup._initSimAgent(sim)
        hwIO.lookupRes._initSimAgent(sim)

    @override
    def getDrivers(self):
        hwIO = self.hwIO
        yield from hwIO.insert._ag.getDrivers()
        yield from hwIO.lookup._ag.getDrivers()
        yield from hwIO.lookupRes._ag.getMonitors()

    @override
    def getMonitors(self):
        hwIO = self.hwIO
        yield from hwIO.insert._ag.getMonitors()
        yield from hwIO.lookup._ag.getMonitors()
        yield from hwIO.lookupRes._ag.getDrivers()

