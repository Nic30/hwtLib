#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import StaticForEach
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync, streamAck
from hwtLib.structManipulators.structReader import StructReader


SKIP = 1
PROPAGATE = 0


class StructWriter(StructReader):
    """
    Write struct specified in constructor over wDatapump interface on address
    specified over set interface

    :ivar MAX_OVERLAP: parameter which specifies the maximum number of concurrent transaction
    """
    def _config(self):
        StructReader._config(self)
        self.MAX_OVERLAP = Param(2)

    def _createInterfaceForField(self, structT, fInfo):
        i = Handshaked()
        i.DATA_WIDTH.set(fInfo.dtype.bit_length())
        fInfo.interface = i
        return i

    def _declr(self):
        addClkRstn(self)
        self.parseTemplate()
        self.dataIn = StructIntf(self._structT,
                                 self._createInterfaceForField)

        self.set = Handshaked()  # data signal is addr of structure to write
        self.set._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        # write ack from slave
        self.writeAck = HandshakeSync()

        with self._paramsShared():
            # interface for communication with datapump
            self.wDatapump = AxiWDatapumpIntf()
            self.wDatapump.MAX_LEN.set(self.maxWordIndex() + 1)

        self.frameAssember = AxiS_frameForge(AxiStream,
                                             self._structT,
                                             maxPaddingWords=self._maxPaddingWords)

    def _impl(self):
        propagateClkRstn(self)

        req = self.wDatapump.req
        w = self.wDatapump.w
        ack = self.wDatapump.ack

        req.id ** self.ID
        req.rem ** 0

        # multi frame
        ackPropageteInfo = HandshakedFifo(Handshaked)
        ackPropageteInfo.DATA_WIDTH.set(1)
        ackPropageteInfo.DEPTH.set(self.MAX_OVERLAP)
        self.ackPropageteInfo = ackPropageteInfo
        ackPropageteInfo.clk ** self.clk
        ackPropageteInfo.rst_n ** self.rst_n

        def propagateRequests(frame, indx):
            ack = streamAck(slaves=[req, ackPropageteInfo.dataIn])
            statements = [req.addr ** (self.set.data + frame.startBitAddr // 8),
                          req.len ** (frame.getWordCnt() - 1),
                          streamSync(slaves=[req, ackPropageteInfo.dataIn],
                                     extraConds={req: self.set.vld,
                                                 ackPropageteInfo.dataIn: self.set.vld})
                          ]
            if indx != 0:
                prop = SKIP
            else:
                prop = PROPAGATE

            statements += ackPropageteInfo.dataIn.data ** prop

            isLastFrame = indx == len(self._frames) - 1
            if isLastFrame:
                statements.append(self.set.rd ** ack)
            else:
                statements.append(self.set.rd ** 0)

            return statements, ack & self.set.vld

        StaticForEach(self, self._frames, propagateRequests)

        # connect write channel
        w ** self.frameAssember.dataOut

        # propagate ack
        streamSync(masters=[ack, ackPropageteInfo.dataOut],
                   slaves=[self.writeAck],
                   skipWhen={
                             self.writeAck: ackPropageteInfo.dataOut.data._eq(PROPAGATE)
                            })

        # connect fields to assembler
        for _, transTmpl in self._tmpl.walkFlatten():
            f = transTmpl.origin
            intf = self.frameAssember.dataIn._fieldsToInterfaces[f]
            intf ** self.dataIn._fieldsToInterfaces[f]


if __name__ == "__main__":
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t
    from hwt.synthesizer.shortcuts import toRtl

    s = HStruct(
            (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
            (uint64_t, None),  # name = None means this field will be ignored
            (uint64_t, "item1"),
            (uint64_t, None),
            (uint16_t, "item2"),
            (uint16_t, "item3"),
            (uint32_t, "item4"),
            (uint32_t, None),
            (uint64_t, "item5"),  # this word is split on two bus words
            (uint32_t, None),
            (uint64_t, None),
            (uint64_t, None),
            (uint64_t, None),
            (uint64_t, "item6"),
            (uint64_t, "item7"),
        )

    u = StructWriter(s)
    print(toRtl(u))
