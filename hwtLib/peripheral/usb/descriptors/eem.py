"""
:note: Based on: Universal Serial Bus Communications Class Subclass Specification
    for Ethernet Emulation Model Devices, Revision 1.0, February 2, 2005
"""

from typing import Optional

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle
from hwtLib.peripheral.usb.descriptors.cdc import make_descriptor_functional_header, \
    usb_descriptor_functional_header, USB_CDC_DESCRIPTOR_SUBTYPE, \
    make_descriptor_functional_union
from hwtLib.peripheral.usb.descriptors.std import default_usb_descriptor_string0, \
    make_usb_descriptor_string, make_usb_descriptor_interface, USB_DEVICE_CLASS, \
    make_usb_descriptor_configuration, usb_format_bMaxPower, USB_DESCRIPTOR_TYPE, \
    make_usb_descriptor_endpoint, USB_ENDPOINT_DIR, \
    USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE, \
    USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE, \
    USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE, usb_descriptor_configuration_t, \
    make_usb_descriptor_device
from hwtLib.types.ctypes import uint8_t, uint16_t
from hwtLib.peripheral.ethernet.constants import ETH_FRAME_LEN


class EEM_REQUEST:
    """
    Used as value of bRequest, the wIndex should be interface.
    :see: Universal Serial Bus Class Definitions for Communication Devices, Version 1.1, January 19, 1999

    :ivar SEND_ENCAPSULATED_COMMAND:
        Issues a command in the format of the supported control
        protocol. The intent of this mechanism is to support
        networking devices (e.g., host-based cable modems)
        that require an additional vendor-defined interface for
        media specific hardware configuration and
        management.
        Optional.

    :ivar GET_ENCAPSULATED_RESPONSE: Optional.

    :ivar SET_ETHERNET_MULTICAST_FILTERS:
        As applications are loaded and unloaded on the host,
        the networking transport will instruct the device’s MAC
        driver to change settings of the Networking device’s
        multicast filters.
        Optional.

    :ivar SET_ETHERNET_POWER_MANAGEMENT_PATTERN_FILTER:
        Some hosts are able to conserve energy and stay quiet
        in a “sleeping” state while not being used. USB
        Networking devices may provide special pattern filtering
        hardware that enables it to wake up the attached host
        on demand when something is attempting to contact the
        host (e.g., an incoming web browser connection).
        Primitives are needed in management plane to negotiate
        the setting of these special filters

    :ivar GET_ETHERNET_POWER_MANAGEMENT_PATTERN_FILTER: Optional.
    :ivar GET_ETHERNET_STATISTIC: Optional.
    """
    SEND_ENCAPSULATED_COMMAND = 0x00
    GET_ENCAPSULATED_RESPONSE = 0x01

    SET_ETHERNET_MULTICAST_FILTERS = 0x40

    SET_ETHERNET_POWER_MANAGEMENT_PATTERN_FILTER = 0x41
    GET_ETHERNET_POWER_MANAGEMENT_PATTERN_FILTER = 0x42

    SET_ETHERNET_PACKET_FILTER = 0x43

    GET_ETHERNET_STATISTIC = 0x44


# a payloadof SET_ETHERNET_PACKET_FILTER request
eem_packet_filter_bitmap_t = HStruct(
    # ALL frames received by the networking device are forwarded
    # up to the host (required)
    (BIT, "PACKET_TYPE_PROMISCUOUS"),
    # ALL multicast frames received by the networking device are
    # forwarded up to the host, not just the ones enumerated in the
    # device's multicast address list (required)
    (BIT, "PACKET_TYPE_ALL_MULTICAST"),
    # Directed packets received containing a destination address equal
    # to the MAC address of the networking device are forwarded up to
    # the host (required)
    (BIT, "PACKET_TYPE_DIRECTED"),
    # All broadcast packets received by the networking device are
    # forwarded up to the host. (required)
    (BIT, "PACKET_TYPE_BROADCAST"),
    # All multicast packets enumerated in the device's multicast address
    # list are forwarded up to the host. (required)
    (BIT, "PACKET_TYPE_MULTICAST"),
    (Bits(32 - 5), "reserved0"),
    name="eem_packet_filter_bitmap_t"
)


class EEM_STATS:
    """
    Ethernet Statistics Feature Selector Codes
    """
    XMIT_OK = 0x01
    RCV_OK = 0x02
    XMIT_ERROR = 0x03
    RCV_ERROR = 0x04
    RCV_NO_BUFFER = 0x05
    DIRECTED_BYTES_XMIT = 0x06
    DIRECTED_FRAMES_XMIT = 0x07
    MULTICAST_BYTES_XMIT = 0x08
    MULTICAST_FRAMES_XMIT = 0x09
    BROADCAST_BYTES_XMIT = 0x0A
    BROADCAST_FRAMES_XMIT = 0x0B
    DIRECTED_BYTES_RCV = 0x0C
    DIRECTED_FRAMES_RCV = 0x0D
    MULTICAST_BYTES_RCV = 0x0E
    MULTICAST_FRAMES_RCV = 0x0F
    BROADCAST_BYTES_RCV = 0x10
    BROADCAST_FRAMES_RCV = 0x11
    RCV_CRC_ERROR = 0x12
    TRANSMIT_QUEUE_LENGTH = 0x13
    RCV_ERROR_ALIGNMENT = 0x14
    XMIT_ONE_COLLISION = 0x15
    XMIT_MORE_COLLISIONS = 0x16
    XMIT_DEFERRED = 0x17
    XMIT_MAX_COLLISIONS = 0x18
    RCV_OVERRUN = 0x19
    XMIT_UNDERRUN = 0x1A
    XMIT_HEARTBEAT_FAILURE = 0x1B
    XMIT_TIMES_CRS_LOST = 0x1C
    XMIT_LATE_COLLISIONS = 0x1D


class EEM_PACKET_TYPE:
    DATA_PAYLOAD = 0
    COMMAND = 1


# header prepended before each ethernet frame
# the frame can cross usb packet boundary and a single
# usb packet can contain multiple ethernet frames
eem_packet_header_data_t = HStruct(
    (BIT, "bmType"), # :see: :class:`~.EEM_PACKET_TYPE`
    (BIT, "bmCRC"),  # :see: :class:`~.EEM_bmCRC`
    (Bits(14), "ethFrameLen"),
)


class EEM_bmCRC:
    DEADBEEF = 0
    CALCULATED = 1


eem_packet_command_t = HStruct(
    (BIT, "bmType"), # :see: :class:`~.EEM_PACKET_TYPE`
    (BIT, "reserved0"),  # must be set to 0
    (Bits(3), "bmEEMCmd"),  # see :class:`~.EEM_bmEEMCmd`
    (Bits(11), "bmEEMCmdParam"),
)


class EEM_bmEEMCmd:
    ECHO = 0  # :note: used for usb link validation
    ECHO_RESPONSE = 1
    SUSPEND_HINT = 2
    RESPONSE_HINT = 3
    RESPONSE_COMPLETE_HINT = 4
    TICKLE = 5


wNumberMCFilters_t = HStruct(
    (Bits(15), "multicastAddrCnt"),
    (BIT, "imperfectFiltering"),  # the filter can clasify ony to probably yes
    name="wNumberMCFilters_t",
)

usb_descriptor_functional_ethernet_control_management_body_t = HStruct(
    (uint8_t, "iMACAddress"),  # Index of string descriptor. The MAC itself is also stored as string
    (Bits(32), "bmEthernetStatistics"),
    (uint16_t, "wMaxSegmentSize"),
    (wNumberMCFilters_t, "wNumberMCFilters"),
    (uint8_t, "bNumberPowerFilters"),
    name="usb_descriptor_functional_abstract_control_management_body_t"
)
usb_descriptor_functional_ethernet_control_management_t = HStruct(
    (usb_descriptor_functional_header, "header"),
    (usb_descriptor_functional_ethernet_control_management_body_t, "body"),
    name="usb_descriptor_functional_ethernet_control_management_t",
)


def make_descriptor_functional_ethernet_control_management(
        iMACAddress: int,
        bmEthernetStatistics: int,
        wMaxSegmentSize: int,
        wNumberMCFilters_multicastAddrCnt: int,
        wNumberMCFilters_imperfectFiltering: bool,
        wNumberPowerFilters: int,
        ):
    t = usb_descriptor_functional_ethernet_control_management_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.FUNCTIONAL,
            "bDescriptorSubtype": USB_CDC_DESCRIPTOR_SUBTYPE.ETHERNET_NETWORKING_FUNCTIONAL,
        },
        "body": {
            "iMACAddress": iMACAddress,
            "bmEthernetStatistics": bmEthernetStatistics,
            "wMaxSegmentSize": wMaxSegmentSize,
            "wNumberMCFilters": {
                "multicastAddrCnt": wNumberMCFilters_multicastAddrCnt,
                "imperfectFiltering": wNumberMCFilters_imperfectFiltering,
            },
            "wNumberPowerFilters": wNumberPowerFilters,
        }
    })


def get_default_usb_cdc_eem_descriptors(
        usbVer=USB_VER.USB2_0,
        bMaxPacketSize=64,
        manufacturerStr:Optional[str]=None,
        productStr:Optional[str]=None,
        deviceVer:str="0.0",
        mac="01:23:45:67:89:AB") -> UsbDescriptorBundle:
    """
    Generates USB descriptors for USB CDC Ethernet device.

    :note: based on https://github.com/hdl4fpga/hdl4fpga/blob/9334ec5b9aaebfc2104c31bba635a49ad848515a/library/usb/usbcdc/usb_cdc_descriptor_pack.vhd
    """

    strings = [default_usb_descriptor_string0, ]
    iManufacturer = 0
    if manufacturerStr is not None:
        iManufacturer = len(strings)
        strings.append(make_usb_descriptor_string(manufacturerStr))

    iProduct = 0
    if productStr is not None:
        iProduct = len(strings)
        strings.append(make_usb_descriptor_string(productStr))
    mac = mac.replace(":", "")
    assert len(mac) == 2 * 6
    iMac = len(strings)
    strings.append(make_usb_descriptor_string(mac))

    config_0 = [
        # management interface (EP2)
        make_usb_descriptor_interface(
            bInterfaceNumber=0, bAlternateSetting=0,
            bNumEndpoints=1,
            bInterfaceClass=USB_DEVICE_CLASS.CDC_CONTROL,
            bInterfaceSubClass=6,  # Ethernet Control Model
            bInterfaceProtocol=0,  # no specific protocol
            iInterface=0),
        make_descriptor_functional_header("2.0"),
        make_descriptor_functional_union(
            bMasterInterface=0, bSlaveInterface=[1]),
        make_descriptor_functional_ethernet_control_management(
            iMACAddress=iMac,
            bmEthernetStatistics=0,
            wMaxSegmentSize=ETH_FRAME_LEN,
            wNumberMCFilters_multicastAddrCnt=0,
            wNumberMCFilters_imperfectFiltering=0,
            wNumberPowerFilters=0,
        ),

        # data interface (EP1)
        make_usb_descriptor_interface(
            bInterfaceNumber=1,
            bAlternateSetting=0,
            bNumEndpoints=2,
            bInterfaceClass=USB_DEVICE_CLASS.CDC_DATA,
            bInterfaceSubClass=0,
            bInterfaceProtocol=0,
            iInterface=0),
        make_usb_descriptor_endpoint(
            bEndpointAddressDir=USB_ENDPOINT_DIR.IN,
            bEndpointAddress=1,
            attr_transferType=USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK,
            attr_synchronisationType=USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE.NONE,
            attr_usageType=USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE.DATA,
            wMaxPacketSize=bMaxPacketSize,
            bInterval=0),
        make_usb_descriptor_endpoint(
            bEndpointAddressDir=USB_ENDPOINT_DIR.OUT,
            bEndpointAddress=1,
            attr_transferType=USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK,
            attr_synchronisationType=USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE.NONE,
            attr_usageType=USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE.DATA,
            wMaxPacketSize=bMaxPacketSize,
            bInterval=0),
    ]
    config_0_len = usb_descriptor_configuration_t.bit_length() // 8 + \
        sum(c._dtype.bit_length() // 8 for c in config_0)
    assert config_0_len == 67, config_0_len

    return UsbDescriptorBundle([
        make_usb_descriptor_device(
            bDeviceClass=USB_DEVICE_CLASS.CDC_CONTROL,
            bDeviceSubClass=0x00, bDeviceProtocol=0x00,
            usbVer=usbVer,
            bMaxPacketSize=min(64, bMaxPacketSize),
            idVendor=0, idProduct=0,
            bcdDevice=deviceVer,
            iManufacturer=iManufacturer,
            iProduct=iProduct,
            iSerialNumber=0,
            bNumConfigurations=1),
        make_usb_descriptor_configuration(
            wTotalLength=config_0_len,
            bNumInterfaces=2,
            bConfigurationValue=1,
            iConfiguration=0,
            remoteWakeup=0,
            selfPowered=0,
            bMaxPower=usb_format_bMaxPower(500)
        ),
        *config_0,
        *strings,
    ])
