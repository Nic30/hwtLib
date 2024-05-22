from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIOVectSignal, HwIORdVldSync, HwIOSignal
from hwt.hwParam import HwParam
from hwtSimApi.hdlSimulator import HdlSimulator


class HwIOCuckooInsert(HwIORdVldSync):
    """
    Cuckoo hash insert interface
    """

    def _config(self):
        self.KEY_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(0)

    def _declr(self):
        super(HwIOCuckooInsert, self)._declr()
        self.key = HwIOVectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = HwIOVectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOCuckooInsertAgent(sim, self)


class HwIOCuckooInsertRes(HwIOCuckooInsert):
    """
    An interface with an result of insert operation.
    
    :ivar pop: signal if 1 the key and data on this interface contains
        the item which had to be removed during insert because the insertion
        limit was exceeded
    """

    def _declr(self):
        self.pop = HwIOSignal()
        HwIOCuckooInsert._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOCuckooInsertResAgent(sim, self)


class HwIOCuckooInsertAgent(HwIODataRdVldAgent):
    """
    Agent for HwIOCuckooInsert interface
    """

    def __init__(self, sim, hwIO):
        HwIODataRdVldAgent.__init__(self, sim, hwIO)
        self._hasData = bool(hwIO.DATA_WIDTH)

    def get_data(self):
        hwIO = self.hwIO
        if self._hasData:
            return hwIO.key.read(), hwIO.data.read()
        else:
            return hwIO.key.read()

    def set_data(self, data):
        hwIO = self.hwIO
        if self._hasData:
            if data is None:
                k = None
                d = None
            else:
                k, d = data
            hwIO.key.write(k)
            hwIO.data.write(d)
        else:
            hwIO.key.write(data)


class HwIOCuckooInsertResAgent(HwIOCuckooInsertAgent):
    """
    Agent for HwIOCuckooInsertRes interface
    """

    def get_data(self):
        hwIO = self.hwIO
        if self._hasData:
            return hwIO.pop.read(), hwIO.key.read(), hwIO.data.read()
        else:
            return hwIO.pop.read(), hwIO.key.read()

    def set_data(self, data):
        hwIO = self.hwIO
        if self._hasData:
            if data is None:
                p = None
                k = None
                d = None
            else:
                p, k, d = data
            hwIO.pop.write(p)
            hwIO.key.write(k)
            hwIO.data.write(d)
        else:
            hwIO.pop.write(p)
            hwIO.key.write(data)
    
    
