from hwtLib.types.ctypes import uint8_t
from hwtLib.peripheral.usb.descriptors.std import USB_DESCRIPTOR_TYPE


class UsbNoSuchDescriptor(Exception):
    """
    Raised when the device responded with STALL to GET_DESCRIPTOR which means that it does not have such a descriptor.
    """


class UsbDescriptorBundle(list):
    """
    Container of USB descriptors.
    """

    def get_descriptor(self, descr_t, descr_i:int):
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

    def get_descriptor_index(self, descr_t, descr_i:int):
        return self.get_descriptor(descr_t, descr_i)[0]

    @staticmethod
    def pack_descriptor(d):
        _data = d._reinterpret_cast(uint8_t[d._dtype.bit_length() // 8])
        return _data.to_py()

    def get_descr_bytes(self, start_descr_i, wLength):
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
