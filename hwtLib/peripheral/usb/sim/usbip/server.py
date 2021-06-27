#!/usr/bin/env python3

"""
This server allows to connect virtual USB devices in the simulator directly to any machine which supports USBIP.

Based on https://github.com/jwise/pyusbip/blob/master/pyusbip.py
https://www.kernel.org/doc/html/latest/usb/usbip_protocol.html
https://forums.aws.amazon.com/thread.jspa?messageID=968176

:note: usbip is a part of linux-tools-common apt package
       but in /usr/bin/ is only a placeholder
       the /usr/lib/linux-tools-`uname -r`/usbipd

https://developer.ridgerun.com/wiki/index.php?title=How_to_setup_and_use_USB/IP

:note: on some machines /usr/bin/usbip does not work correctly
    because the version of a kernel slightly differs from version of linux tools
    /usr/lib/linux-tools-5.8.0-25/usbip
    /usr/lib/linux-tools-5.9.0-050900-generic/usbip

.. code-block::

    modprobe vhci_hcd
    usbip list -r 127.0.0.1 -l
    usbip attach -r 127.0.0.1 -b 0-1

    usbip port -r 127.0.0.1
    usbip detach -p 00

"""
import asyncio
from asyncio.selector_events import BaseSelectorEventLoop
from asyncio.streams import StreamReader, StreamWriter
import threading

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.sim.usbip.connection import USBIPConnection
from hwtLib.peripheral.usb.usb2.device_cdc import Usb2Cdc
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgentBaseTC
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Timer


class UsbipServer():

    def __init__(self, usb_ag: UtmiUsbAgent, host='127.0.0.1', port=3240, debug=False):
        self.usb_ag = usb_ag
        self.host = host
        self.port = port
        self._debug = debug
        self._server = None
        self._loop = None
        self._die_on_exception = debug
        self._terminated = False
        self.main_thread_id = None

    async def on_usbip_connection(self, reader: StreamReader, writer: StreamWriter):
        conn = USBIPConnection(self, reader, writer)
        await conn.connection()

    def terminate(self):
        if self._terminated:
            return
        self._terminated = True
        server = self._server
        loop = self._loop
        if loop is not None:
            if server is not None:
                server.close()
                # loop.run_until_complete(server.wait_closed())
            loop.stop()
            # loop.close()
            # self._server = None
            # self._loop = None

    def run(self):
        if self._terminated:
            return
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop: BaseSelectorEventLoop
        self._loop = loop
        self.main_thread_id = threading.get_ident()

        def handle_exception(loop, context):
            # raise the exception in main thread that there was some unfixable error
            self._terminated = True
            sim = self.usb_ag.sim

            def raise_err():
                raise
                yield

            self.usb_ag.sim._schedule_proc(sim.now + 2, raise_err())

            # msg = ctypes.py_object(SystemExit)
            # thread_id = ctypes.c_long(self.main_thread_id)
            # res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, msg)
            # if res == 0:
            #     raise ValueError("Can not notify the exception to a main thread")
            # elif res > 1:
            #     ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            # raise context.get("exception", context["message"])

        loop.set_exception_handler(handle_exception)
        coro = asyncio.start_server(self.on_usbip_connection, self.host, self.port, loop=loop)
        if self._terminated:
            self.terminate()
            return

        self._server = loop.run_until_complete(coro)
        if self._terminated:
            self.terminate()
            return
        t1 = threading.Thread(target=loop.run_forever, args=())
        t1.daemon = True
        t1.start()

        return t1


if __name__ == "__main__":

    # example how to use this server
    class Usb2CdcTC(UlpiAgentBaseTC):

        @classmethod
        def setUpClass(cls):
            cls.u = u = Usb2Cdc()
            u.PRE_NEGOTIATED_TO = USB_VER.USB2_0  # to avoid waiting at the begin of sim
            cls.compileSim(u)

        def setUp(self):
            SimTestCase.setUp(self)
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

            u = self.u
            u.phy._ag = UtmiUsbAgent(u.phy._ag.sim, u.phy)
            u.phy._ag.RETRY_CNTR_MAX = 100

        def test_descriptor_download(self):
            u = self.u
            server = UsbipServer(u.phy._ag, host='127.0.0.1', port=3240, debug=False)
            # print("main:", threading.get_ident())
            server.run()

            def send_some_data():
                while True:
                    yield Timer(CLK_PERIOD * 1000)
                    u.tx._ag.data.extend(ord(c) for c in
                                         # "Hello word!\r\n"
                                         '0123456789\r\n'
                                         )
                    rx = u.rx._ag.data
                    if rx:
                        print("RX in sim: ", bytes([int(x) for x in rx]))
                        rx.clear()

            self.procs.append(send_some_data())
            try:
                self.runSim(1 << 64)
            except:
                server.terminate()
                raise

    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(Usb2CdcTC("test_phy_to_link"))
    suite.addTest(unittest.makeSuite(Usb2CdcTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)

