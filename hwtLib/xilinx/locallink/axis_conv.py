#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, Switch, If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.xilinx.locallink.intf import LocalLink
from pyMathBitPrecise.bit_utils import mask


def strbToRem(strbBits, remBits):
    for i in range(strbBits):
        strb = Bits(strbBits).from_py(mask(i + 1))
        rem = Bits(remBits).from_py(i)
        yield strb, rem


class AxiSToLocalLink(Unit):
    """
    Axi 4 stream to LocalLink

    format of user signal:
    user[0]: start of packet
    user[1]: end of packet

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.USER_WIDTH = Param(2)
        self.USE_STRB = Param(True)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = AxiStream()
            self.dataOut = LocalLink()._m()

    def _impl(self):
        assert(int(self.USER_WIDTH) == 2)  # this is how is protocol specified
        In = self.dataIn
        Out = self.dataOut

        propagateClkRstn(self)
        lastSeenLast = self._reg("lastSeenLast", def_val=1)
        sof = lastSeenLast

        Out.data(In.data)
        Out.src_rdy_n(~In.valid)

        outRd = ~Out.dst_rdy_n
        If(In.valid & outRd,
           lastSeenLast(In.last)
        )
        In.ready(outRd)

        Out.eof_n(~In.last)

        # AXI_USER(0) -> FL_SOP_N
        # Always set FL_SOP_N when FL_SOF_N - added for compatibility with xilinx
        # axi components. Otherwise FL_SOP_N would never been set and LocalLink
        # protocol would be broken.
        sop = In.user[0]
        If(sof,
           Out.sop_n(0)
        ).Else(
           Out.sop_n(~sop)
        )

        # AXI_USER(1) -> FL_EOP_N
        # Always set FL_EOP_N when FL_EOF_N - added for compatibility with xilinx
        # axi components. Otherwise FL_EOP_N would never been set and LocalLink
        # protocol would be broken.
        eop = In.user[1]
        If(In.last,
           Out.eop_n(0)
        ).Else(
           Out.eop_n(~eop)
        )

        remMap = []
        remBits = Out.rem._dtype.bit_length()
        strbBits = In.strb._dtype.bit_length()

        for strb, rem in strbToRem(strbBits, remBits):
            remMap.append((strb, Out.rem(rem)))

        end_of_part_or_transaction = In.last | eop

        If(end_of_part_or_transaction,
            Switch(In.strb)\
            .add_cases(remMap)\
            .Default(Out.rem(None))
        ).Else(
            Out.rem(mask(remBits))
        )

        Out.sof_n(~sof)


class LocalLinkToAxiS(Unit):
    """
    Framelink to axi-stream

    format of user signal:
    user[0]: start of packet
    user[1]: end of packet

    .. hwt-autodoc::
    """

    def _config(self):
        AxiSToLocalLink._config(self)

    def _declr(self):
        with self._paramsShared():
            addClkRstn(self)
            self.dataIn = LocalLink()
            self.dataOut = AxiStream()._m()

    def _impl(self):
        In = self.dataIn
        Out = self.dataOut

        sop = self._sig("sop")
        eop = self._sig("eop")

        Out.data(In.data)
        Out.valid(~In.src_rdy_n)
        In.dst_rdy_n(~Out.ready)

        Out.last(~In.eof_n)
        eop(~In.eop_n)
        sop(~In.sop_n)

        Out.user(Concat(eop, sop))

        strbMap = []
        remBits = In.rem._dtype.bit_length()
        strbBits = Out.strb._dtype.bit_length()
        for strb, rem in strbToRem(strbBits, remBits):
            strbMap.append((rem, Out.strb(strb)))
        Switch(In.rem)\
            .add_cases(strbMap)\
            .Default(Out.strb(None))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiSToLocalLink()
    print(to_rtl_str(u))
