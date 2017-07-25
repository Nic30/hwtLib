from hwt.hdlObjects.constants import Time
from hwt.interfaces.std import BramPort_withoutClk
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
from hwtLib.amba.axiLite import AxiLite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axiLite_comp.endpoint_arr_test import addrGetter
from hwtLib.amba.sim.axiMemSpaceMaster import AxiLiteMemSpaceMaster
from hwtLib.amba.constants import RESP_OKAY, RESP_SLVERR
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param


class TestComponent(Unit):
    """
    Containter of AxiLiteEndpoint constructed by fromInterfaceMap
    """
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.bus = AxiLite()

    def _impl(self):
        def configEp(ep):
            ep._updateParamsFrom(self)

        interfaceMap = []
        AxiLiteEndpoint.fromInterfaceMap(self,
                                         "axiLiteConv",
                                         self.bus,
                                         configEp,
                                         interfaceMap)
        Unit._impl(self)


class AxiLiteEndpoint_fromInterfaceTC(SimTestCase):

    def mkRegisterMap(self, u, modelCls):
        self.addrProbe = AddressSpaceProbe(u.bus, addrGetter)
        self.regs = AxiLiteMemSpaceMaster(u.bus, self.addrProbe.discovered)

    def randomizeAll(self):
        u = self.u
        for intf in u._interfaces:
            if u not in (u.clk, u.rst_n, u.bus) and not isinstance(intf, BramPort_withoutClk):
                self.randomize(intf)

        self.randomize(u.bus.ar)
        self.randomize(u.bus.aw)
        self.randomize(u.bus.r)
        self.randomize(u.bus.w)
        self.randomize(u.bus.b)

    def mySetUp(self, data_width=32):
        u = self.u = AxiLiteEndpoint(self.STRUCT_TEMPLATE)

        self.DATA_WIDTH = data_width
        u.DATA_WIDTH.set(self.DATA_WIDTH)

        self.prepareUnit(self.u, onAfterToRtl=self.mkRegisterMap)
        return u

    def test_nop(self):
        u = self.mySetUp(32)

        self.randomizeAll()
        self.doSim(100 * Time.ns)

        self.assertEmpty(u.bus._ag.r.data)
        self.assertEmpty(u.decoded.field0._ag.dout)
        self.assertEmpty(u.decoded.field1._ag.dout)

    def test_read(self):
        u = self.mySetUp(32)
        MAGIC = 100
        A = self.FIELD_ADDR
        u.bus.ar._ag.data.extend([A[0], A[1], A[0], A[1], A[1] + 0x4])

        u.decoded.field0._ag.din.extend([MAGIC])
        u.decoded.field1._ag.din.extend([MAGIC + 1])

        self.randomizeAll()
        self.doSim(300 * Time.ns)

        self.assertValSequenceEqual(u.bus.r._ag.data,
                                    [(MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (MAGIC, RESP_OKAY),
                                     (MAGIC + 1, RESP_OKAY),
                                     (None, RESP_SLVERR)])

    def test_write(self):
        u = self.mySetUp(32)
        MAGIC = 100
        m = mask(32 // 8)
        A = self.FIELD_ADDR
        u.bus.aw._ag.data.extend([A[0],
                                  A[1],
                                  A[0],
                                  A[1],
                                  A[1] + 0x4])
        u.bus.w._ag.data.extend([(MAGIC, m),
                                 (MAGIC + 1, m),
                                 (MAGIC + 2, m),
                                 (MAGIC + 3, m),
                                 (MAGIC + 4, m)])

        self.randomizeAll()
        self.doSim(500 * Time.ns)

        self.assertValSequenceEqual(u.decoded.field0._ag.dout,
                                    [MAGIC,
                                     MAGIC + 2
                                     ])
        self.assertValSequenceEqual(u.decoded.field1._ag.dout,
                                    [MAGIC + 1,
                                     MAGIC + 3
                                     ])
        self.assertValSequenceEqual(u.bus.b._ag.data, [RESP_OKAY for _ in range(4)] + [RESP_SLVERR])

    def test_registerMap(self):
        self.mySetUp(32)
        s = self.addrProbe.discovered.__repr__(withAddr=0, expandStructs=True)
        expected = """struct {
    <Bits, 32bits, unsigned> field0 // start:0x0(bit) 0x0(byte)
    <Bits, 32bits, unsigned> field1 // start:0x20(bit) 0x4(byte)
}"""
        self.assertEqual(s, expected)
