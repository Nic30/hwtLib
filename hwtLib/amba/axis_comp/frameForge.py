from hwt.bitmask import mask
from hwt.code import log2ceil, Switch, If, isPow2, In
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.byteOrder import reverseByteOrder
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.amba.axis_comp.templateBasedUnit import TemplateBasedUnit
from hwtLib.handshaked.streamNode import streamSync, streamAck


class AxiS_frameForge(AxiSCompBase, TemplateBasedUnit):
    """
    Assemble fields into frame on axi stream interface

    .. aafig::
        +---------+
        | field0  +------+
        +---------+      |
                       +-v-------+
        +---------+    |         | output stream
        | field1  +---->  forge  +--------------->
        +---------+    |         |
                       +-^-------+
        +---------+      |
        | field2  +------+
        +---------+

    :note: names in the picture are just illustrative
    """
    def __init__(self, axiSIntfCls, structT,
                 tmpl=None, frames=None):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        :param structT: instance of HStruct used as template for this frame
            if name is None no input port is generated and space is filled with invalid values
            litle-endian encoding,
            supported types of interfaces are: Handshaked, Signal
            can be also instance of FrameTemplate
        :param tmpl: instance of TransTmpl for this structT
        :param frames: list of FrameTemplate instances for this tmpl
        :note: if tmpl and frames are None they are resolved from structT parseTemplate
        :note: this unit can parse sequence of frames, if they are specified by "frames"
        :note: structT can contain fields with variable size like HStream
        """
        if axiSIntfCls is not AxiStream:
            raise NotImplementedError()

        self._structT = structT
        self._tmpl = tmpl
        self._frames = frames

        AxiSCompBase.__init__(self, axiSIntfCls)

    @staticmethod
    def _mkFieldIntf(structIntf, frameTemplateItem):
        p = Handshaked()
        p.DATA_WIDTH.set(frameTemplateItem.dtype.bit_length())
        return p

    def _declr(self):
        addClkRstn(self)
        self.parseTemplate()
        with self._paramsShared():
            self.dataOut = self.intfCls()
        self.dataIn = StructIntf(self._structT, self._mkFieldIntf)

    def _impl(self):
        words = list(self.chainFrameWords())
        dout = self.dataOut
        if self.IS_BIGENDIAN:
            byteOrderCare = reverseByteOrder
        else:
            def byteOrderCare(sig):
                return sig

        self.parseTemplate()
        maxWordIndex = words[-1][0]
        useCounter = maxWordIndex > 0
        if useCounter:
            # multiple word frame
            wordCntr_inversed = self._reg("wordCntr_inversed",
                                          vecT(log2ceil(maxWordIndex + 1), False),
                                          defVal=maxWordIndex)
            wcntrSw = Switch(wordCntr_inversed)

        endsOfFrames = []
        for i, transactionParts, last in words:
            inversedI = maxWordIndex - i

            inPorts = []
            lastInPorts = []
            wordData = self._sig("word%d" % i, dout.data._dtype)

            for tPart in transactionParts:
                high, low = tPart.getBusWordBitRange()
                if tPart.isPadding:
                    wordData[high:low] ** None
                else:
                    intf = self.dataIn._fieldsToInterfaces[tPart.tmpl.origin]
                    fhigh, flow = tPart.getFieldBitRange()
                    wordData[high:low] ** byteOrderCare(intf.data)[fhigh:flow]
                    inPorts.append(intf)
                    if tPart.isLastPart():
                        lastInPorts.append(intf)

            if useCounter:
                if i == maxWordIndex:
                    nextWordIndex = maxWordIndex
                else:
                    nextWordIndex = wordCntr_inversed - 1

            if lastInPorts:
                # input ready logic
                wordEnConds = {}
                for intf in lastInPorts:
                    wordEnConds[intf] = dout.ready
                    if useCounter:
                        c = wordEnConds[intf]
                        wordEnConds[intf] = c & wordCntr_inversed._eq(inversedI)

                streamSync(masters=lastInPorts,
                           # slaves=[dout],
                           extraConds=wordEnConds)

            if inPorts:
                ack = streamAck(masters=inPorts)
            else:
                ack = 1

            if useCounter:
                # word cntr next logic
                if ack is 1:
                    _ack = dout.ready
                else:
                    _ack = ack & dout.ready
                a = If(_ack,
                       wordCntr_inversed ** nextWordIndex
                    )
            else:
                a = []

            a.extend(dout.valid ** ack)
            # data out logic
            a.extend(dout.data ** wordData)

            if useCounter:
                wcntrSw.Case(inversedI, a)

            if last:
                endsOfFrames.append(inversedI)

        # to prevent latches
        if not useCounter:
            pass
        elif not isPow2(maxWordIndex + 1):
            default = wordCntr_inversed ** maxWordIndex
            default.extend(dout.valid ** 0)
            default.extend(dout.data ** None)

            wcntrSw.Default(default)

        if useCounter:
            dout.last ** In(wordCntr_inversed, endsOfFrames)
        else:
            dout.last ** 1

        dout.strb ** mask(int(self.DATA_WIDTH // 8))


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t
    u = AxiS_frameForge(AxiStream,
                        # tuples (type, name) where type has to be instance of Bits type
                        HStruct(
                            (uint64_t, "item0"),
                            (uint64_t, None),  # name = None means field is padding
                            (uint64_t, "item1"),
                            (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
                        )
                        )
    u.DATA_WIDTH.set(64)
    print(toRtl(u))
    print(u._frames)
