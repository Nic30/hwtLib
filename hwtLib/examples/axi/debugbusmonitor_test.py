#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import deque
from io import StringIO
from math import ceil
import os
import threading
import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.examples.axi.debugbusmonitor import DebugBusMonitorExampleAxi
from hwtLib.tools.debug_bus_monitor_ctl import DebugBusMonitorCtl, words_to_int
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer, StopSimumulation, WaitWriteOnly
from pyMathBitPrecise.bit_utils import ValidityError


class DebugBusMonitorCtlSim(DebugBusMonitorCtl):

    def __init__(self, tc):
        DebugBusMonitorCtl.__init__(self, 0)
        self.tc = tc

    def read(self, addr, size):
        axi = self.tc.dut.s
        word_size = axi.DATA_WIDTH // 8
        words = []
        tc: DebugBusMonitorExampleAxiTC = self.tc
        for _ in range(ceil(size / word_size)):
            assert not tc.sim_done
            ar_req = axi.ar._ag.create_addr_req(addr)
            axi.ar._ag.data.append(ar_req)

            # notify simulator about new request
            tc.ctl_thread_has_requests.release()
            assert self.tc.r_data_available.locked(), "assert that no data from simulator is pending"

            r_data = axi.r._ag.data
            assert not self.tc.sim_done
            # wait until simulator provides the data
            self.tc.r_data_available.acquire()
            assert tc.ctl_thread_has_requests.locked(), "assert that the simulator is waiting on new requets"

            d = r_data.popleft()[0]
            try:
                d = int(d)
            except ValidityError:
                d = d.val & d.vld_mask

            words.append(d)
            addr += word_size

        return words_to_int(words, word_size, size).to_bytes(size, "little")


class DebugBusMonitorExampleAxiTC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        dut = cls.dut = DebugBusMonitorExampleAxi()
        dut.DATA_WIDTH = 32
        cls.compileSim(dut)

    def setUp(self):
        SimTestCase.setUp(self)
        self.sim_done = False
        self.r_data_available = threading.Lock()
        self.r_data_available.acquire()  # locked means there are no data
        self.ctl_thread_has_requests = threading.Lock()
        self.ctl_thread_has_requests.acquire()  # locked means there are no requests

    def test_dump(self):
        dut = self.dut
        tc = self

        class SpyDeque(deque):

            def __init__(self, tc):
                super(SpyDeque, self).__init__()
                self.tc = tc

            def append(self, x):
                super(SpyDeque, self).append(x)
                self.tc.r_data_available.release()
                tc.ctl_thread_has_requests.acquire()

        dut.s.r._ag.data = SpyDeque(self)
        dut.din0._ag.data.extend([1, 2])
        dut.din1._ag.data.extend([3, 4])
        dut.din2._ag.data.extend([5, 6])

        def sim_init():
            yield WaitWriteOnly()
            dut.dout1._ag.setEnable(False)

        def time_sync():
            """
            Make simulator running only when controll tool thread has pending requests
            """
            # firstIteration = True

            tc.ctl_thread_has_requests.acquire()
            while True:
                yield Timer(CLK_PERIOD)
                if tc.sim_done:
                    raise StopSimumulation()

        self.procs.extend([time_sync(), sim_init()])

        sim_thread = threading.Thread(target=self.runSim,
                                      # actually takes less time as the simulation is stopped after ctl_thread end
                                      args=(200000 * CLK_PERIOD,))
        sim_thread.start()

        buff_txt = StringIO()
        buff_dot = StringIO()

        db = DebugBusMonitorCtlSim(tc)
        db.dump_txt(buff_txt)
        db.dump_dot(buff_dot)

        # handle the case where something went wrong and ctl thread is still running
        self.sim_done = True
        if self.r_data_available.locked():
            self.r_data_available.release()
        if self.ctl_thread_has_requests.locked():
            self.ctl_thread_has_requests.release()

        sim_thread.join()

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
        # with open(dot_file, "w") as f:
        #    f.write(buff_dot.getvalue())
        with open(dot_file, "r") as f:
            self.assertEqual(buff_dot.getvalue(), f.read())


if __name__ == "__main__":
    testLoader = unittest.TestLoader()
    # suite = unittest.TestSuite([DebugBusMonitorExampleAxiTC("test_write")])
    suite = testLoader.loadTestsFromTestCase(DebugBusMonitorExampleAxiTC)
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
