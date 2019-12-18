from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.code import SwitchLogic, Concat
from hwtLib.abstract.busEndpoint import inRange
from hwt.hdl.typeShortcuts import vec


class BusStaticRemap(Unit):
    """
    Abstract class for component which remaps memory regions on bus interfaces

    :ivar MEM_MAP: list of tuples (addr_from, addr_to, size) for each memory region on second interface
    :ivar m: slave interface of first interface class where master should be connected
    :ivar s: slave interface of second interface class where master slave be connected
    """

    def _config(self):
        self.MEM_MAP = Param([])

    def _normalize_mem_map(self, mem_map):
        assert mem_map, "This would mean that second interface is entirely disconnected"
        # sort by addr from input interface
        mem_map.sort(key=lambda x: x[0])

        # assert the mapped segments are not overlapping on input interface
        last_end = 0x0
        for (offset, size, _) in mem_map:
            assert offset >= 0, offset
            assert size > 0, size
            assert offset >= last_end
            last_end = offset + size

        return mem_map

    def translate_addr_signal(self, mem_map, sig_in, sig_out):
        cases = []
        AW = sig_in._dtype.bit_length()

        for (offset_in, size, offset_out) in mem_map:
            in_is_aligned = offset_in % size == 0
            out_is_aligned = offset_out % size == 0
            if in_is_aligned:
                L = (size - 1).bit_length()
                en_sig = sig_in[:L]._eq(offset_in >> L)
                _sig_in = sig_in[L:]
                if out_is_aligned:
                    addr_drive = Concat(
                        vec(offset_out, AW - L), _sig_in)
                else:
                    addr_drive = Concat(vec(0, AW - L), _sig_in) + offset_out
            else:
                en_sig = inRange(sig_in, offset_in, offset_in + size)
                addr_drive = sig_in - (offset_in - offset_out)
            cases.append((en_sig, sig_out(addr_drive)))
        SwitchLogic(cases, default=sig_out(sig_in))

    def _declr(self):
        with self._paramsShared():
            self.m = self.intfCls()
            self.s = self.intfCls()._m()

        self.MEM_MAP = self._normalize_mem_map(self.MEM_MAP)
