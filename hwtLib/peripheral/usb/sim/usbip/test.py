import json
import os
import threading
import unittest

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.sim.usbip.server import UsbipServer
from hwtLib.peripheral.usb.sim.usbip.session_recorder import UsbipServerReplayer, \
    UsbipServerSessionRecorder, cut_off_empty_time_segments, filter_empty_in
from hwtLib.peripheral.usb.usb2.device_cdc import Usb2Cdc
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer, StopSimumulation


class UsbipTC(SimTestCase):

    def test_cdc_vcp(self):
        u = Usb2Cdc()
        u.PRE_NEGOTIATED_TO = USB_VER.USB2_0  # to avoid waiting at the begin of sim
        self.compileSimAndStart(u)
        lock = self.hdl_simulator.scheduler_lock = threading.Lock()
        # sched = self.hdl_simulator.schedule
        # orig_sched = self.hdl_simulator.schedule
        #
        # def schedule(*args):
        #    with lock:
        #        return orig_sched(*args)
        #
        # self.hdl_simulator.schedule = schedule

        orig_pop = self.hdl_simulator._events.pop

        def pop():
            with lock:
                return orig_pop()

        self.hdl_simulator._events.pop = pop

        u.phy._ag = UtmiUsbAgent(u.phy._ag.sim, u.phy)
        u.phy._ag.RETRY_CNTR_MAX = 100

        trace_file = os.path.join(os.path.dirname(__file__), self.getTestName() + ".json")
        with open(trace_file) as f:
            server = UsbipServerReplayer(u.phy._ag, json.load(f), debug=False)
        #
        # server = UsbipServer(u.phy._ag, host='127.0.0.1', port=3240, debug=True)
        # rec = UsbipServerSessionRecorder(self.hdl_simulator)
        # server.install_session_recorder(rec)
        server.run()

        def send_some_data():
            msg_send = False
            while True:
                yield Timer(CLK_PERIOD * 1000)
                if not msg_send:
                    u.tx._ag.data.extend(ord(c) for c in
                                         "Hello word!\r\n"
                                         '0123456789\r\n'
                                         )
                    msg_send = True

                rx = u.rx._ag.data
                if rx:
                    # print("RX in sim: ", bytes([int(x) for x in rx]))
                    if "exit" == bytes([int(x) for x in rx]).decode():
                        raise StopSimumulation()
                    else:
                        raise AssertionError("Expexted string 'exit' received", bytes([int(x) for x in rx]))

                    rx.clear()

        self.procs.append(send_some_data())
        try:
            self.runSim(1 << 64)
        finally:
            server.terminate()

            # with open(trace_file, 'w') as f:
            #    json.dump(rec.session_data, f)


class UsbipSessionUtilsTC(unittest.TestCase):

    def test_cut_off_empty_time_segments(self):
        data = [
            (0, 'r', (0,)),
            (10, 'r', (1,)),
            (20, 'r', (2,)),
            (30, 'r', (1,)),
        ]
        res = cut_off_empty_time_segments(data, [(1, 2), (21, 30), (31, 50)])
        self.assertSequenceEqual(res, [
            (0, 'r', (0,)),
            (9, 'r', (1,)),
            (19, 'r', (2,)),
            (20, 'r', (1,)),
        ])

    def test_filter_empty_in(self):
        trace_file = os.path.join(os.path.dirname(__file__), "UsbipTC_test_cdc_vcp.json")
        with open(trace_file) as f:
            data = json.load(f)
            _data = filter_empty_in(data[0], {})
            self.assertSequenceEqual(_data, data[0])


UsbipTCs = [UsbipTC, UsbipSessionUtilsTC]

if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(Usb2CdcTC("test_phy_to_link"))
    for tc in UsbipTCs:
        suite.addTest(unittest.makeSuite(tc))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
