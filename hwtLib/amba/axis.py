from hwt.bitmask import mask
from hwt.hdlObjects.types.structUtils import HStruct_unpack
from hwt.interfaces.std import Signal, VectSignal
from hwt.pyUtils.arrayQuery import iter_with_last, take
from hwt.serializer.ip_packager.interfaces.intfConfig import IntfConfig
from hwt.synthesizer.param import Param
from hwtLib.amba.axi_intf_common import Axi_user, Axi_id, Axi_strb, Axi_hs
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from hwt.synthesizer.vectorUtils import iterBits


# http://www.xilinx.com/support/documentation/ip_documentation/ug761_axi_reference_guide.pdf
class AxiStream_withoutSTRB(Axi_hs):
    """
    Bare AMBA AXI-stream interface

    :ivar IS_BIGENDIAN: Param which specifies if interface uses bigendian byte order or litleendian byte order
    :attention: no checks are made for endianity, this is just information
    :note: bigendian for interface means that items which are send through this interface has reversed byte endianity
        that means that most significant byte is is on lower address than les significant ones
        f.e. litle endian value 0x1a2b will be 0x2b1a
        but iterface itselelf is not reversed in any way

    :ivar DATA_WIDTH: Param which specifies width of data signal
    :ivar data: main data signal
    :ivar last: signal which if high this data is last in this frame
    """
    def _config(self):
        self.IS_BIGENDIAN = Param(False)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        super(AxiStream_withoutSTRB, self)._declr()
        self.data = VectSignal(self.DATA_WIDTH)
        self.last = Signal()

    def _getIpCoreIntfClass(self):
        return IP_AXIStream

    def _getSimAgent(self):
        return AxiStream_withoutSTRBAgent


class AxiStream_withoutSTRBAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.AxiStream_withoutSTRB` interface

    input/output data stored in list under "data" property
    data contains tuples (data, strb, last)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read

        data = r(intf.data)
        last = r(intf.last)

        return (data, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            _data, last = None, None
        else:
            _data, last = data

        w(_data, intf.data)
        w(last, intf.last)


class AxiStream(AxiStream_withoutSTRB, Axi_strb):
    """
    :class:`.AxiStream_withoutSTRB` with strb signal

    :ivar strb: byte strobe signal, has bit for each byte of data,
        data valid if corresponding bit ins strb signal is high
    """
    def _config(self):
        AxiStream_withoutSTRB._config(self)
        Axi_strb._config(self)

    def _declr(self):
        AxiStream_withoutSTRB._declr(self)
        Axi_strb._declr(self)

    def _getSimAgent(self):
        return AxiStreamAgent


class AxiStream_withUserAndNoStrb(AxiStream_withoutSTRB, Axi_user):
    """
    :class:`.AxiStream_withoutSTRB` with user signal

    :ivar user: generic signal with user specified meaning
    """
    def _config(self):
        AxiStream_withoutSTRB._config(self)
        Axi_user._config(self)

    def _declr(self):
        AxiStream_withoutSTRB._declr(self)
        Axi_user._declr(self)


class AxiStream_withId(Axi_id, AxiStream):
    """
    :class:`.AxiStream` with id signal

    :ivar id: id signal, usually identifies type or destination of frame
    """
    def _config(self):
        Axi_id._config(self)
        AxiStream._config(self)

    def _declr(self):
        Axi_id._declr(self)
        AxiStream._declr(self)

    def _getSimAgent(self):
        return AxiStream_withIdAgent


class AxiStream_withUserAndStrb(AxiStream, Axi_user):
    """
    :class:`.AxiStream` with user signal

    :ivar user: generic signal with user specified meaning
    """
    def _config(self):
        AxiStream._config(self)
        Axi_user._config(self)

    def _declr(self):
        AxiStream._declr(self)
        Axi_user._declr(self)

    def _getSimAgent(self):
        return AxiStream_withUserAndStrbAgent


class AxiStreamAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.AxiStream` interface

    input/output data stored in list under "data" property
    data contains tuples (data, strb, last)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read

        data = r(intf.data)
        strb = r(intf.strb)
        last = r(intf.last)

        return (data, strb, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(3)]

        _data, strb, last = data

        w(_data, intf.data)
        w(strb, intf.strb)
        w(last, intf.last)


class AxiStream_withIdAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.AxiStream_withId` interface

    input/output data stored in list under "data" property
    data contains tuples (id, data, strb, last)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read

        _id = r(intf.id)
        data = r(intf.data)
        strb = r(intf.strb)
        last = r(intf.last)

        return (_id, data, strb, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(4)]

        _id, data, strb, last = data

        w(_id, intf.id)
        w(data, intf.data)
        w(strb, intf.strb)
        w(last, intf.last)


class AxiStream_withUserAndStrbAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.AxiStream_withUserAndStrb` interface

    input/output data stored in list under "data" property
    data contains tuples (data, strb, user, last)
    """
    def doRead(self, s):
        intf = self.intf
        r = s.read

        data = r(intf.data)
        strb = r(intf.strb)
        user = r(intf.user)
        last = r(intf.last)

        return (data, strb, user, last)

    def doWrite(self, s, data):
        intf = self.intf
        w = s.write

        if data is None:
            data = [None for _ in range(4)]

        data, strb, user, last = data

        w(data, intf.data)
        w(strb, intf.strb)
        w(user, intf.user)
        w(last, intf.last)


def packAxiSFrame(dataWidth, structVal, withStrb=False):
    """
    pack data of structure into words on axis interface
    """
    if withStrb:
        maskAll = mask(dataWidth // 8)

    words = iterBits(structVal, bitsInOne=dataWidth, skipPadding=False, fillup=True)
    for last, d in iter_with_last(words):
        assert d._dtype.bit_length() == dataWidth, d._dtype.bit_length()
        if withStrb:
            # [TODO] mask in last resolved from size of datatype, mask for padding
            yield (d, maskAll, last)
        else:
            yield (d, last)


def unpackAxiSFrame(structT, frameData, getDataFn=None, dataWidth=None):
    """
    opposite of packAxiSFrame
    """
    if getDataFn is None:
        def _getDataFn(x):
            return x[0]

        getDataFn = _getDataFn

    return HStruct_unpack(structT, frameData, getDataFn, dataWidth)


def axiSFrame_toBytes(intf, frameData):
    """
    Unpack frame data to array of bytes

    :param intf: interface the frame comes from to resolve data format
    :param frameData: data collected by agent
    :return: array of bytes (of type Bits(8) ) (if interface has strb it is used in last to cut off unused bytes at the end)
    """

    bytesInWord = int(intf.DATA_WIDTH) // 8
    hasStrb = hasattr(intf, "strb")
    result = []

    bytesInThisWord = bytesInWord
    for d in frameData:
        if hasStrb:
            data, strb, last = d

            if last:
                bytesInThisWord = strb.val.bit_length()
            else:
                bytesInThisWord = bytesInWord
        else:
            data, last = d

        result.extend(take(iterBits(data, bitsInOne=8), bytesInThisWord))

    return result


class IP_AXIStream(IntfConfig):
    """
    Class which specifies how to describe AxiStream interfaces in IP-core
    """
    def __init__(self):
        super().__init__()
        self.name = "axis"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {'id': "TID",
                    'data': "TDATA",
                    'last': "TLAST",
                    'valid': "TVALID",
                    'strb': "TSTRB",
                    'keep': "TKEEP",
                    'user': 'TUSER',
                    'ready': "TREADY"
                    }
