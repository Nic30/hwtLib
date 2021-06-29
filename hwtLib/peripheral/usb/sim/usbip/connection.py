import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import sleep
import re
import struct
import traceback
from typing import Dict, Tuple

from hwt.hdl.types.bits import Bits
from hwtLib.peripheral.usb.descriptors.std import USB_ENDPOINT_DIR
from hwtLib.peripheral.usb.device_request import usb_request_type_t, USB_REQUEST, \
    USB_REQUEST_TYPE_RECIPIENT
from hwtLib.peripheral.usb.sim.usbip.constants import USBIP_SPEED, USBIP_VERSION, \
    USBIP_OP_DEVLIST, USBIP_REPLY, USBIP_ST_OK, USBIP_OP_IMPORT, USBIP_ST_NA, \
    USBIP_RET_SUBMIT, USB_EPIPE, USB_ENOENT, \
    USBIP_RET_UNLINK, USBIP_CMD_SUBMIT, USBIP_CMD_UNLINK, USBIP_RESET_DEV, \
    USBIP_OP_UNSPEC, USBIP_REQUEST, USBIP_OP_DEVINFO, USBIP_BUS_ID_SIZE
from hwtLib.peripheral.usb.sim.usbip.device import USBIPDevice, USBIPPending, \
    USBIPSimDevice


class USBIPProtocolErrorException(Exception):

    def __init__(self, message):
        self.message = message


class USBIPConnection:
    """
    Server container of informations about USBIP client connection
    """
    OP_SUBMIT = ">IiIIi8s"
    OP_SUBMIT_SIZE = struct.calcsize(OP_SUBMIT)
    OP_COMMON = ">HIIII"
    OP_COMMON_SIZE = struct.calcsize(OP_COMMON)

    def __init__(self, server: 'UsbipServer', reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer
        self.devices: Dict[Tuple[int, int], USBIPDevice] = {}
        self.urbs: Dict[int, USBIPPending] = {}
        self.debug: bool = server._debug
        self.server = server

    def debug_log(self, t):
        addr = self.writer.get_extra_info('peername')
        print(f'{addr}: {t}')

    def pack_device_desc(self, dev: USBIPSimDevice, interfaces=True):
        """
        Pack a device descriptors into bytes for stransport to client
        """
        busnum = dev.getBusNumber()
        devnum = dev.getDeviceAddress()
        path = f"pyusbip/{busnum:d}/{devnum:d}"
        busid = f"{busnum:d}-{devnum:d}"
        speed = USBIP_SPEED[dev.getDeviceSpeed()]

        idVendor = dev.getVendorID()
        idProduct = dev.getProductID()
        bcdDevice = dev.getbcdDevice()

        bDeviceClass = dev.getDeviceClass()
        bDeviceSubClass = dev.getDeviceSubClass()
        bDeviceProtocol = dev.getDeviceProtocol()
        configs = list(dev.iterConfigurations())
        try:
            hnd = dev.open()
            bConfigurationValue = hnd.getConfiguration()
            hnd.close()
        except Exception:
            bConfigurationValue = configs[0].getConfigurationValue()

        bNumConfigurations = dev.getNumConfigurations()

        # Sigh, find it.
        config = configs[0]
        for _config in configs:
            if _config.getConfigurationValue() == bConfigurationValue:
                config = _config
                break
        bNumInterfaces = config.getNumInterfaces()

        data = [
            struct.pack(">256s32sIIIHHHBBBBBB",
                path.encode(), busid.encode(),
                busnum, devnum, speed,
                idVendor, idProduct, bcdDevice,
                bDeviceClass, bDeviceSubClass, bDeviceProtocol,
                bConfigurationValue, bNumConfigurations, bNumInterfaces),
        ]

        if interfaces:
            for ifc in config.iterInterfaces():
                _set = list(ifc.iterSettings())[0]
                data.append(
                    struct.pack(">BBBB",
                                _set.getClass(),
                                _set.getSubClass(),
                                _set.getProtocol(), 0)
                )

        return b"".join(data)

    async def getDeviceList(self):
        """
        usbctx like function
        """
        while self.server.usb_ag.usb_driver is None or not self.server.usb_ag.usb_driver._descriptors_downloaded:
            await sleep(0.001)
        # return usbctx.getDeviceList()
        for addr, descriptors in self.server.usb_ag.usb_driver.descr.items():
            yield USBIPSimDevice(self.server.usb_ag, addr, descriptors)

    async def handle_op_devlist(self):
        if self.debug:
            self.debug_log('DEVLIST')
        devlist = [x async for x in self.getDeviceList()]

        resp = [
            struct.pack(">HHII",
                USBIP_VERSION,
                USBIP_OP_DEVLIST | USBIP_REPLY,
                USBIP_ST_OK,
                len(devlist)),
        ]
        for dev in devlist:
            resp.append(self.pack_device_desc(dev))

        self.writer.write(b''.join(resp))

    async def handle_op_import(self, busid):
        # We kind of do this the hard way -- rather than looking up by bus
        # id / device address, we instead just compare the string.  Life is
        # too short to extend python-libusb1.
        if self.debug:
            self.debug_log(f'IMPORT {busid}')

        m = re.match("(\d+)-(\d+)", busid)
        if m:
            busnum = int(m.group(1))
            devnum = int(m.group(2))

        async for dev in self.getDeviceList():
            devid = (dev.getBusNumber(), dev.getDeviceAddress())
            if devid == (busnum, devnum):
                hnd = dev.open()
                if self.debug:
                    self.debug_log(f'opened device {busid}')
                d = USBIPDevice(devid, hnd)
                self.devices[d.packDevid()] = d
                resp = struct.pack(">HHI", USBIP_VERSION,
                                   USBIP_OP_IMPORT | USBIP_REPLY, USBIP_ST_OK,
                                   ) + self.pack_device_desc(dev, interfaces=False)
                self.writer.write(resp)
                return

        if self.debug:
            self.debug_log('device not found')

        resp = struct.pack(">HHI", USBIP_VERSION,
                           USBIP_OP_IMPORT | USBIP_REPLY,
                           USBIP_ST_NA)
        self.writer.write(resp)

    @classmethod
    def make_usbip_header_basic(cls, command: int, seqnum: int, devid: int, direction:int, ep:int):
        return struct.pack(">IIIII",
            command, seqnum, devid, direction, ep
        )

    @classmethod
    def usbip_ret_submit(cls, seqnum, devid, direction, ep,
                              status:int, actual_length:int,
                               error_count:int, transfer_buffer:bytes,
                              iso_start_frame=0, iso_number_of_packets=0xffffffff,
                              iso_packet_descriptor:bytes=b''):

        header = cls.make_usbip_header_basic(
            USBIP_RET_SUBMIT, seqnum, devid, direction, ep)

        resp = b''.join([
            header,
            struct.pack(">iiiII",
                        status, actual_length, iso_start_frame,
                        iso_number_of_packets, error_count,
                        ),
            b'\x00\x00\x00\x00\x00\x00\x00\x00',
            transfer_buffer,
            iso_packet_descriptor,
        ])
        return resp

    async def handle_urb_submit(self, seqnum:int, dev: USBIPDevice, direction, ep):
        data = await self.reader.readexactly(self.OP_SUBMIT_SIZE)
        (transfer_flags, buflen, start_frame, number_of_packets, interval, setup) = \
            struct.unpack(self.OP_SUBMIT, data)

        if start_frame not in (0, 0xffffffff):
            raise NotImplementedError(f"ISO start_frame {start_frame:d}")

        if number_of_packets not in (0, 0xffffffff):
            raise NotImplementedError(f"ISO number_of_packets {number_of_packets:d}")

        if direction == USB_ENDPOINT_DIR.OUT and buflen:
            buf = await self.reader.readexactly(buflen)
        else:
            buf = b''

        if ep == 0:
            (bRequestType, bRequest, wValue, wIndex, wLength) = struct.unpack("<BBHHH", setup)
            # EP0 control traffic; unpack the control request, synchronous.
            if wLength != buflen:
                raise USBIPProtocolErrorException(f"wLength {wLength:d} != buflen {buflen:d}")

            req = Bits(8).from_py(bRequestType)._reinterpret_cast(usb_request_type_t)
            if self.debug:
                _req_str = repr(req).replace('\n', ' ')
                self.debug_log(f"seq 0x{seqnum:x} EP0 requesttype {_req_str:s}, request {bRequest:d}, wValue {wValue:d},"
                               f" wIndex {wIndex:d}, wLength {wLength:d}")

            try:
                if direction == USB_ENDPOINT_DIR.IN:
                    data = await dev.hnd.controlRead(int(req.recipient),
                                                     int(req.type),
                                                     int(req.data_transfer_direction),
                                                     bRequest, wValue, wIndex, wLength)
                    if self.debug:
                        self.debug_log(f"seq 0x{seqnum:x}: read response with {len(data):d}/{wLength:d} bytes")

                    resp = self.usbip_ret_submit(seqnum, dev.packDevid(), direction, ep,
                                               0, len(data), 0, data)

                else:

                    if bRequestType == USB_REQUEST_TYPE_RECIPIENT.DEVICE and bRequest == USB_REQUEST.SET_ADDRESS:
                        raise NotImplementedError("USB_REQ_SET_ADDRESS")
                    elif bRequestType == USB_REQUEST_TYPE_RECIPIENT.DEVICE and bRequest == USB_REQUEST.SET_CONFIGURATION:
                        if self.debug:
                            self.debug_log(f'set configuration: {wValue:d}')
                    elif bRequestType == USB_REQUEST_TYPE_RECIPIENT.INTERFACE and bRequest == USB_REQUEST.SET_INTERFACE:
                        if self.debug:
                            self.debug_log(f'set interface alt setting: {wIndex:d} -> {wValue:d}')

                    wlen = await dev.hnd.controlWrite(int(req.recipient),
                                                      int(req.type),
                                                      int(req.data_transfer_direction),
                                                      bRequest, wValue, wIndex, buf)

                    if self.debug:
                        self.debug_log(f"seq 0x{seqnum:x}: wrote {wlen:d}/{wLength:d} bytes")
                    resp = self.usbip_ret_submit(seqnum, dev.packDevid(), direction, ep,
                                               0, len(buf), 0, b'')
            except Exception as e:
                if self.debug:
                    traceback.print_exc()
                    print(e)
                    self.debug_log('EPIPE')
                resp = self.usbip_ret_submit(seqnum, dev.packDevid(), direction, ep,
                                             -USB_EPIPE, 0, 0, b'')
            self.writer.write(resp)
        else:
            # a request on another endpoint. These are asynchronous.
            xfer = dev.hnd.getTransfer()

            if direction == USB_ENDPOINT_DIR.IN:

                def callback(xfer_):
                    if self.debug:
                        self.debug_log(f'IN callback seqnum 0x{seqnum:x} ep {ep:d} status {xfer.getStatus():d} '
                                       f'len {xfer.getActualLength():d} buflen {len(xfer.getBuffer()):d}')
                    data = xfer.getBuffer()[:xfer.getActualLength()]
                    resp = self.usbip_ret_submit(seqnum, dev.packDevid(), direction, ep,
                           -xfer.getStatus(), len(data), 0, bytes(data))
                    self.writer.write(resp)
                    del self.urbs[seqnum]

                xfer.setBulk(ep | 0x80, buflen, callback)

            else:
                assert direction == USB_ENDPOINT_DIR.OUT, direction

                def callback(xfer_):
                    if self.debug:
                        self.debug_log(f'OUT callback seqnum 0x{seqnum:x} ep {ep:d} status {xfer.getStatus():d} {xfer_.buffer}',)
                    resp = self.usbip_ret_submit(seqnum, dev.packDevid(), direction, ep,
                           -xfer.getStatus(), 0, 0, b'')
                    self.writer.write(resp)
                    del self.urbs[seqnum]

                xfer.setBulk(ep, buf, callback)

            self.urbs[seqnum] = USBIPPending(seqnum, dev, xfer)
            await xfer.submit()

    async def handle_urb_unlink(self, seqnum, dev: USBIPDevice, direction, ep):
        op_submit = ">Iiiii8s"
        data = await self.reader.readexactly(struct.calcsize(op_submit))
        (sseqnum, buflen, start_frame, number_of_packets, interval, setup) = struct.unpack(op_submit, data)

        if self.debug:
            self.debug_log(f"seq 0x{sseqnum:x}: UNLINK")

        if sseqnum not in self.urbs:
            rv = -USB_ENOENT
        else:
            rv = 0
            self.urbs[sseqnum].xfer.cancel()

        resp = (
            self.make_usbip_header_basic(USBIP_RET_UNLINK, seqnum, dev.packDevid(), 0, 0),
            struct.pack(">iiiii8s",
                rv, 0, 0, 0, 0, b''
            )
        )
        self.writer.write(b''.join(resp))

    async def handle_packet(self):
        """
        Handle a USBIP packet.
        """
        try:
            data = await self.reader.readexactly(2)
        except asyncio.IncompleteReadError:
            return False

        # Try to read a header of some kind.  We can tell because if it's an
        # URB, the |op_common.version| is overlayed with the
        # |usbip_header_basic.command|, and so the |.version| is 0x0000;
        # otherwise, it's supposed to be 0x0106.
        (version,) = struct.unpack(">H", data)
        if version == 0x0000:
            # Note that we've already trimmed the version.
            data = await self.reader.readexactly(self.OP_COMMON_SIZE)
            (opcode, seqnum, devid, direction, ep) = struct.unpack(self.OP_COMMON, data)

            if devid not in self.devices:
                raise USBIPProtocolErrorException(f'devid unattached 0x{devid:x}')
            dev = self.devices[devid]

            if opcode == USBIP_CMD_SUBMIT:
                await self.handle_urb_submit(seqnum, dev, direction, ep)
            elif opcode == USBIP_CMD_UNLINK:
                await self.handle_urb_unlink(seqnum, dev, direction, ep)
            elif opcode == USBIP_RESET_DEV:
                raise NotImplementedError("URB_RESET_DEV")
            else:
                raise USBIPProtocolErrorException(f'bad USBIP URB {opcode:x}')

        elif (version & 0xff00) == 0x0100:
            # Note that we've already trimmed the version.
            op_common = ">HI"
            data = await self.reader.readexactly(struct.calcsize(op_common))
            (opcode, status) = struct.unpack(op_common, data)

            if opcode == USBIP_OP_UNSPEC | USBIP_REQUEST:
                self.writer.write(struct.pack(">HHI", version,
                                              USBIP_OP_UNSPEC | USBIP_REPLY, USBIP_ST_OK))
            elif opcode == USBIP_OP_DEVINFO | USBIP_REQUEST:
                data = await self.reader.readexactly(USBIP_BUS_ID_SIZE)
                raise NotImplementedError("DEVINFO")
                # writer.write(struct.pack(">HHI", version, USBIP_OP_DEVINFO | USBIP_REPLY, USBIP_ST_NA)
            elif opcode == USBIP_OP_DEVLIST | USBIP_REQUEST:
                await self.handle_op_devlist()
            elif opcode == USBIP_OP_IMPORT | USBIP_REQUEST:
                data = (await self.reader.readexactly(USBIP_BUS_ID_SIZE)).decode().rstrip('\0')
                await self.handle_op_import(data)
            else:
                raise USBIPProtocolErrorException(f'Unknown USBIP op 0x{opcode:x}')
        else:
            raise USBIPProtocolErrorException(f"unsupported USBIP version 0x{version:02x}")

        return True

    async def connection(self):
        if self.debug:
            self.debug_log('connect')
        _e = None
        while True:
            try:
                success = await self.handle_packet()
                await self.writer.drain()
                if not success:
                    break
            except Exception as e:
                traceback.print_exc()
                if self.debug:
                    self.debug_log('force disconnect due to exception')
                _e = e
                break

        if self.debug:
            self.debug_log('disconnect')
        for i in self.devices:
            self.devices[i].hnd.close()
            self.devices[i] = None
        await self.writer.drain()
        self.writer.close()
        if _e is not None and self.server._die_on_exception:
            raise _e

