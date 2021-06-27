from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct


class USB_REQUEST_TYPE_DIRECTION:
    """
    Values for usb_request_type_t.recipient
    """
    HOST_TO_DEV = 0
    DEV_TO_HOST = 1


class USB_REQUEST_TYPE_TYPE:
    """
    Values for usb_request_type_t.type
    """
    STANDARD = 0
    CLASS = 1
    VENDOR = 2


class USB_REQUEST_TYPE_RECIPIENT:
    """
    Values for usb_request_type_t.data_transfer_direction
    """
    DEVICE = 0
    INTERFACE = 1
    ENDPOINT = 2
    OTHER = 3


usb_request_type_t = HStruct(
    (Bits(5), "recipient"), # :see: :class:`~.USB_REQUEST_TYPE_RECIPIENT`
    (Bits(2), "type"),  # :see: :class:`~.USB_REQUEST_TYPE_TYPE`
    (Bits(1), "data_transfer_direction"), # :see: :class:`~.USB_REQUEST_TYPE_DIRECTION`
)


class USB_REQUEST:
    """
    Values for usb_device_request_t.bRequest
    """
    GET_STATUS = 0x00  # dev, intf, ep
    CLEAR_FEATURE = 0x01  # dev, intf, ep
    SET_FEATURE = 0x03  # dev, intf, ep
    SET_ADDRESS = 0x05  # dev
    GET_DESCRIPTOR = 0x06  # dev
    SET_DESCRIPTOR = 0x07  # dev
    GET_CONFIGURATION = 0x08  # dev
    SET_CONFIGURATION = 0x09  # dev
    SYNCH_FRAME = 0x12  # ep
    GET_INTERFACE = 0x0A  # intf
    SET_INTERFACE = 0x11  # intf


# used as a data for setup transactions
usb_device_request_t = HStruct(
    (usb_request_type_t, "bmRequestType"),
    (Bits(1 * 8), "bRequest"),
    # Word-sized field that varies according to request
    (Bits(2 * 8), "wValue"),
    # Word-sized field that varies according to
    # request; typically used to pass an index or offset
    (Bits(2 * 8), "wIndex"),
    # Number of bytes to transfer if there is a Data stage
    (Bits(2 * 8), "wLength"),
)


def make_usb_device_request(bmRequestType_recipient: USB_REQUEST_TYPE_RECIPIENT,
                        bmRequestType_type: USB_REQUEST_TYPE_TYPE,
                        bmRequestType_data_transfer_direction: USB_REQUEST_TYPE_DIRECTION,
                        bRequest:USB_REQUEST,
                        wValue: int,
                        wIndex: int,
                        wLength: int):
    return usb_device_request_t.from_py({
            "bmRequestType": {
                "recipient": bmRequestType_recipient,
                "type": bmRequestType_type,
                "data_transfer_direction": bmRequestType_data_transfer_direction,
            },
            "bRequest": bRequest,
            "wValue": wValue,
            "wIndex": wIndex,
            "wLength": wLength,
        })
