from typing import Union, Tuple

from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIORdVldSync, HwIOVectSignal
from hwt.hwParam import HwParam
from hwtLib.handshaked.hwIOBiDirectional import HwIORdVldSyncBiDirectionalDataAgent
from ipCorePackager.constants import DIRECTION
from hwtSimApi.hdlSimulator import HdlSimulator


class HwIOIndexKeyRdVld(HwIODataRdVld):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.INDEX_WIDTH = HwParam(4)
        self.KEY_WIDTH = HwParam(4)

    def _declr(self):
        HwIORdVldSync._declr(self)
        if self.KEY_WIDTH:
            self.key = HwIOVectSignal(self.KEY_WIDTH)
        self.index = HwIOVectSignal(self.INDEX_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOIndexKeyRdVldAgent(sim, self)


class HwIOIndexKeyRdVldAgent(HwIODataRdVldAgent):

    def get_data(self) -> Union[Tuple[int, int], int]:
        i = self.hwIO
        if i.KEY_WIDTH:
            return (i.key.read(), i.index.read())
        else:
            return i.index.read()

    def set_data(self, data: Union[Tuple[int, int], int]):
        hwIO = self.hwIO
        if hwIO.KEY_WIDTH:
            if data is None:
                k = None
                i = None
            else:
                k, i = data
            hwIO.key.write(k)
        else:
            i = data
        hwIO.index.write(i)


class HwIOIndexKeyInRdVld(HwIODataRdVld):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.INDEX_WIDTH = HwParam(4)
        self.KEY_WIDTH = HwParam(4)

    def _declr(self):
        HwIORdVldSync._declr(self)
        if self.KEY_WIDTH:
            self.key = HwIOVectSignal(self.KEY_WIDTH, masterDir=DIRECTION.IN)
        self.index = HwIOVectSignal(self.INDEX_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOIndexKeyInRdVldAgent(sim, self)


class HwIOIndexKeyInRdVldAgent(HwIORdVldSyncBiDirectionalDataAgent):

    def onMonitorReady(self):
        "write din"
        i = self.hwIO
        if i.KEY_WIDTH:
            d = self.dinData.popleft()
            i.key.write(d)

    def onDriverWriteAck(self):
        "read din"
        i = self.hwIO
        if i.KEY_WIDTH:
            d = i.key.read()
            self.dinData.append(d)

    def get_data(self) -> Union[Tuple[int, int], int]:
        return self.hwIO.index.read()

    def set_data(self, data: Union[Tuple[int, int], int]):
        self.hwIO.index.write(data)

