from typing import List, Optional

from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.synthesizer.rtlLevel.constants import NOT_SPECIFIED
from hwtLib.peripheral.usb.constants import USB_VER
from hwtLib.peripheral.usb.device_request import USB_REQUEST_TYPE_RECIPIENT, \
    USB_REQUEST_TYPE_TYPE, USB_REQUEST_TYPE_DIRECTION, USB_REQUEST, make_usb_device_request
from hwtLib.types.ctypes import uint8_t, uint16_t

"""
This module contains a definition of standard USB descriptor types
and constants.
In addition there are class specific/functional descriptors.
A class-specific descriptor exists only at the Interface level.
Each class-specific descriptor is defined as a concatenation ofall
of the functional descriptors for the Interface.  The first functional descriptor
returned by the device for the interfaceshall be a header functional descriptor.
"""


# https://beyondlogic.org/usbnutshell/usb6.shtml
# https://www.engineersgarage.com/featured-contributions/usb-descriptors-and-their-types-part-3-6/
class USB_DEVICE_CLASS():
    """
    https://www.usb.org/defined-class-codes
    """
    UNSPECIFIED = 0x00
    AUDIO = 0x01
    CDC_CONTROL = 0x02  # Communications and CDC Control
    HID = 0x03  # Human Interface Device
    USB_PID = 0x05  # Physical Interface Device
    IMAGE = 0x06
    PRINTER = 0x07
    MASS_STORAGE = 0x08
    USB_HUB = 0x09
    CDC_DATA = 0x0A
    SMART_CARD = 0x0B
    CONTENT_SECURITY = 0x0D
    VIDEO = 0x0E
    PERSONAL_HEALTHCARE = 0x0F
    AUDIO_VIDEO_DEVICE = 0x10
    BILBOARD_DEVICE = 0x11
    USB_TYPE_C_BRIDGE = 0x12
    DIAGNOSTIC_DEVICE = 0xDC
    WIRELESS_CONTROLLER = 0xE0
    MISCELLANEOUS = 0xEF
    APPLICATION_SPECIFIC = 0xFE
    VENDOR_SPECIFIC = 0xFF


class USB_DESCRIPTOR_TYPE():
    DEVICE = 1
    CONFIGURATION = 2
    STRING = 3
    INTERFACE = 4
    ENDPOINT = 5
    DEVICE_QUALIFIER = 6
    OTHER_SPEED_CONFIGURATION = 7
    INTERFACE_POWER = 8
    HID = 0x21
    REPORT = 0x22
    FUNCTIONAL = 0x24

USB_2_0_PACKET_SIEZES = (8, 16, 32, 64, 128, 256, 512)
# https://www.beyondlogic.org/usbnutshell/usb5.shtml#EndpointDescriptors
usb_descriptor_header_t = HStruct(
    (uint8_t, "bLength"),  # (in bytes, including this header)
    (uint8_t, "bDescriptorType"),
    name="usb_descriptor_header_t",
)

usb_descriptor_device_body_t = HStruct(
    # The bcdUSB field reports the highest version of USB the device supports.
    # Use :func:`~bdc_encode_version`
    (uint16_t, "bcdUSB"),
    # Class Code (Assigned by USB Org)
    # If equal to Zero, each interface specifies it’s own class code
    # If equal to 0xFF, the class code is vendor specified.
    # Otherwise field is valid Class Code.
    (uint8_t, "bDeviceClass"),
    # Subclass Code (Assigned by USB Org)
    (uint8_t, "bDeviceSubClass"),
    # Protocol Code (Assigned by USB Org)
    (uint8_t, "bDeviceProtocol"),
    # Maximum Packet Size for Zero Endpoint. Valid Sizes are 8, 16, 32, 64
    (uint8_t, "bMaxPacketSize"),
    # Vendor ID (Assigned by USB Org)
    (uint16_t, "idVendor"),
    # Product ID (Assigned by Manufacturer)
    (uint16_t, "idProduct"),
    # Device Release Number, you may use :func:`~bdc_encode_version`
    (uint16_t, "bcdDevice"),
    # Index of Manufacturer String Descriptor
    (uint8_t, "iManufacturer"),
    # Index of Product String Descriptor
    (uint8_t, "iProduct"),
    # Index of Serial Number String Descriptor
    (uint8_t, "iSerialNumber"),
    # Number of Possible Configurations
    (uint8_t, "bNumConfigurations"),
    name="usb_descriptor_device_body_t",
)

usb_descriptor_device_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_device_body_t, "body"),
    name="usb_descriptor_device_t"
)


def make_usb_descriptor_device(
        bDeviceClass: USB_DEVICE_CLASS, bDeviceSubClass=0x00, bDeviceProtocol=0xff,
        usbVer: USB_VER=USB_VER.USB2_0, bMaxPacketSize=64,
        idVendor=0x1234, idProduct=0x5678,  # Micro Science Co., Ltd. Disk 2.0
        bcdDevice="0.1",
        iManufacturer=1,
        iProduct=2,
        iSerialNumber=0,
        bNumConfigurations=1):
    assert bMaxPacketSize in USB_2_0_PACKET_SIEZES, bMaxPacketSize

    t = usb_descriptor_device_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.DEVICE
        },
        "body": {
            "bcdUSB": USB_VER.to_uint16_t(usbVer),
            "bDeviceClass": bDeviceClass,
            "bDeviceSubClass": bDeviceSubClass,
            "bDeviceProtocol": bDeviceProtocol,
            "bMaxPacketSize": bMaxPacketSize,
            "idVendor": idVendor,
            "idProduct": idProduct,
            "bcdDevice": USB_VER.to_uint16_t(bcdDevice),
            "iManufacturer": iManufacturer,
            "iProduct": iProduct,
            "iSerialNumber": iSerialNumber,
            "bNumConfigurations": bNumConfigurations,
        },
    })


# A high-speed capable device that has different device information
# for full-speed and high-speed must specify this descriptor.
# It contains the same informatio as device descriptor but it is specific to high-speed.
# :note: for description of fields check :var:`~.usb_descriptor_device_body_t`
usb_descriptor_device_qualifier_body_t = HStruct(
    (uint16_t, "bcdUSB"),
    (uint8_t, "bDeviceClass"),
    (uint8_t, "bDeviceSubClass"),
    (uint8_t, "bDeviceProtocol"),
    (uint8_t, "bMaxPacketSize"),
    (uint8_t, "bNumConfigurations"),
    (uint8_t, "reserved0"),  # must be set to 0
    name="usb_descriptor_device_qualifier_body_t",
)
usb_descriptor_device_qualifier_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_device_qualifier_body_t, "body"),
    name="usb_descriptor_device_qualifier_t",
)


def make_usb_descriptor_device_qualifier(
        bDeviceClass: USB_DEVICE_CLASS, bDeviceSubClass=0x00, bDeviceProtocol=0xff,
        usbVer: USB_VER=USB_VER.USB2_0, bMaxPacketSize=64,
        bNumConfigurations=1):
    assert bMaxPacketSize in USB_2_0_PACKET_SIEZES, bMaxPacketSize
    t = usb_descriptor_device_qualifier_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.DEVICE_QUALIFIER
        },
        "body": {
            "bcdUSB": USB_VER.to_uint16_t(usbVer),
            "bDeviceClass": bDeviceClass,
            "bDeviceSubClass": bDeviceSubClass,
            "bDeviceProtocol": bDeviceProtocol,
            "bMaxPacketSize": bMaxPacketSize,
            "bNumConfigurations": bNumConfigurations,
            "reserved0": 0,
        },
    })


usb_configuration_body_bmAttributes_t = HStruct(
    (Bits(5), "reserved0"),  # has to be set to 0
    (Bits(1), "remoteWakeup"),
    (Bits(1), "selfPowered"),
    (Bits(1), "reserved1"),  # has to be set to 1
    name="usb_configuration_body_bmAttributes_t"
)


def usb_format_bMaxPower(mA):
    v = mA // 2
    assert v < 256, mA
    return v


usb_descriptor_configuration_body_t = HStruct(
    # Total length in bytes of data returned (sum of this and all functional and endpoint descriptors)
    # :note: All interface, endpoint and functional descriptors are
    # downloaded as a part of configuration descriptor.
    (uint16_t, "wTotalLength"),
    # Number of Interfaces of interfaces present for this configuration.
    (uint8_t, "bNumInterfaces"),
    # Value to use as an argument to select this configuration
    (uint8_t, "bConfigurationValue"),
    # Index of String Descriptor describing this configuration
    (uint8_t, "iConfiguration"),
    (usb_configuration_body_bmAttributes_t, "bmAttributes"),
    # Maximum Power Consumption in 2mA units
    (uint8_t, "bMaxPower"),
    name="usb_descriptor_configuration_body_t",
)

usb_descriptor_configuration_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_configuration_body_t, "body"),
    name="usb_descriptor_configuration_t"
)


def make_usb_descriptor_configuration(wTotalLength:int,
            bNumInterfaces:int,
            bConfigurationValue:int,
            iConfiguration:int,
            remoteWakeup:int=0,
            selfPowered:int=0,
            bMaxPower:int=usb_format_bMaxPower(500)):
    t = usb_descriptor_configuration_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.CONFIGURATION
        },
        "body": {
            "wTotalLength": wTotalLength,
            "bNumInterfaces": bNumInterfaces,
            "bConfigurationValue": bConfigurationValue,
            "iConfiguration": iConfiguration,
            "bmAttributes": {
                "reserved0": 0,
                "remoteWakeup": remoteWakeup,
                "selfPowered": selfPowered,
                "reserved1": 1,
            },
            "bMaxPower": bMaxPower,
        }
    })


# same as usb_descriptor_configuration_t just different bDescriptor type
usb_descriptor_other_speed_configuration_t = HStruct(
    *usb_descriptor_configuration_t.fields,
    name="usb_descriptor_other_speed_configuration_t",
)

usb_descriptor_interface_body_t = HStruct(
    # Number of Interface
    (uint8_t, "bInterfaceNumber"),
    # Value used to select alternative setting
    (uint8_t, "bAlternateSetting"),
    # Number of Endpoints used for this interface
    (uint8_t, "bNumEndpoints"),
    # Class Code (Assigned by USB Org)
    (uint8_t, "bInterfaceClass"),
    # Subclass Code (Assigned by USB Org)
    (uint8_t, "bInterfaceSubClass"),
    # Protocol Code (Assigned by USB Org)
    (uint8_t, "bInterfaceProtocol"),
    # Index of String Descriptor Describing this interface
    (uint8_t, "iInterface"),
    name="usb_descriptor_interface_body_t",
)

usb_descriptor_interface_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_interface_body_t, "body"),
    name="usb_descriptor_interface_t",
)


def make_usb_descriptor_interface(
        bInterfaceNumber:int, bAlternateSetting:int,
        bNumEndpoints: int, bInterfaceClass:USB_DEVICE_CLASS,
        bInterfaceSubClass:int, bInterfaceProtocol:int, iInterface:int):
    t = usb_descriptor_interface_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.INTERFACE
        },
        "body": {
           "bInterfaceNumber":bInterfaceNumber,
           "bAlternateSetting":bAlternateSetting,
           "bNumEndpoints":bNumEndpoints,
           "bInterfaceClass":bInterfaceClass,
           "bInterfaceSubClass":bInterfaceSubClass,
           "bInterfaceProtocol":bInterfaceProtocol,
           "iInterface": iInterface,
        }
    })


class USB_ENDPOINT_DIR:
    OUT = 0
    IN = 1


class USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE:
    CONTROL = 0
    ISOCHRONOUS = 1
    BULK = 2
    INTERRUPT = 3


class USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE:
    """
    Note only apply to isochronous endpoints.
    """
    NONE = 0
    ASYNCHRONOUS = 1
    ADAPTIVE = 2
    SYNCHRONOUS = 3


class USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE:
    DATA = 0
    FEEDBACK = 1
    IMPLICIT_FEEDBACK_DATA = 2
    RESERVED = 3


usb_configuration_body_bmAttributes_t = HStruct(
    (Bits(2), "transferType"),  # :note: :class:`~.USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE`
    (Bits(2), "synchronisationType"),  # :note: :class:`~.USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE`
    (Bits(2), "usageType"),  # :note: :class:`~.USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE`
    (Bits(2), "reserved0"),  # has to be set to 0
    name="usb_configuration_body_bmAttributes_t",
)

usb_descriptor_endpoint_body_t = HStruct(
    # The address of this endpoint within the device.
    (Bits(7), "bEndpointAddress"),
    (BIT, "bEndpointAddressDir"),  # :note: :class:`~.USB_ENDPOINT_DIR`
    (usb_configuration_body_bmAttributes_t, "bmAttributes"),
    (uint16_t, "wMaxPacketSize"),
    # Expressed in frames (ms) for low/full speed or microframes (125us) for high speed.
    (uint8_t, "bInterval"),
    name="usb_descriptor_endpoint_body_t",
)
usb_descriptor_endpoint_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_endpoint_body_t, "body"),
    name="usb_descriptor_endpoint_t",
)


def make_usb_descriptor_endpoint(
        bEndpointAddressDir:USB_ENDPOINT_DIR,
        bEndpointAddress:int,
        attr_transferType:USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE,
        attr_synchronisationType: USB_ENDPOINT_ATTRIBUTES_SYNCHRONISATION_TYPE,
        attr_usageType:USB_ENDPOINT_ATTRIBUTES_USAGE_TYPE,
        wMaxPacketSize: int,
        bInterval: int,
    ):
    assert bEndpointAddress > 0, bEndpointAddress
    t = usb_descriptor_endpoint_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.ENDPOINT,
        },
        "body": {
            "bEndpointAddress": bEndpointAddress,
            "bEndpointAddressDir":bEndpointAddressDir,
            "bmAttributes": {
                "transferType": attr_transferType,
                "synchronisationType": attr_synchronisationType,
                "usageType": attr_usageType,
                "reserved0": 0,
            },
            "wMaxPacketSize": wMaxPacketSize,
            "bInterval": bInterval,
        }
    })


def usb_define_descriptor_string0(lang_cnt:int):
    return HStruct(
        (usb_descriptor_header_t, "header"),
        (uint16_t[lang_cnt], "body"),
    )


def make_usb_descriptor_string0(langIds: List[int]):
    t = usb_define_descriptor_string0(len(langIds))
    return t.from_py({
        "header": {
            "bLength": usb_descriptor_header_t.bit_length() // 8 + 2 * len(langIds),
            "bDescriptorType": USB_DESCRIPTOR_TYPE.STRING,
        },
        "body": langIds
    })


LANG_ID_EN_US = 0x0409
default_usb_descriptor_string0 = make_usb_descriptor_string0([LANG_ID_EN_US])


def usb_define_descriptor_string(utf16_char_cnt):
    return HStruct(
        (usb_descriptor_header_t, "header"),
        (uint8_t[utf16_char_cnt * 2], "body"),
    )


def make_usb_descriptor_string(s: str):
    as_utf_16 = s.encode("utf-16")
    t = usb_define_descriptor_string(len(as_utf_16) // 2)
    return t.from_py({
        "header": {
            "bLength": usb_descriptor_header_t.bit_length() // 8 + len(as_utf_16),
            "bDescriptorType": USB_DESCRIPTOR_TYPE.STRING,
        },
        "body": [b for b in as_utf_16]
    })


def make_usb_device_request_get_descr(descr_t, i: int, wIndex=0, wLength: Optional[int]=NOT_SPECIFIED):
    if descr_t is usb_descriptor_device_t:
        des_t_id = USB_DESCRIPTOR_TYPE.DEVICE
    elif descr_t is usb_descriptor_configuration_t:
        des_t_id = USB_DESCRIPTOR_TYPE.CONFIGURATION
    elif descr_t is str:
        des_t_id = USB_DESCRIPTOR_TYPE.STRING
    elif descr_t is usb_descriptor_interface_t:
        des_t_id = USB_DESCRIPTOR_TYPE.INTERFACE
    elif descr_t is usb_descriptor_endpoint_t:
        des_t_id = USB_DESCRIPTOR_TYPE.ENDPOINT
    elif descr_t is usb_descriptor_device_qualifier_t:
        des_t_id = USB_DESCRIPTOR_TYPE.DEVICE_QUALIFIER
    elif descr_t is usb_descriptor_other_speed_configuration_t:
        des_t_id = USB_DESCRIPTOR_TYPE.OTHER_SPEED_CONFIGURATION
    else:
        # Interface_power Descriptor was proposed by Microsoft 1998 but hasn’t been implemented.
        raise ValueError(descr_t)

    if wLength is NOT_SPECIFIED:
        if descr_t is str:
            wLength = 255
        else:
            wLength = descr_t.bit_length() // 8

    return make_usb_device_request(
            bmRequestType_recipient=USB_REQUEST_TYPE_RECIPIENT.DEVICE,
            bmRequestType_type=USB_REQUEST_TYPE_TYPE.STANDARD,
            bmRequestType_data_transfer_direction=USB_REQUEST_TYPE_DIRECTION.DEV_TO_HOST,
            bRequest=USB_REQUEST.GET_DESCRIPTOR,
            wValue=(des_t_id << 8) | i,
            wIndex=wIndex,
            wLength=wLength)

