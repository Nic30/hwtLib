from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.bits import Bits
from hwtLib.types.ctypes import uint8_t, uint16_t
from hwtLib.peripheral.usb.descriptors.std import make_usb_descriptor_device, \
    USB_DEVICE_CLASS, make_usb_descriptor_string, default_usb_descriptor_string0, \
    make_usb_descriptor_interface, usb_descriptor_header_t, USB_DESCRIPTOR_TYPE
from hwtLib.peripheral.usb.constants import USB_VER

# based on Device Class Definition for Human Interface Devices (HID)
# Firmware Specification—5/27/01 Version 1.11

usb_hid_mouse_input_report_t = HStruct(
    (Bits(5), "button"),
    (Bits(3), "reserved"),
    (uint8_t, "x"),
    (uint8_t, "y"),
    (uint8_t, "wheel"),
)


class USB_HID_SUBLCASS:
    NONE = 0
    BOOT_INTERFACE = 1


class USB_HID_PROTOCOL:
    NONE = 0
    KEYBOARD = 1
    MOUSE = 2


class USB_HID_COUNTRY_CODE:
    NOT_SUPPORTED = 0
    ARABIC = 1
    BELGIAN = 2
    CANADIAN_BILINGUAL = 3
    CANADIAN_FRENCH = 4
    CZECH_REPUBLIC = 5
    DANISH = 6
    FINNISH = 7
    FRENCH = 8
    GERMAN = 9
    GREEK = 10
    HEBREW = 11
    HUNGARY = 12
    INTERNATIONAL_ISO = 13
    ITALIAN = 14
    JAPAN_KATAKANA = 15
    KOREAN = 16
    LATIN_AMERICAN = 17
    NETHERLANDS_DUTCH = 18
    NORWEGIAN = 19
    PERSIAN_FARSI = 20
    POLAND = 21
    PORTUGUESE = 22
    RUSSIA = 23
    SLOVAKIA = 24
    SPANISH = 25
    SWEDISH = 26
    SWISS_FRENCH = 27
    SWISS_GERMAN = 28
    SWITZERLAND = 29
    TAIWAN = 30
    TURKISH_Q = 31
    UK = 32
    US = 33
    YUGOSLAVIA = 34
    TURKISH_F = 35


usb_descriptor_hid_body_t = HStruct(
    (uint16_t, "bcdHID"),  # HID Class Specification release.
    (uint8_t, "bCountryCode"),  # :note: :class:`~.USB_HID_COUNTRY_CODE`
    (uint8_t, "bNumDescriptors"),
    (uint8_t, "bDescriptorType"),
    (uint16_t, "wDescriptorLength"),
    # :note: bDescriptorType, wDescriptorLength are optional and not present
)
usb_descriptor_hid_t = HStruct(
    (usb_descriptor_header_t, "header"),
    (usb_descriptor_hid_body_t, "body"),
)


def make_usb_descriptor_hid(
        hidVer:str,
        bCountryCode:USB_HID_COUNTRY_CODE,
        bNumDescriptors:int,
        bDescriptorType: USB_DESCRIPTOR_TYPE,
        wDescriptorLength: int):
    t = usb_descriptor_hid_t
    return t.from_py({
        "header": {
            "bLength": t.bit_length() // 8,
            "bDescriptorType": USB_DESCRIPTOR_TYPE.HID,
        },
        "body": {
            "bcdHID": USB_VER.to_uint16_t(hidVer),
            "bCountryCode": bCountryCode,
            "bNumDescriptors": bNumDescriptors,
            "bDescriptorType": bDescriptorType,
            "wDescriptorLength": wDescriptorLength,
        }
    })


def get_default_usb_hid_mouse_descriptors():
    "based on https://www.usbmadesimple.co.uk/ums_5.htm"
    dev = make_usb_descriptor_device(
        bDeviceClass=USB_DEVICE_CLASS.UNSPECIFIED,
        bDeviceSubClass=0,
        bDeviceProtocol=0,
        usbVer=USB_VER.USB1_1,
        bMaxPacketSize=8,
        idVendor=0x0f62,  # Acrox Tchnologies Co., Ltd.
        idProduct=0x1001,  # mouse
        bcdDevice="0.01",
        iManufacturer=1,
        iProduct=2,
        iSerialNumber=0,
        bNumConfigurations=1)
    strings = [
        default_usb_descriptor_string0,
        make_usb_descriptor_string("Not known"),
        make_usb_descriptor_string("USB_PS/2 Mouse")
    ]
    conf_body = [
        make_usb_descriptor_interface(
            bInterfaceNumber=0,
            bAlternateSetting=0,
            bNumEndpoints=1,
            bInterfaceClass=USB_DEVICE_CLASS.HID,
            bInterfaceSubClass=USB_HID_SUBLCASS.BOOT_INTERFACE,
            bInterfaceProtocol=USB_HID_PROTOCOL.MOUSE,
            iInterface=0),
        make_usb_descriptor_hid(),
    ]
    raise NotImplementedError("[TODO]")

