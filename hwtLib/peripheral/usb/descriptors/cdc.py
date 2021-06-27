"""
This file contains a data structures used for communication and configuration
of USB CDC UART device.
Based on:
https://www.silabs.com/documents/public/application-notes/AN758.pdf
"""

from typing import List, Optional

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle
from hwtLib.peripheral.usb.descriptors.std import make_usb_descriptor_device, \
    USB_DEVICE_CLASS, make_usb_descriptor_configuration, usb_format_bMaxPower, \
    make_usb_descriptor_interface, usb_descriptor_header_t, USB_DESCRIPTOR_TYPE, \
    make_usb_descriptor_endpoint, USB_ENDPOINT_DIR, USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE, \
    USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE, USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE, \
    usb_descriptor_configuration_t, default_usb_descriptor_string0, make_usb_descriptor_string
from hwtLib.types.ctypes import uint32_t, uint8_t, uint16_t


class CLASS_REQUEST:
    # Configures baud rate, stop-bits, parity, and number-of-character bits.
    SET_LINE_CODING = 0x20
    # Requests current DTE rate, stop-bits, parity, and number-of-character bits.
    GET_LINE_CODING = 0x21
    # RS232 signal used to tell the DCE device the DTE device is now present.
    SET_CONTROL_LINE_STATE = 0x22


class CHAR_FORMAT:
    STOP_BIT_1 = 0
    STOP_BIT_1_5 = 1
    STOP_BIT_2 = 2


class PARITY_TYPE:
    NONE = 0
    ODD = 1
    EVEN = 2
    MARK = 3
    SPACE = 4


usb_line_coding_t = HStruct(
    (uint32_t, "dwDTERate"),  # Data terminal rate, in bits per second.
    (uint8_t, "bCharFormat"),  # :note: :class:`~.CHAR_FORMAT`
    (uint8_t, "bParityType"),  # :note: :class:`~.PARITY_TYPE`
    (uint8_t, "bDataBits"),  # Data bits (5, 6, 7, 8 or 16)
    name="usb_line_coding_t",
)


def make_usb_line_coding_default(dwDTERate=115200, bCharFormat=CHAR_FORMAT.STOP_BIT_1, bParityType=PARITY_TYPE.NONE, bDataBits=8):
    return usb_line_coding_t.from_py({
        "dwDTERate": dwDTERate,
        "bCharFormat": bCharFormat,
        "bParityType": bParityType,
        "bDataBits": bDataBits,
    })


class USB_CDC_DESCRIPTOR_SUBTYPE:
    HEADER = 0x00
    CALL_MANAGEMENT_FUNCTIONAL = 0x01
    ABSTRACT_CONTROL_MANAGEMENT = 0x02
    DIRECT_LINE_MANAGEMENT = 0x03
    TELEPHONE_RINGER_FUNCTIONAL = 0x04
    TELEPHONE_CALL_AND_LINE_STATE_REPORTING_CAPABILITIES = 0x05
    UNION = 0x06
    COUNTRY_SELECTION_FUNCTIONAL = 0x07
    TELEPHONE_OPERATIONAL_MODES = 0x08
    USB_TERMINAL_FUNCTIONAL = 0x09
    NETWORK_CHANNEL_TERMINAL = 0x0a
    PROTOCOL_UNIT_FUNCTIONAL = 0x0b
    EXTENSION_UNIT_FUNCTIONAL = 0x0c
    MULTI_CHANNEL_MANAGEMENT = 0x0d
    CAPI_CONTROL_MANAGEMENT = 0x0e
    ETHERNET_NETWORKING_FUNCTIONAL = 0x0f
    ATM_NETWORKING_FUNCTIONAL = 0x10


# :note: header common to all functional descriptors, the Header Functional Descriptor
# is :var:`~.usb_descriptor_functional_header_t`
usb_descriptor_functional_header = HStruct(
    *usb_descriptor_header_t.fields,
    (uint8_t, "bDescriptorSubtype"),
    name="usb_descriptor_functional_header",
)

usb_descriptor_functional_header_body_t = HStruct(
    (uint16_t, "bcdCDC"),
    name="usb_descriptor_functional_header_body_t",
)
usb_descriptor_functional_header_t = HStruct(
    (usb_descriptor_functional_header, "header"),
    (usb_descriptor_functional_header_body_t, "body"),
    name="usb_descriptor_functional_header_t",
)


def make_descriptor_functional_header(cdcVer:str):
    t = usb_descriptor_functional_header_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.FUNCTIONAL,
            "bDescriptorSubtype": USB_CDC_DESCRIPTOR_SUBTYPE.HEADER,
        },
        "body": {
            "bcdCDC": USB_VER.to_uint16_t(cdcVer),
        }
    })


usb_descriptor_functional_call_management_body_t = HStruct(
    (HStruct(
        # if 0 Device sends/receives call management information only over
        # the Communication Class interface.
        (BIT, "supportHandlesCallManagementItself"),
        (BIT, "supportManagementOverDataClassInterface"),
        (Bits(6), "reserved0"),
    ), "bmCapabilities"),
    # Interface number of Data Class interface optionally used for call management.
    # (Zero based index of the interface in this configuration.(bInterfaceNum))
    (uint8_t, "bDataInterface"),
    name="usb_descriptor_functional_call_management_body_t",
)
usb_descriptor_functional_call_management_t = HStruct(
    (usb_descriptor_functional_header, "header"),
    (usb_descriptor_functional_call_management_body_t, "body"),
    name="usb_descriptor_functional_call_management_t",
)


def make_descriptor_functional_call_management(
        supportHandlesCallManagementItself: bool,
        supportManagementOverDataClassInterface: bool,
        bDataInterface: int):
    t = usb_descriptor_functional_call_management_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.FUNCTIONAL,
            "bDescriptorSubtype": USB_CDC_DESCRIPTOR_SUBTYPE.CALL_MANAGEMENT_FUNCTIONAL,
        },
        "body": {
            "bmCapabilities": {
                "supportHandlesCallManagementItself": supportHandlesCallManagementItself,
                "supportManagementOverDataClassInterface": supportManagementOverDataClassInterface,
                "reserved0": 0,
            },
            "bDataInterface": bDataInterface,
        }
    })


usb_descriptor_functional_abstract_control_management_body_t = HStruct(
    (HStruct(
        (BIT, "commFeature"),
        (BIT, "lineCodingAndSerialState"),
        (BIT, "sendBreak"),
        (BIT, "networkConnection"),
        (Bits(4), "reserved0"),
    ), "bmCapabilities"),
    name="usb_descriptor_functional_abstract_control_management_body_t"
)
usb_descriptor_functional_abstract_control_management_t = HStruct(
    (usb_descriptor_functional_header, "header"),
    (usb_descriptor_functional_abstract_control_management_body_t, "body"),
    name="usb_descriptor_functional_abstract_control_management_t",
)


def make_descriptor_functional_abstract_control_management(
        capability_commFeature: bool,
        capability_lineCodingAndSerialState: bool,
        capability_sendBreak: bool,
        capability_networkConnection: bool,
        ):
    t = usb_descriptor_functional_abstract_control_management_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.FUNCTIONAL,
            "bDescriptorSubtype": USB_CDC_DESCRIPTOR_SUBTYPE.ABSTRACT_CONTROL_MANAGEMENT,
        },
        "body": {
            "bmCapabilities": {
                "commFeature": capability_commFeature,
                "lineCodingAndSerialState": capability_lineCodingAndSerialState,
                "sendBreak": capability_sendBreak,
                "networkConnection": capability_networkConnection,
                "reserved0": 0,
            }
        }
    })


def usb_define_descriptor_functional_union_body_t(SLAVE_INTERFACE_CNT: int):
    return HStruct(
        # The interface number of the Communication or
        # Data Class interface, designated as the master
        # or controlling interface for the union.
        (uint8_t, "bMasterInterface"),
        # Interface number of first slave or associated
        # interface in the union.
        (uint8_t[SLAVE_INTERFACE_CNT], "bSlaveInterface"),
        # (All zero based index of the interface in this configuration (bInterfaceNum).)
        name="usb_descriptor_functional_union_body_t",
    )


def usb_define_descriptor_functional_union_t(SLAVE_INTERFACE_CNT: int):
    assert SLAVE_INTERFACE_CNT > 0 and SLAVE_INTERFACE_CNT < 256, SLAVE_INTERFACE_CNT
    return HStruct(
        (usb_descriptor_functional_header, "header"),
        (usb_define_descriptor_functional_union_body_t(SLAVE_INTERFACE_CNT), "body"),
        name="descriptor_functional_union_t",
    )


def make_descriptor_functional_union(bMasterInterface:int, bSlaveInterface:List[int]):
    assert bSlaveInterface
    t = usb_define_descriptor_functional_union_t(len(bSlaveInterface))
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.FUNCTIONAL,
            "bDescriptorSubtype": USB_CDC_DESCRIPTOR_SUBTYPE.UNION,
        },
        "body": {
            "bMasterInterface": bMasterInterface,
            "bSlaveInterface": bSlaveInterface
        }
    })


def get_default_usb_cdc_vcp_descriptors(
        usbVer=USB_VER.USB2_0,
        bMaxPacketSize=64,
        manufacturerStr:Optional[str]=None,
        productStr:Optional[str]=None,
        deviceVer:str="0.0") -> UsbDescriptorBundle:
    """
    Generates USB descriptors for USB CDC device which works as a UART (serial)

    :note: based on https://github.com/tinyfpga/TinyFPGA-Bootloader/blob/master/common/usb_serial_ctrl_ep.v#L344
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

    config_0 = [
        # management interface (EP2)
        make_usb_descriptor_interface(
            bInterfaceNumber=0, bAlternateSetting=0,
            bNumEndpoints=1,
            bInterfaceClass=USB_DEVICE_CLASS.CDC_CONTROL,
            bInterfaceSubClass=2,  # Abstract Control Model
            bInterfaceProtocol=1,  # AT Commands: V.250 etc
            iInterface=0),
        make_descriptor_functional_header("1.1"),
        make_descriptor_functional_call_management(
            supportHandlesCallManagementItself=0,
            supportManagementOverDataClassInterface=0,
            bDataInterface=1),
        make_descriptor_functional_abstract_control_management(
            capability_commFeature=0,
            capability_lineCodingAndSerialState=0,
            capability_sendBreak=0,
            capability_networkConnection=0),
        make_descriptor_functional_union(
            bMasterInterface=0, bSlaveInterface=[1]),
        make_usb_descriptor_endpoint(
            bEndpointAddressDir=USB_ENDPOINT_DIR.IN,
            bEndpointAddress=2, # ACM endpoint
            attr_transferType=USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.INTERRUPT,
            attr_synchronisationType=USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE.NONE,
            attr_usageType=USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE.DATA,
            wMaxPacketSize=8,
            bInterval=10), # 64
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
            bEndpointAddressDir=USB_ENDPOINT_DIR.OUT,
            bEndpointAddress=1,
            attr_transferType=USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE.BULK,
            attr_synchronisationType=USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE.NONE,
            attr_usageType=USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE.DATA,
            wMaxPacketSize=bMaxPacketSize,
            bInterval=0),
        make_usb_descriptor_endpoint(
            bEndpointAddressDir=USB_ENDPOINT_DIR.IN,
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

