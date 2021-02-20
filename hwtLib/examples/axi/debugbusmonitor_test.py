#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from io import StringIO
from math import ceil
import threading
import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.axi.debugbusmonitor import DebugBusMonitorExampleAxi
from hwtLib.tools.debug_bus_monitor_ctl import DebugBusMonitorCtl, words_to_int
from pyMathBitPrecise.bit_utils import ValidityError
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer, StopSimumulation


class DebugBusMonitorCtlSim(DebugBusMonitorCtl):

    def __init__(self, tc):
        DebugBusMonitorCtl.__init__(self, 0)
        self.tc = tc

    def read(self, addr, size):
        axi = self.tc.u.s
        word_size = axi.DATA_WIDTH // 8
        words = []
        for _ in range(ceil(size / word_size)):
            assert not self.tc.sim_done
            ar_req = axi.ar._ag.create_addr_req(addr)
            axi.ar._ag.data.append(ar_req)

            r_data = axi.r._ag.data
            while not r_data:
                assert not self.tc.sim_done
                self.tc.r_data_available.acquire()

            d = r_data.popleft()[0]
            try:
                d = int(d)
            except ValidityError:
                d = d.val & d.vld_mask

            words.append(d)
            addr += word_size

        return words_to_int(words, word_size, size).to_bytes(size, "little")


def run_DebugBusMonitorCtlSim(tc, out):
    db = DebugBusMonitorCtlSim(tc)
    db.dump_txt(out)
    tc.sim_done = True


class DebugBusMonitorExampleAxiTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = DebugBusMonitorExampleAxi()
        u.DATA_WIDTH = 32
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        self.sim_done = False
        self.r_data_available = threading.Lock()
        self.r_data_available.acquire()

    def test_dump_txt(self):
        u = self.u
        buff = StringIO()
        tc = self

        class SpyDeque(deque):

            def __init__(self, tc):
                super(SpyDeque, self).__init__()
                self.tc = tc

            def append(self, x):
                if self.tc.r_data_available.locked():
                    self.tc.r_data_available.release()
                super(SpyDeque, self).append(x)

        u.s.r._ag.data = SpyDeque(self)

        def time_sync():
            while True:
                if u.s.r._ag.data and self.r_data_available.locked():
                    tc.r_data_available.release()
                yield Timer(CLK_PERIOD)
                if self.sim_done:
                    raise StopSimumulation()

        self.procs.append(time_sync())
        ctl_thread = threading.Thread(target=run_DebugBusMonitorCtlSim,
                                      args=(self, buff,))
        ctl_thread.start()
        # actually takes less time as the simulation is stopped after ctl_thread end
        self.runSim(8000 * CLK_PERIOD)
        # handle the case where something went wrong and ctl thread is still running
        self.sim_done = True
        if self.r_data_available.locked():
            self.r_data_available.release()
        ctl_thread.join()

        d = buff.getvalue()
        self.assertEqual(d, """\
din0:
  data: 0x0
  vld: 0
  rd: 1
din0_snapshot:
  data: 0x0
  vld: 0
  rd: 0
dout0:
  data: 0x0
  vld: 0
  rd: 1
dout0_snapshot:
  data: 0x0
  vld: 0
  rd: 0
din1:
  data: 0x0
  vld: 0
  rd: 1
din1_snapshot:
  data: 0x0
  vld: 0
  rd: 0
dataIn:
  data: 0x0
  vld: 0
  rd: 1
dataIn_snapshot:
  data: 0x0
  vld: 0
  rd: 0
dataOut:
  data: 0x0
  vld: 0
  rd: 1
dataOut_snapshot:
  data: 0x0
  vld: 0
  rd: 0
dout1:
  data: 0x0
  vld: 0
  rd: 1
dout1_snapshot:
  data: 0x0
  vld: 0
  rd: 0
din2:
  data: 0x0
  vld: 0
  rd: 1
din2_snapshot:
  data: 0x0
  vld: 0
  rd: 0
dout2:
  data: 0x0
  vld: 0
  rd: 1
dout2_snapshot:
  data: 0x0
  vld: 0
  rd: 0
""")


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(DebugBusMonitorExampleAxiTC('test_write'))
    suite.addTest(unittest.makeSuite(DebugBusMonitorExampleAxiTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
