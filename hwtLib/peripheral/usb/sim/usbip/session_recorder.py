from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import sleep
from collections  import deque
import struct
import time
from typing import List, Deque, Tuple, Set

from hdlConvertorAst.to.hdlUtils import iter_with_last
from hwtLib.peripheral.usb.descriptors.std import USB_ENDPOINT_DIR
from hwtLib.peripheral.usb.sim.usbip.connection import USBIPConnection
from hwtLib.peripheral.usb.sim.usbip.constants import USBIP_CMD_SUBMIT
from hwtLib.peripheral.usb.sim.usbip.server import UsbipServer
from hwtLib.peripheral.usb.usb2.utmi_usb_agent import UtmiUsbAgent
from hwtSimApi.hdlSimulator import HdlSimulator
from math import inf
from hwtSimApi.constants import Time


class UsbipServerSessionRecorder():
    """
    Used to record the client-server communication
    in :class:`hwtLib.peripheral.usb.sim.usbip.server.UsbipServer` for later replay.
    """

    class Reader():

        def __init__(self, sim: HdlSimulator, original: StreamReader, dst: List[List[int]]):
            self.dst = dst
            self.sim = sim
            self.original = original

        async def readexactly(self, size):
            v = await self.original.readexactly(size)
            self.dst.append((self.sim.now, 'r', list(v)))
            return v

    class Writer():

        def __init__(self, sim: HdlSimulator, original: StreamWriter, dst: List[List[int]]):
            self.dst = dst
            self.original = original
            self.sim = sim

        def write(self, data):
            self.original.write(data)
            self.dst.append((self.sim.now, 'w', list(data)))

        async def drain(self):
            pass

        def close(self):
            pass

        def get_extra_info(self, name):
            return self.original.get_extra_info(name)

    def __init__(self, sim: HdlSimulator):
        self.session_data = []
        self.sim = sim

    def apply(self, reader: StreamReader, writer: StreamWriter):
        data = []
        reader = self.Reader(self.sim, reader, data)
        writer = self.Writer(self.sim, writer, data)
        self.session_data.append(data)
        return reader, writer


class UsbipServerReplayer(UsbipServer):

    class Reader():

        def __init__(self, sim: HdlSimulator, data: Deque[Tuple[int, str, List[int]]]):
            self.data = data
            self.sim = sim

        async def readexactly(self, size) -> bytes:
            t, rw, d = self.data.popleft()
            assert rw == 'r', (t, rw, "Expected write instead")
            while t > self.sim.now:
                await sleep(0.001)

            assert len(d) == size, (d, size)
            return bytes(d)

    class Writer():

        def __init__(self, sim: HdlSimulator, ref_data: Deque[List[int]]):
            self.ref_data = ref_data
            self.sim = sim

        def get_extra_info(self, name):
            if name != 'peername':
                raise NotImplementedError()
            return "sim"

        def write(self, data: bytes):
            t, rw, d = self.ref_data.popleft()
            assert rw == 'w', (t, rw, "Expected read instead")
            d = bytes(d)
            assert d == data, (d, data)
            while t > self.sim.now:
                time.sleep(0.001)

        async def drain(self):
            pass

        def close(self):
            assert not self.ref_data

    def __init__(self, usb_ag: UtmiUsbAgent, session_data, debug=False):
        self.usb_ag = usb_ag
        self.session_data = session_data
        self._debug = debug
        self._server = None
        self._loop = None
        self._die_on_exception = debug
        self._terminated = False

    def _start_server(self, loop):
        if len(self.session_data) != 1:
            raise NotImplementedError()

        data = deque(self.session_data[0])
        coro = loop.create_task(self.on_usbip_connection(
            self.Reader(self.usb_ag.sim, data),
            self.Writer(self.usb_ag.sim, data)
        ))
        return coro

    async def on_usbip_connection(self, reader: StreamReader, writer: StreamWriter):
        conn = USBIPConnection(self, reader, writer)
        await conn.connection()


def cut_off_empty_time_segments(data: List[Tuple[int, str, List[int]]],
                                time_segments: List[Tuple[int, int]]) -> List[Tuple[int, str, List[int]]]:
    """
    :note: if time segments contains some transaction the assertion error is raised
    :note: if segment (0,10) is cut off from times 0, 10, 11 it becomes 0, 1, 2

    :param time_segments: list of ranges of times to cut off (the time after is shifted)

    :return: filtered list of data from input
    """
    new_data = []
    t_offset = 0
    intervals = iter(time_segments)
    next_interval = next(intervals)
    for (t, rw, d) in data:
        while t >= next_interval[1]:
            # while current time si behind the interval substract the duration of interval
            t_offset -= next_interval[1] - next_interval[0]
            try:
                next_interval = next(intervals)
            except StopIteration:
                next_interval = (inf, inf)

        # assert t <= next_interval[0], (t, next_interval)
        new_data.append((t + t_offset, rw, d))

    return new_data


def filter_empty_in(_data: List[Tuple[int, str, List[int]]],
                    seqnum_to_rm: Set[int]) -> List[Tuple[int, str, List[int]]]:
    """
    Remove empty IN transfers from endpoints other than 0 and remove transactions by seqnum

    :param _data: list of tuples time, r/w, list of bytes
    :param seqnum_to_rm: set of seqnum to remove (all parts of the transaction with that specified seqnum are removed entirely)
    :param cut_off_segments: list of ranges of times to cut off (the time after is shifted)

    :return: filtered list of data from input
    """

    data = iter(enumerate(_data))
    to_delete = []
    while True:
        try:
            i, (_, rw, d) = next(data)
            if rw == 'r':
                if len(d) == 2:
                    (version,) = struct.unpack(">H", bytes(d))
                    if version == 0x0000:
                        current = [i]
                        i, (_, rw, d) = next(data)
                        if len(d) == USBIPConnection.OP_COMMON_SIZE:
                            (opcode, seqnum, devid, direction, ep) = \
                                struct.unpack(USBIPConnection.OP_COMMON, bytes(d))
                            current.append(i)

                            if opcode == USBIP_CMD_SUBMIT and seqnum in seqnum_to_rm:
                                # removed because of its seqnum
                                i, (_, rw, d) = next(data)  # submit command body
                                assert len(d) == USBIPConnection.OP_SUBMIT_SIZE
                                current.append(i)
                                assert len(d) == USBIPConnection.OP_SUBMIT_SIZE
                                (_, buflen, _, _, _, _) = \
                                    struct.unpack(USBIPConnection.OP_SUBMIT, bytes(d))
                                if direction == USB_ENDPOINT_DIR.OUT and buflen:
                                    i, (_, rw, d) = next(data)  # submit command data
                                    assert len(d) == buflen
                                    current.append(i)

                                # get command return
                                i, (_, rw, d) = next(data)
                                current.append(i)
                                assert rw == 'w', (rw, d)
                                to_delete.extend(current)

                            elif opcode == USBIP_CMD_SUBMIT and ep != 0 and direction == USB_ENDPOINT_DIR.IN:
                                # potentially remove if it is empty IN
                                # get command body
                                i, (_, rw, d) = next(data)  # submit command body
                                current.append(i)
                                assert len(d) == USBIPConnection.OP_SUBMIT_SIZE
                                (_, buflen, _, _, _, _) = \
                                    struct.unpack(USBIPConnection.OP_SUBMIT, bytes(d))

                                # get command return
                                i, (_, rw, d) = next(data)
                                current.append(i)
                                assert rw == 'w'
                                resp = USBIPConnection.usbip_ret_submit(
                                    seqnum, devid, direction, ep,
                                    0, len(b''), 0, b'')
                                if bytes(d) == resp:
                                    to_delete.extend(current)

        except StopIteration:
            break

    return [d for i, d in enumerate(_data) if i not in to_delete]


if __name__ == "__main__":
    import json

    with open("UsbipTC_test_cdc_vcp.json") as f:
        _data = json.load(f)
    _data = filter_empty_in(
        _data[0],
        set(range(0x5746, 0x5746 + 16))
        # {0x564c, 0x564d, 0x564e, 0x564f, 0x5650, 0x5651, 0x5652, 0x5653,
        # 0x5654, 0x5655, 0x5656, 0x5657, 0x5658, 0x5659, 0x565a, 0x565b}
    )
    _data = cut_off_empty_time_segments(_data,
                                        [
                                            #(6 * Time.us, 9 * Time.us),
                                         #(24 * Time.us, 33 * Time.us),
                                         #(41 * Time.us, 52 * Time.us),
                                         (55 * Time.us, 65 * Time.us)
                                         ])
        # print(_data)
    with open("UsbipTC_test_cdc_vcp2.json", 'w') as f:
        f.write("[[\n")
        for last, x in iter_with_last(_data):
            f.write(" ")
            f.write(json.dumps(x))
            if last:
                f.write("\n")
            else:
                f.write(",\n")
        f.write("]]\n")
