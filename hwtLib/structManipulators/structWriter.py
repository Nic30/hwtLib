#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import StaticForEach
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_comp.axi_datapump_intf import AxiWDatapumpIntf
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.structManipulators.structReader import StructReader


SKIP = 1
PROPAGATE = 0


class StructWriter(StructReader):
    """
    Write struct specified in constructor over wDatapump interface on address
    specified over set interface

    :ivar MAX_OVERLAP: parameter which specifies the maximum number of concurrent transaction
    :ivar WRITE_ACK: Param, if true ready on "set" will be set only
        when component is in idle (if false "set"
        is regular handshaked interface)

    .. aafig::
            set (base addr)          +---------+
         +----------------    +------> field0  |
                         |    |      +---------+
           bus w req  +--v---+-+
         <------------+         |    +---------+
           bus w data |         +----> field1  |
         <------------+ reader  |    +---------+
           bus w ack  |         |
         +------------>         |
                      +-------+-+
                              |      +---------+
                              +------> field2  |
                                     +---------+

    :note: names in the picture are just illustrative

    .. hwt-schematic:: _example_StructWriter
    """
    def _config(self):
        StructReader._config(self)
        self.MAX_OVERLAP = Param(2)
        self.WRITE_ACK = Param(False)

    def _createInterfaceForField(self, parent, structField):
        return AxiS_frameForge._mkFieldIntf(parent, structField)

    def _declr(self):
        addClkRstn(self)
        self.parseTemplate()
        self.dataIn = StructIntf(self._structT,
                                 self._createInterfaceForField)

        s = self.set = Handshaked()  # data signal is addr of structure to write
        s.DATA_WIDTH = self.ADDR_WIDTH
        # write ack from slave
        self.writeAck = HandshakeSync()._m()

        with self._paramsShared():
            # interface for communication with datapump
            self.wDatapump = AxiWDatapumpIntf()._m()
            self.wDatapump.MAX_LEN = self.maxWordIndex() + 1

        self.frameAssember = AxiS_frameForge(self._structT,
                                             tmpl=self._tmpl,
                                             frames=self._frames)

    def _impl(self):
        req = self.wDatapump.req
        w = self.wDatapump.w
        ack = self.wDatapump.ack

        # multi frame
        ackPropageteInfo = HandshakedFifo(Handshaked)
        ackPropageteInfo.DATA_WIDTH = 1
        ackPropageteInfo.DEPTH = self.MAX_OVERLAP
        self.ackPropageteInfo = ackPropageteInfo
        propagateClkRstn(self)

        if self.WRITE_ACK:
            _set = self.set
        else:
            _set = HsBuilder(self, self.set).buff().end

        req.id(self.ID)
        req.rem(0)

        def propagateRequests(frame, indx):
            ack = StreamNode(slaves=[req, ackPropageteInfo.dataIn]).ack()
            statements = [req.addr(_set.data + frame.startBitAddr // 8),
                          req.len(frame.getWordCnt() - 1),
                          StreamNode(slaves=[req, ackPropageteInfo.dataIn],
                                     ).sync(_set.vld)
                          ]
            if indx != 0:
                prop = SKIP
            else:
                prop = PROPAGATE

            statements.append(ackPropageteInfo.dataIn.data(prop))

            isLastFrame = indx == len(self._frames) - 1
            if isLastFrame:
                statements.append(_set.rd(ack))
            else:
                statements.append(_set.rd(0))

            return statements, ack & _set.vld

        StaticForEach(self, self._frames, propagateRequests)

        # connect write channel
        w(self.frameAssember.dataOut)

        # propagate ack
        StreamNode(masters=[ack, ackPropageteInfo.dataOut],
                   slaves=[self.writeAck],
                   skipWhen={
                             self.writeAck: ackPropageteInfo.dataOut.data._eq(PROPAGATE)
                            }).sync()

        # connect fields to assembler
        for _, transTmpl in self._tmpl.walkFlatten():
            f = transTmpl.origin
            intf = self.frameAssember.dataIn._fieldsToInterfaces[f]
            intf(self.dataIn._fieldsToInterfaces[f])


def  _example_StructWriter():
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t

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
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_StructWriter()
    print(toRtl(u))
