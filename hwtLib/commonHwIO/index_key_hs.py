from typing import Union, Tuple

from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIODataRdVld, HwIORdVldSync, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.handshaked.hwIOBiDirectional import HwIORdVldSyncBiDirectionalDataAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class HwIOIndexKeyRdVld(HwIODataRdVld):
    """
    .. hwt-autodoc::
    """
    @override
    def hwConfig(self):
        self.INDEX_WIDTH = HwParam(4)
        self.KEY_WIDTH = HwParam(4)

    @override
    def hwDeclr(self):
        HwIORdVldSync.hwDeclr(self)
        if self.KEY_WIDTH:
            self.key = HwIOVectSignal(self.KEY_WIDTH)
        self.index = HwIOVectSignal(self.INDEX_WIDTH)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOIndexKeyRdVldAgent(sim, self)


class HwIOIndexKeyRdVldAgent(HwIODataRdVldAgent):

    @override
    def get_data(self) -> Union[Tuple[int, int], int]:
        i = self.hwIO
        if i.KEY_WIDTH:
            return (i.key.read(), i.index.read())
        else:
            return i.index.read()

    @override
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

    @override
    def hwConfig(self):
        self.INDEX_WIDTH = HwParam(4)
        self.KEY_WIDTH = HwParam(4)

    @override
    def hwDeclr(self):
        HwIORdVldSync.hwDeclr(self)
        if self.KEY_WIDTH:
            self.key = HwIOVectSignal(self.KEY_WIDTH, masterDir=DIRECTION.IN)
        self.index = HwIOVectSignal(self.INDEX_WIDTH)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOIndexKeyInRdVldAgent(sim, self)


class HwIOIndexKeyInRdVldAgent(HwIORdVldSyncBiDirectionalDataAgent):

    @override
    def onMonitorReady(self):
        "write din"
        i = self.hwIO
        if i.KEY_WIDTH:
            d = self.dinData.popleft()
            i.key.write(d)

    @override
    def onDriverWriteAck(self):
        "read din"
        i = self.hwIO
        if i.KEY_WIDTH:
            d = i.key.read()
            self.dinData.append(d)

    @override
    def get_data(self) -> Union[Tuple[int, int], int]:
        return self.hwIO.index.read()

    @override
    def set_data(self, data: Union[Tuple[int, int], int]):
        self.hwIO.index.write(data)

