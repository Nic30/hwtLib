import unittest

from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.simulator.simTestCase import SimTestCase
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream, axis_recieve_bytes, axis_send_bytes
from hwtLib.amba.axis_comp.strformat_fn import axiS_strFormat
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.constants import CLK_PERIOD


class _example_AxiS_strFormat_no_args(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.out = AxiStream()._m()

    def _impl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "test 1234")
        self.out(o)
        propagateClkRstn(self)


class _example_AxiS_strFormat_args_numbers(_example_AxiS_strFormat_no_args):

    def _config(self):
        _example_AxiS_strFormat_no_args._config(self)
        self.FORMAT = Param("0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}")

    def _impl(self):
        n = self._sig("n", dtype=uint8_t)
        n(13)
        o = axiS_strFormat(
            self, "f0", self.DATA_WIDTH,
            self.FORMAT,
            n)
        self.out(o)
        propagateClkRstn(self)


class _example_AxiS_strFormat_kwargs_numbers(_example_AxiS_strFormat_no_args):

    def _config(self):
        _example_AxiS_strFormat_no_args._config(self)
        self.FORMAT = "0b{arg0:08b}, 0o{arg0:04o}, {arg0:03d}, 0x{arg0:02x}, 0x{arg0:02X}"

    def _impl(self):
        n = self._sig("n", dtype=uint8_t)
        n(13)
        o = axiS_strFormat(
            self, "f0", self.DATA_WIDTH,
            self.FORMAT,
            arg0=n)
        self.out(o)
        propagateClkRstn(self)


class _example_AxiS_strFormat_1x_str(Unit):

    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.out = AxiStream()._m()
            self.str0 = AxiStream()

    def _impl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "str0:{0:s}", self.str0)
        self.out(o)
        propagateClkRstn(self)


class _example_AxiS_strFormat_3x_str(_example_AxiS_strFormat_1x_str):

    def _declr(self):
        super(_example_AxiS_strFormat_3x_str, self)._declr()
        with self._paramsShared():
            self.str1 = AxiStream()
            self.str2 = AxiStream()

    def _impl(self):
        o = axiS_strFormat(self, "f0", self.DATA_WIDTH, "{0:s}{1:s}xyz{str2:s}",
                           self.str0, self.str1, str2=self.str2)
        self.out(o)
        propagateClkRstn(self)


class AxiS_strFormat_TC(SimTestCase):

    def test_args_numbers(self):
        u = self.compileSimAndStart(_example_AxiS_strFormat_args_numbers())
        self.runSim(200 * CLK_PERIOD)

        for _ in range(3):
            frame = axis_recieve_bytes(u.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}".format(13))

    def test_kwargs_numbers(self):
        u = self.compileSimAndStart(_example_AxiS_strFormat_kwargs_numbers())
        self.runSim(200 * CLK_PERIOD)

        for _ in range(3):
            frame = axis_recieve_bytes(u.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "0b{0:08b}, 0o{0:04o}, {0:03d}, 0x{0:02x}, 0x{0:02X}".format(13))

    def test_no_args(self):
        u = self.compileSimAndStart(_example_AxiS_strFormat_no_args())
        self.randomize(u.out)
        self.runSim(50 * CLK_PERIOD)

        for _ in range(3):
            frame = axis_recieve_bytes(u.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, 'test 1234')

    def test_1x_str(self):
        u = self.compileSimAndStart(_example_AxiS_strFormat_1x_str())
        self.randomize(u.out)
        self.randomize(u.str0)
        strings = ["test0", "x", "1234567890"]
        for s in strings:
            axis_send_bytes(u.str0, s.encode("utf-8"))
        self.runSim(200 * CLK_PERIOD)

        for s_ref in strings:
            frame = axis_recieve_bytes(u.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "str0:{0:s}".format(s_ref))

    def test_3x_str(self):
        u = self.compileSimAndStart(_example_AxiS_strFormat_3x_str())
        self.randomize(u.out)
        self.randomize(u.str0)
        self.randomize(u.str1)
        self.randomize(u.str2)
        strings = [("test0", "str1", "str3"),
                   ("x", "y", "z" ),
                   ("1234567890", "abc", "\t\n")]
        for s0, s1, s2 in strings:
            axis_send_bytes(u.str0, s0.encode("utf-8"))
            axis_send_bytes(u.str1, s1.encode("utf-8"))
            axis_send_bytes(u.str2, s2.encode("utf-8"))
        self.runSim(200 * CLK_PERIOD)

        for s_ref in strings:
            frame = axis_recieve_bytes(u.out)
            s = bytes(frame[1]).decode("utf-8")
            self.assertEqual(s, "{0:s}{1:s}xyz{2:s}".format(*s_ref))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(AxiS_strFormat_TC('test_args_numbers'))
    suite.addTest(unittest.makeSuite(AxiS_strFormat_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
    # from hwt.synthesizer.utils import to_rtl_str
    # u = _example_AxiS_strFormat_1x_str()
    # print(to_rtl_str(u))

