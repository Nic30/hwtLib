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
from hwtSimApi.triggers import Timer, StopSimumulation, WaitWriteOnly
import os


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


def run_DebugBusMonitorCtlSim(tc, out_txt, out_dot):
    db = DebugBusMonitorCtlSim(tc)
    db.dump_txt(out_txt)
    db.dump_dot(out_dot)
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

    def test_dump(self):
        u = self.u
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
        u.din0._ag.data.extend([1, 2])
        u.din1._ag.data.extend([3, 4])
        u.din2._ag.data.extend([5, 6])

        def sim_init():
            yield WaitWriteOnly()
            u.dout1._ag.setEnable(False)

        def time_sync():
            while True:
                if u.s.r._ag.data and self.r_data_available.locked():
                    tc.r_data_available.release()
                yield Timer(CLK_PERIOD)
                if self.sim_done:
                    raise StopSimumulation()

        self.procs.extend([time_sync(), sim_init()])

        buff_txt = StringIO()
        buff_dot = StringIO()
        ctl_thread = threading.Thread(target=run_DebugBusMonitorCtlSim,
                                      args=(self, buff_txt, buff_dot))
        ctl_thread.start()
        # actually takes less time as the simulation is stopped after ctl_thread end
        self.runSim(12000 * CLK_PERIOD)
        # handle the case where something went wrong and ctl thread is still running
        self.sim_done = True
        if self.r_data_available.locked():
            self.r_data_available.release()
        ctl_thread.join()

        d = buff_txt.getvalue()
        self.assertEqual(d, """\
din0:
  data: 0x0
  vld: 0
  rd: 1
din0_snapshot:
  data: 0x2
  vld: 1
  rd: 1
dout0:
  data: 0x0
  vld: 0
  rd: 1
dout0_snapshot:
  data: 0x2
  vld: 1
  rd: 1
din1:
  data: 0x4
  vld: 1
  rd: 0
din1_snapshot:
  data: 0x3
  vld: 1
  rd: 1
reg:
  dataIn:
    data: 0x4
    vld: 1
    rd: 0
  dataIn_snapshot:
    data: 0x4
    vld: 1
    rd: 0
  dataOut:
    data: 0x3
    vld: 1
    rd: 0
  dataOut_snapshot:
    data: 0x0
    vld: 0
    rd: 0
dout1:
  data: 0x3
  vld: 1
  rd: 0
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
  rd: 1
dout2:
  data: 0x0
  vld: 0
  rd: 1
dout2_snapshot:
  data: 0x0
  vld: 0
  rd: 1
""")
        dot_file = os.path.join(os.path.dirname(__file__), "DebugBusMonitorExampleAxiTC.dot")
        #with open(dot_file, "w") as f:
        #    f.write(buff_dot.getvalue())
        with open(dot_file, "r") as f:
            self.assertEqual(buff_dot.getvalue(), f.read())

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(DebugBusMonitorExampleAxiTC('test_write'))
    suite.addTest(unittest.makeSuite(DebugBusMonitorExampleAxiTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
