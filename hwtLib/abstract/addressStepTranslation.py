from hwt.code import Concat
from hwt.hdl.types.bits import Bits
from hwt.math import isPow2, log2ceil


class AddressStepTranslation():
    """
    :ivar align_bits: number of bits on source/destination address which are addressing in a single
        word or other address
    :ivar src_addr_step: how many bits is addressing one unit of src_addr_sig
    :ivar dst_addr_step: how many bits is addressing one unit of dst_addr_sig
    """

    def __init__(self, src_addr_step:int=8, dst_addr_step:int=8):
        self.src_addr_step = src_addr_step
        self.dst_addr_step = dst_addr_step
        assert isPow2(src_addr_step), src_addr_step
        assert isPow2(dst_addr_step), dst_addr_step

        if src_addr_step == dst_addr_step:
            align_bits = 0
        elif src_addr_step < dst_addr_step:
            align_bits = log2ceil((dst_addr_step // src_addr_step) - 1)
        else:
            align_bits = log2ceil((src_addr_step // dst_addr_step) - 1)
        self.align_bits = align_bits

    def propagate(self, src_addr_sig, dst_addr_sig, dst_offset:int=0):
        """
        :param src_addr_sig: input signal with address
        :param dst_addr_sig: output signal for address
        """
        src_addr_step, dst_addr_step = self.src_addr_step, self.dst_addr_step

        if src_addr_step != dst_addr_step:
            src_w = src_addr_sig._dtype.bit_length()
            dst_w = dst_addr_sig._dtype.bit_length()

            if src_addr_step > dst_addr_step:
                # extend src address
                assert src_w + self.align_bits <= dst_w, (
                    "Destination address space is smaller than required",
                    src_addr_sig, dst_addr_sig, src_w, self.align_bits, dst_w)
                padding = Bits(self.align_bits).from_py(0)
                src_addr_sig = Concat(src_addr_sig, padding)
            else:
                # cut src address
                assert src_w - self.align_bits <= dst_w, (
                    "Destination address space is smaller than required",
                    src_addr_sig, dst_addr_sig, src_w, self.align_bits, dst_w)
                src_addr_sig = src_addr_sig[:self.align_bits]

        # first extend then add if required to prevent value overflow
        src_addr_sig = src_addr_sig._reinterpret_cast(dst_addr_sig._dtype)
        if dst_offset != 0:
            src_addr_sig = src_addr_sig + dst_offset

        return dst_addr_sig(src_addr_sig)
