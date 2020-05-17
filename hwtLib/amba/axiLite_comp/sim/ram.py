from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.amba.constants import RESP_OKAY


class Axi4LiteSimRam(AxiSimRam):
    """
    Simulation memory for Axi4Lite interfaces (slave component)
    """

    def parseReq(self, req):
        try:
            req = [int(v) for v in req]
        except ValueError:
            raise AssertionError("Invalid AXI request", req) from None

        addr = req[0]
        return (0, addr, 1, self.allMask)

    def add_r_ag_data(self, _id, data, isLast):
        assert isLast
        self.rAg.data.append((data, RESP_OKAY))

    def pop_w_ag_data(self, _id):
        data, strb = self.wAg.data.popleft()
        last = 1
        return (data, strb, last)

    def doWriteAck(self, _id):
        self.wAckAg.data.append(RESP_OKAY)
