from typing import List, Tuple, Optional

from hwt.hdl.types.bits import Bits
from hwt.hdl.value import HValue
from hwtLib.peripheral.usb.descriptors.std import USB_DESCRIPTOR_TYPE, \
    usb_descriptor_device_t, usb_descriptor_endpoint_t, USB_ENDPOINT_DIR, \
    USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE
from hwtLib.types.ctypes import uint8_t


class UsbNoSuchDescriptor(Exception):
    """
    Raised when the device responded with STALL to GET_DESCRIPTOR which means that it does not have such a descriptor.
    """


class UsbEndpointMeta():
    """
    Information about USB endpoint extracted from :class:`~.UsbDescriptorBundle`
    """

    def __init__(self, index: int, dir_:USB_ENDPOINT_DIR,
                 supports_setup: bool=False,
                 supports_bulk: bool=False,
                 supports_interrupt: bool=False,
                 supports_isochronoust: bool=False,
                 max_packet_size: int=0,
                 buffer_size: Optional[int]=None,
                 ):
        self.index = index
        self.dir = dir_
        self.supports_setup = supports_setup
        self.supports_bulk = supports_bulk
        self.supports_interrupt = supports_interrupt
        self.supports_isochronoust = supports_isochronoust

        self.max_packet_size = max_packet_size
        if buffer_size is None:
            buffer_size = max_packet_size * 2
        self.buffer_size = buffer_size

    def __repr__(self):
        capabilities = []
        if self.supports_setup:
            capabilities.append("setup")
        if self.supports_bulk:
            capabilities.append("bulk")
        if self.supports_interrupt:
            capabilities.append("interrupt")
        if self.supports_isochronoust:
            capabilities.append("isochronoust")

        if self.dir == USB_ENDPOINT_DIR.IN:
            d = "IN"
        elif self.dir == USB_ENDPOINT_DIR.OUT:
            d = "OUT"
        else:
            d = "INVALID"

        return (
            f"<{self.__class__.__name__:s} EP{self.index:d} {d:s} {capabilities} "
            f"maxPacketSize:{self.max_packet_size:d}B>"
        )


class UsbDescriptorBundle(list):
    """
    Container of USB descriptors.

    :ivar compiled_rom: list of bytes for descriptor rom generated from this descriptor bundle
    :ivar compiled_type_to_addr_and_size: a dictionary mapping the descriptor type to list of tuples address size
        for a localization of the descriptor in compiled rom
    """

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.compiled_rom: Optional[List[int]] = None
        self.compiled_type_to_addr_and_size: Optional[USB_DESCRIPTOR_TYPE, List[Tuple[int, int]]] = None

    def get_descriptor(self, descr_t, descr_i: int) -> Tuple[int, HValue]:
        """
        Get an index of descriptor of a specific type

        :param descr_t: specific type of descriptor
        :param descr_i: index of this descriptor of this specific type (excluding any descriptors of different type)
        """
        _i = 0
        for i, desc in enumerate(self):
            if desc._dtype is descr_t or (
                    descr_t is str and
                    int(desc.header.bDescriptorType) == USB_DESCRIPTOR_TYPE.STRING):
                if _i == descr_i:
                    return i, desc
                else:
                    _i += 1
        raise UsbNoSuchDescriptor()

    def get_descriptor_index(self, descr_t, descr_i: int) -> int:
        return self.get_descriptor(descr_t, descr_i)[0]

    @staticmethod
    def pack_descriptor(d: HValue) -> List[int]:
        _data = d._reinterpret_cast(uint8_t[d._dtype.bit_length() // 8])
        return _data.to_py()

    def get_descr_bytes(self, start_descr_i: int, wLength: int) -> List[int]:
        """
        Start at the beginning of the descriptor on index start_descr_i and copy specified
        number of bytes from that location (may overlap to other descriptors as well)
        """
        data = []
        remain = wLength
        descr_i = start_descr_i
        while True:
            try:
                _d = self[descr_i]
            except IndexError:
                break
            d = self.pack_descriptor(_d)
            d_len = len(d)
            if d_len > remain:
                data.extend(d[:remain])
                break
            elif d_len == remain:
                data.extend(d)
                break
            else:
                remain -= d_len
                data.extend(d)
                descr_i += 1

        return data

    def get_endpoint_meta(self) -> Tuple[Tuple[Optional[UsbEndpointMeta], Optional[UsbEndpointMeta]]]:
        endpoints = []
        for d in self:
            if d._dtype == usb_descriptor_device_t:
                pSize = int(d.body.bMaxPacketSize)
                assert not endpoints, (endpoints, "Device descriptor should be only one")
                ep_out = UsbEndpointMeta(0, USB_ENDPOINT_DIR.OUT, supports_setup=True, max_packet_size=pSize)
                ep_in = UsbEndpointMeta(0, USB_ENDPOINT_DIR.IN, supports_setup=True, max_packet_size=pSize)
                endpoints.append([ep_out, ep_in])

            elif d._dtype == usb_descriptor_endpoint_t:
                addr = int(d.body.bEndpointAddress)
                assert addr > 0, (addr, "Control endpoint properties should be specified only in device descriptor")
                dir_ = int(d.body.bEndpointAddressDir)
                assert dir_ in (USB_ENDPOINT_DIR.IN, USB_ENDPOINT_DIR.OUT), dir_

                # add records to endponts list if there is not record for this endpoint
                missig_endponts = addr + 1 - len(endpoints)
                if missig_endponts > 0:
                    endpoints.extend([[None, None] for _ in range(missig_endponts)])
                ep = endpoints[addr][dir_]
                if ep is None:
                    ep = endpoints[addr][dir_] = UsbEndpointMeta(addr, dir_)

                # update UsbEndpointMeta with the data from this descriptor
                syn = int(d.body.bmAttributes.synchronisationType)
                if syn == USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.CONTROL:
                    ep.supports_setup = True
                elif syn == USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.ISOCHRONOUS:
                    ep.supports_isochronoust = True
                elif syn == USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK:
                    ep.supports_bulk = True
                elif syn == USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.INTERRUPT:
                    ep.supports_interrupt = True
                else:
                    raise ValueError(syn)
                ep.max_packet_size = max(ep.max_packet_size, int(d.body.wMaxPacketSize))
                ep.buffer_size = ep.max_packet_size * 2

        return tuple(endpoints)

    def get_descriptors_from_rom(self, descr_t: USB_DESCRIPTOR_TYPE) -> Tuple[int, int]:
        """
        Get the address and size of descriptor in comiled rom memory

        :param i: index of the decriptor in a list of descriptors of this type to get

        :returns: tuple address, size
        """
        assert self.compiled_rom is not None, "Rom has to be compiled first"
        try:
            return self.compiled_type_to_addr_and_size[descr_t]
        except:
            raise UsbNoSuchDescriptor()

    @staticmethod
    def HValue_to_byte_list(d: HValue):
        w = d._dtype.bit_length()
        return d._reinterpret_cast(Bits(8)[w // 8]).to_py()

    def compile_rom(self) -> List[int]:
        assert self.compiled_rom is None, "Avoid recompilation"
        self.compiled_rom = []
        self.compiled_type_to_addr_and_size = {}
        for d in self:
            as_bytelist = self.HValue_to_byte_list(d)
            addr = len(self.compiled_rom)
            size = len(as_bytelist)
            self.compiled_rom.extend(as_bytelist)
            t = int(d.header.bDescriptorType)
            descr_info_list = self.compiled_type_to_addr_and_size.setdefault(t, [])
            descr_info_list.append((addr, size))
        return self.compiled_rom
