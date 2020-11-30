#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from tempfile import TemporaryDirectory
import unittest

from hwt.interfaces.std import Rst_n, Clk
from hwt.serializer.store_manager import SaveToFilesFlat
from hwt.serializer.vhdl import Vhdl2008Serializer
from hwt.serializer.xdc.serializer import XdcSerializer
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import to_rtl
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_fullduplex import AxiStreamFullDuplex
from hwtLib.mem.fifoAsync import FifoAsync


# note: not in main library as typical usecase differs to much
#     and it is more simple to instantiate 2 independent CDCs
#     rather than using complex configuration
#     (separate clk, rsts for rx/tx, different buff sizes, ...)
class AxiStreamFullDuplexCdc(Unit):
    """
    CDC for AxiStreamFullDuplex interface
    (2x async FIFO with same params, hdl component shared)
    """

    def _config(self):
        self.DEPTH = Param(0)
        self.IN_FREQ = Param(int(100e6))
        self.OUT_FREQ = Param(int(100e6))
        AxiStreamFullDuplex._config(self)

    def _declr(self):
        self.dataIn_clk = Clk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        self.dataOut_clk = Clk()
        self.dataOut_clk.FREQ = self.OUT_FREQ

        with self._paramsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn_rst_n = Rst_n()
                with self._associated(rst=self.dataIn_rst_n):
                    self.dataIn = AxiStreamFullDuplex()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut_rst_n = Rst_n()
                with self._associated(rst=self.dataOut_rst_n):
                    self.dataOut = AxiStreamFullDuplex()._m()

    def _impl(self):
        tx = AxiSBuilder(self, self.dataIn.tx).buff_cdc(
            self.dataOut_clk, self.dataOut_rst_n, self.DEPTH).end
        self.dataOut.tx(tx)

        rx = AxiSBuilder(self, self.dataOut.rx).buff_cdc(
            self.dataIn_clk, self.dataIn_rst_n, self.DEPTH).end
        self.dataIn.rx(rx)


class ConstraintsXdcClockRelatedTC(unittest.TestCase):
    __FILE__ = __file__

    def assert_constraints_file_eq(self, u, file_name):
        THIS_DIR = os.path.dirname(os.path.realpath(self.__FILE__))
        ref_f_name = os.path.join(THIS_DIR, file_name)
        with TemporaryDirectory() as build_root:
            saver = SaveToFilesFlat(Vhdl2008Serializer, build_root)
            to_rtl(u, saver)

            f_name = os.path.join(
                build_root, "constraints" + XdcSerializer.fileExtension)
            with open(f_name) as f:
                s = f.read()
            # with open(ref_f_name, "w") as f:
            #     f.write(s)

        with open(ref_f_name) as f:
            ref_s = f.read()
        self.assertEqual(s, ref_s)

    def test_FifoAsync(self):
        u = FifoAsync()
        u.DEPTH = 8
        self.assert_constraints_file_eq(u, "FifoAsync.xdc")

    def testAxiStreamFullDuplexCdc(self):
        u = AxiStreamFullDuplexCdc()
        u.DEPTH = 9
        self.assert_constraints_file_eq(u, "AxiStreamFullDuplexCdc.xdc")


if __name__ == '__main__':
    unittest.main()
