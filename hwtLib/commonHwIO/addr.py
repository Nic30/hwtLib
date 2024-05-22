from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIORdVldSync, HwIOVectSignal
from hwt.hwParam import HwParam
from hwtSimApi.hdlSimulator import HdlSimulator


class HwIOAddrRdVld(HwIORdVldSync):

    def _config(self):
        self.ID_WIDTH = HwParam(4)
        self.ADDR_WIDTH = HwParam(32)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = HwIOVectSignal(self.ID_WIDTH)
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        HwIORdVldSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrRdVldAgent(sim, self)


class HwIOAddrRdVldAgent(HwIODataRdVldAgent):

    def set_data(self, data):
        i = self.hwIO
        if data is None:
            id_, addr = None, None
        elif i.ID_WIDTH:
            id_, addr = data
            i.id.write(id_)
        else:
            addr = data

        i.addr.write(addr)

    def get_data(self):
        i = self.hwIO
        if i.ID_WIDTH:
            return i.id.read(), i.addr.read()
        else:
            return i.addr.read()
