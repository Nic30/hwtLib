#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory
import unittest

from hwt.hwIOs.std import HwIORst_n, HwIOClk
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.serializer.store_manager import SaveToFilesFlat, SaveToSingleFiles
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.serializer.xdc.serializer import XdcSerializer
from hwt.synth import to_rtl
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axi4s_fullduplex import Axi4StreamFullDuplex
from hwtLib.mem.fifoAsync import FifoAsync


# note: not in main library as typical usecase differs to much
#     and it is more simple to instantiate 2 independent CDCs
#     rather than using complex configuration
#     (separate clk, rsts for rx/tx, different buff sizes, ...)
class Axi4StreamFullDuplexCdc(HwModule):
    """
    CDC for Axi4StreamFullDuplex interface
    (2x async FIFO with same params, hdl component shared)
    """

    def _config(self):
        self.DEPTH = HwParam(0)
        self.IN_FREQ = HwParam(int(100e6))
        self.OUT_FREQ = HwParam(int(100e6))
        Axi4StreamFullDuplex._config(self)

    def _declr(self):
        self.dataIn_clk = HwIOClk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        self.dataOut_clk = HwIOClk()
        self.dataOut_clk.FREQ = self.OUT_FREQ

        with self._hwParamsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn_rst_n = HwIORst_n()
                with self._associated(rst=self.dataIn_rst_n):
                    self.dataIn = Axi4StreamFullDuplex()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut_rst_n = HwIORst_n()
                with self._associated(rst=self.dataOut_rst_n):
                    self.dataOut = Axi4StreamFullDuplex()._m()

    def _impl(self):
        tx = Axi4SBuilder(self, self.dataIn.tx).buff_cdc(
            self.dataOut_clk, self.dataOut_rst_n, self.DEPTH).end
        self.dataOut.tx(tx)

        rx = Axi4SBuilder(self, self.dataOut.rx).buff_cdc(
            self.dataIn_clk, self.dataIn_rst_n, self.DEPTH).end
        self.dataIn.rx(rx)


class ConstraintsXdcClockRelatedTC(unittest.TestCase):
    __FILE__ = __file__

    def assert_constraints_file_eq(self, m, file_name: str):
        THIS_DIR = os.path.dirname(os.path.realpath(self.__FILE__))
        ref_f_name = os.path.join(THIS_DIR, file_name)
        with TemporaryDirectory() as build_root:
            saver = SaveToFilesFlat(Vhdl2008Serializer, build_root)
            to_rtl(m, saver)

            f_name = os.path.join(
                build_root, "constraints" + XdcSerializer.fileExtension)
            with open(f_name) as f:
                s = f.read()
            # with open(ref_f_name, "w") as f:
            #     f.write(s)

        with open(ref_f_name) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def assert_constraints_file_eq_flat_files(self, m: HwModule, file_name):
        THIS_DIR = os.path.dirname(os.path.realpath(self.__FILE__))
        ref_f_name = os.path.join(THIS_DIR, file_name)
        with TemporaryDirectory() as build_root:
            saver = SaveToSingleFiles(Vhdl2008Serializer, build_root, m._getDefaultName())
            to_rtl(m, saver)

            f_name = os.path.join(
                build_root, m._name + XdcSerializer.fileExtension)
            with open(f_name) as f:
                s = f.read()
            # with open(ref_f_name, "w") as f:
            #     f.write(s)

        with open(ref_f_name) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def test_FifoAsync(self):
        m = FifoAsync()
        m.DEPTH = 8
        self.assert_constraints_file_eq(m, "FifoAsync.xdc")

    def testAxi4StreamFullDuplexCdc(self):
        m = Axi4StreamFullDuplexCdc()
        m.DEPTH = 9
        self.assert_constraints_file_eq(m, "Axi4StreamFullDuplexCdc.xdc")

    def test_FifoAsync_flat_files(self):
        m = FifoAsync()
        m.DEPTH = 8
        self.assert_constraints_file_eq_flat_files(m, "FifoAsync.xdc")


if __name__ == '__main__':
    unittest.main()
