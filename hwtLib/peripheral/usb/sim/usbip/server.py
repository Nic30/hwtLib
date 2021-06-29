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

from hwtLib.peripheral.usb.sim.usbip.connection import USBIPConnection
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent


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
        self._session_recorder = None

    def install_session_recorder(self, session_recoder: 'UsbipServerSessionRecorder'):
        self._session_recorder = session_recoder

    async def on_usbip_connection(self, reader: StreamReader, writer: StreamWriter):
        if self._session_recorder:
            reader, writer = self._session_recorder.apply(reader, writer)

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

    def handle_loop_exception(self, loop, context):
        # raise the exception in main thread that there was some unfixable error
        self._terminated = True
        sim = self.usb_ag.sim

        def raise_err():
            raise context.get("exception", context["message"])
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

    def _start_server(self, loop):
        coro = asyncio.start_server(self.on_usbip_connection, self.host, self.port, loop=loop)
        self._server = loop.run_until_complete(coro)
        return coro

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

        loop.set_exception_handler(self.handle_loop_exception)
        coro = self._start_server(loop)
        if self._terminated:
            self.terminate()
            return

        # self._server = loop.run_until_complete(coro)
        if self._terminated:
            self.terminate()
            return

        t1 = threading.Thread(target=loop.run_forever, args=())
        t1.daemon = True
        t1.start()

        return t1

