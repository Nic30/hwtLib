#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, log2ceil, Concat, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.reg import AxiSReg
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.amba.axis import AxiStream


class AxiS_resizer(AxiSCompBase):
    """
    Change data with of AxiStream interface

    :attention: start of frame is expected to be aligned on first word
    :attention: strb can be not fully set only in last word
    :attention: in upscale mode id and other signals which are not dependent on data width
        are propagated only from last word

    .. aafig::
                                         +-------------+
                                         |             |
        +-------------+  +-----------+   |             |
        |stream,      +-->           |   |             |
        |datawidth:64 |  | resizer   +--->stream,      |
        +-------------+  | 64 to 256 |   |datawidth:256|
                         +-----------+   |             |
                                         |             |
        +-------------+                  |             |
        |             |                  +-------------+
        |             |
        |             |  +-----------+
        |stream,      |  |           |   +-------------+
        |datawidth:256+--> resizer   +--->stream,      |
        |             |  | 256 to 64 |   |datawidth:64 |
        |             |  +-----------+   +-------------+
        |             |
        +-------------+


    :note: interface is configurable and schematic is example with AxiStream

    :note: first schematic is for upsize mode, second one is for downsize mode

    .. hwt-schematic:: _example_AxiS_resizer_upscale
    .. hwt-schematic:: _example_AxiS_resizer_downscale
    """

    def _config(self):
        AxiSCompBase._config(self)
        self.OUT_DATA_WIDTH = Param(64)
        self.USE_STRB = True

    def _declr(self):
        assert self.USE_STRB
        addClkRstn(self)

        with self._paramsShared():
            self.dataIn = AxiStream()

        with self._paramsShared(exclude=({"DATA_WIDTH"}, set())):
            o = self.dataOut = AxiStream()._m()
            o.DATA_WIDTH = self.OUT_DATA_WIDTH

    def nextAreNotValidLogic(self, inStrb, actualItemIndx, ITEMS, ITEM_DW):
        res = None
        ITEM_W = ITEM_DW // 8
        for i in range(ITEMS - 1):  # -1 because if it is last we do not need this
            strbHi = ITEMS * ITEM_W
            strbLo = (i + 1) * ITEM_W
            othersNotValid = actualItemIndx._eq(
                i) & inStrb[strbHi:strbLo]._eq(0)
            if res is None:
                res = othersNotValid
            else:
                res = res | othersNotValid
        if res is None:
            return True

        _res = self._sig("nextAreNotValid")
        _res(res)
        return _res

    def upscale(self, IN_DW, OUT_DW):
        if OUT_DW % IN_DW != 0:
            raise NotImplementedError()
        ITEMS = OUT_DW // IN_DW
        dIn = self.getDataWidthDependent(self.dataIn)

        dataOut = self.dataOut
        dOut = self.getDataWidthDependent(dataOut)

        itemCntr = self._reg("itemCntr", Bits(log2ceil(ITEMS + 1)), def_val=0)
        hs = StreamNode([self.dataIn], [dataOut]).ack()
        isLastItem = (itemCntr._eq(ITEMS - 1) | self.dataIn.last)

        vld = self.get_valid_signal(self.dataIn)

        outputs = {outp: [] for outp in dOut}
        for wordIndx in range(ITEMS):
            for inp, outp in zip(dIn, dOut):
                # generate register if is not last item
                s = self._sig("item_%d_%s" % (wordIndx, inp._name), inp._dtype)

                if wordIndx <= ITEMS - 1:
                    r = self._reg("reg_" + inp._name + "_%d" %
                                  wordIndx, inp._dtype, def_val=0)

                    If(hs & isLastItem,
                       r(0)
                    ).Elif(vld & itemCntr._eq(wordIndx),
                       r(inp)
                    )

                    If(itemCntr._eq(wordIndx),
                        s(inp)
                    ).Else(
                        s(r)
                    )
                else:  # last item does not need register
                    If(itemCntr._eq(wordIndx),
                        s(inp)
                    ).Else(
                        s(0)
                    )

                outputs[outp].append(s)

        # dataIn/dataOut hs
        self.get_ready_signal(self.dataIn)(self.get_ready_signal(dataOut))
        self.get_valid_signal(dataOut)(vld & (isLastItem))

        # connect others signals directly
        for inp, outp in zip(self.get_data(self.dataIn), self.get_data(dataOut)):
            if inp not in dIn:
                outp(inp)

        # connect data signals to utput
        for outp, outItems in outputs.items():
            outp(Concat(*reversed(outItems)))

        # itemCntr next logic
        If(hs,
            If(isLastItem,
                itemCntr(0)
            ).Else(
                itemCntr(itemCntr + 1)
            )
        )

    def downscale(self, IN_DW, OUT_DW):
        if IN_DW % OUT_DW != 0:
            raise NotImplementedError()
        dOut = self.getDataWidthDependent(self.dataOut)

        # instantiate AxiSReg, AxiSBuilder is not used to avoid dependencies
        inReg = AxiSReg(self.intfCls)
        inReg._updateParamsFrom(self.dataIn)
        self.inReg = inReg
        inReg.clk(self.clk)
        inReg.rst_n(self.rst_n)
        inReg.dataIn(self.dataIn)
        dataIn = inReg.dataOut

        dIn = self.getDataWidthDependent(dataIn)

        ITEMS = IN_DW // OUT_DW
        itemCntr = self._reg("itemCntr", Bits(log2ceil(ITEMS + 1)), def_val=0)

        hs = StreamNode([dataIn], [self.dataOut]).ack()
        isLastItem = itemCntr._eq(ITEMS - 1)
        strbLastOverride = self.nextAreNotValidLogic(dataIn.strb,
                                                     itemCntr,
                                                     ITEMS,
                                                     OUT_DW)
        if strbLastOverride is not True:
            isLastItem = isLastItem | strbLastOverride

        # connected item selected by itemCntr to output
        for inp, outp in zip(dIn, dOut):
            w = outp._dtype.bit_length()
            Switch(itemCntr)\
            .addCases([
                    (wordIndx, outp(inp[((wordIndx + 1) * w):(w * wordIndx)]))
                    for wordIndx in range(ITEMS)
            ])\
            .Default(
                outp(None)
            )

        # connect others signals directly
        for inp, outp in zip(self.get_data(dataIn), self.get_data(self.dataOut)):
            if inp not in dIn and inp is not dataIn.last:
                outp(inp)

        self.dataOut.last(dataIn.last & isLastItem)
        self.get_ready_signal(dataIn)(self.get_ready_signal(self.dataOut)
                           & isLastItem & dataIn.valid)
        self.get_valid_signal(self.dataOut)(self.get_valid_signal(dataIn))

        If(hs,
           If(isLastItem,
               itemCntr(0)
           ).Else(
               itemCntr(itemCntr + 1)
           )
        )

    def _impl(self):
        IN_DW = int(self.DATA_WIDTH)
        OUT_DW = int(self.OUT_DATA_WIDTH)

        if IN_DW < OUT_DW:  # UPSCALE
            self.upscale(IN_DW, OUT_DW)
        elif IN_DW > OUT_DW:  # DOWNSCALE
            self.downscale(IN_DW, OUT_DW)
        else:  # same
            raise AssertionError(
                "Input and output width are same, this instance is useless")


def _example_AxiS_resizer_upscale():
    from hwtLib.amba.axis import AxiStream

    u = AxiS_resizer(AxiStream)
    u.ID_WIDTH = 3
    u.DATA_WIDTH = 32
    u.OUT_DATA_WIDTH = 64

    return u


def _example_AxiS_resizer_downscale():
    from hwtLib.amba.axis import AxiStream

    u = AxiS_resizer(AxiStream)
    u.ID_WIDTH = 3
    u.DATA_WIDTH = 64
    u.OUT_DATA_WIDTH = 32

    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiS_resizer_downscale()
    print(toRtl(u))
