from hwt.bitmask import mask
from hwt.code import log2ceil, Switch, If, isPow2
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import evalParam
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamSync, streamAck
from hwt.hdlObjects.types.structUtils import FrameTemplate


class AxiS_frameForge(AxiSCompBase):
    """
    Assemble fields into frame on axi stream interface
    """
    def __init__(self, axiSIntfCls, structT):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        :param structT: instance of HStruct used as template for this frame
            if name is None no input port is generated and space is filled with invalid values
            litle-endian encoding,
            supported types of interfaces are: Handshaked, Signal
        """
        if axiSIntfCls is not AxiStream:
            raise NotImplementedError()

        self._frameTemplate = FrameTemplate.fromHStruct(structT)

        assert self._frameTemplate
        AxiSCompBase.__init__(self, axiSIntfCls)

    def _declr(self):
        addClkRstn(self)
        self.dataOut = self.intfCls()
        for item in self._frameTemplate:
            if item.name is not None:
                ep = item.externalInterface
                if ep is not None:
                    p = ep.__class__()
                    setattr(self, item.name, p)
                    p._shareParamsWith(ep)
                else:
                    p = Handshaked()
                    p.DATA_WIDTH.set(item.type.bit_length())
                    setattr(self, item.name, p)
                item.internalInterface = p

    def _impl(self):
        dout = self.dataOut
        maxWordIndex = self._frameTemplate.resolveFieldPossitionsInFrame(evalParam(self.DATA_WIDTH).val) - 1
        if maxWordIndex == 0:
            # single word frame
            for i, recs in self._frameTemplate.walkWords():
                assert i == 0
                inPorts = []
                wordData = self._sig("word%d" % i, dout.data._dtype)

                for fi in recs:
                    assert fi.appearsInWords
                    for w, high, low in fi.appearsInWords:
                        if w == i:
                            if fi.internalInterface is None:
                                wordData[high:low] ** None
                            else:
                                intf = fi.internalInterface
                                wordData[high:low] ** intf.data
                                inPorts.append(intf)
            streamSync(masters=inPorts, slaves=[dout])
            dout.data ** wordData
            dout.last ** 1
            dout.strb ** mask(8)
        else:
            # multiple word frame
            wordCntr_inversed = self._reg("wordCntr_inversed",
                                          vecT(log2ceil(maxWordIndex + 1), False),
                                          defVal=maxWordIndex)

            wcntrSw = Switch(wordCntr_inversed)
            din = {}  # dict word index [] of interfaces
            for i, recs in self._frameTemplate.walkWords():
                inPorts = []
                wordData = self._sig("word%d" % i, dout.data._dtype)

                for fi in recs:
                    assert fi.appearsInWords
                    for w, high, low in fi.appearsInWords:
                        if w == i:
                            if fi.internalInterface is None:
                                wordData[high:low] ** None
                            else:
                                intf = fi.internalInterface
                                wordData[high:low] ** intf.data
                                inPorts.append(intf)
                                l = din.setdefault(i, [])
                                l.append(intf)
                if i == maxWordIndex:
                    v = maxWordIndex
                else:
                    v = wordCntr_inversed - 1

                if inPorts:
                    # input ready logic
                    wordEnConds = {}
                    for intf in inPorts:
                        wordEnConds[intf] = dout.ready & wordCntr_inversed._eq(maxWordIndex - i)

                    streamSync(masters=inPorts,
                               extraConds=wordEnConds)

                    # word cntr next logic
                    ack = streamAck(masters=inPorts, slaves=[dout])
                    a = If(ack,
                           wordCntr_inversed ** v
                        )
                else:
                    ack = 1
                    a = If(dout.ready,
                           wordCntr_inversed ** v
                        )
                a.extend(dout.valid ** ack)
                # data out logic
                a.extend(dout.data ** wordData)

                wcntrSw = wcntrSw.Case(maxWordIndex - i, a)

            # to prevent latches
            if not isPow2(maxWordIndex + 1):
                default = wordCntr_inversed ** maxWordIndex
                default.extend(dout.valid ** 0)
                default.extend(dout.data ** None)

                wcntrSw.Default(default)

            dout.last ** wordCntr_inversed._eq(0)
            dout.strb ** mask(8)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t
    from hwt.hdlObjects.types.struct import HStruct
    u = AxiS_frameForge(AxiStream,
                       # tuples (type, name) where type has to be instance of Bits type
                       HStruct((uint64_t, "item0"),
                        (uint64_t, None),  # name = None means this field will be ignored
                        (uint64_t, "item1"),
                        (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
                        )
                       )
    u.DATA_WIDTH.set(64)

    print(toRtl(u))
