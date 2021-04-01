from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwtLib.types.ctypes import uint8_t, uint16_t


# https://www.beyondlogic.org/usbnutshell/usb5.shtml#EndpointDescriptors
descriptor_header_t = HStruct(
    (uint8_t, "bLength"),
    (uint8_t, "bDescriptorType")
)


def version_encode_bdc(s: str):
    """
    :return: The return value is in binary coded decimal with a format of 0xJJMN
        where JJ is the major version number, M is the minor version number
        and N is the sub minor version number. e.g. USB 2.0 is reported as 0x0200,
        USB 1.1 as 0x0110 and USB 1.0 as 0x0100.
    """
    mj, mi = s.split(".")
    mj = ord(mj) - ord('0')
    mi = ord(mi) - ord('0')
    return (mj << 8) | mi


descriptor_device_body_t = HStruct(
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
)

bmAttributes_t = HStruct(
    (Bits(1), "reserved1"),  # has to be set to 1
    (Bits(1), "self_powered"),
    (Bits(1), "remote_wakeup"),
    (Bits(5), "reserved0"),  # has to be set to 0
)

descriptor_configuration_body_t = HStruct(
    # Total length in bytes of data returned
    (uint16_t, "wTotalLength"),
    # Number of Interfaces of interfaces present for this configuration.
    (uint8_t, "bNumInterfaces"),
    # Value to use as an argument to select this configuration
    (uint8_t, "bConfigurationValue"),
    # Index of String Descriptor describing this configuration
    (uint8_t, "iConfiguration"),
    (bmAttributes_t, "bmAttributes"),
    # Maximum Power Consumption in 2mA units
    (uint8_t, "bMaxPower"),
)

descriptor_interface_t = HStruct(
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
)


class DEVICE_CLASS():
    UNSPECIFIED = 0x00
    AUDIO = 0x01
    CDC_control = 0x02  # Communications and CDC Control
    HID = 0x03  # Human Interface Device
    PID = 0x05  # Physical Interface Device
    IMAGE = 0x06
    PRINTER = 0x07
    MASS_STORAGE = 0x08
    USB_HUB = 0x09
    CDC_DATA = 0x0A
    SMART_CARD = 0x0B
    CONTENT_SECURITY = 0x0D
    VIDEO = 0x0E
    PERSONAL_HEALTHCARE = 0x0F
    DIAGNOSTIC_DEVICE = 0xDC
    WIRELESS_CONTROLLER = 0xE0
    MISCELLANEOUS = 0xEF
    APPLICATION_SPECIFIC = 0xFE
    VENDOR_SPECIFIC = 0xFF
# https://beyondlogic.org/usbnutshell/usb6.shtml
