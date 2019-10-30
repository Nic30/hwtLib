from hwt.hdl.types.structUtils import HStruct_unpack
from hwt.interfaces.std import Signal, VectSignal
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.amba.axi_intf_common import Axi_user, Axi_id, Axi_hs, Axi_strb
from hwtLib.amba.sim.agentCommon import BaseAxiAgent
from ipCorePackager.intfIpMeta import IntfIpMeta
from pyMathBitPrecise.bit_utils import mask
from pycocotb.hdlSimulator import HdlSimulator


# http://www.xilinx.com/support/documentation/ip_documentation/ug761_axi_reference_guide.pdf
class AxiStream(Axi_hs, Axi_id, Axi_user, Axi_strb):
    """
    AMBA AXI-stream interface

    :ivar IS_BIGENDIAN: Param which specifies if interface uses bigendian
        byte order or litleendian byte order

    :ivar HAS_STRB: if set strb signal is present
    :ivar HAS_KEEP: if set keep signal is present
    :ivar ID_WIDTH: if > 0 id signal is present and this is it's width
    :ivar DEST_WIDTH: if > 0 dest signal is present and this is it's width

    :attention: no checks are made for endianity, this is just information
    :note: bigendian for interface means that items which are send through
        this interface have reversed byte endianity.
        That means that most significant byte is is on lower address
        than les significant ones
        f.e. litle endian value 0x1a2b will be 0x2b1a
        but iterface itselelf is not reversed in any way

    :ivar DATA_WIDTH: Param which specifies width of data signal
    :ivar id: optional signal wich specifies id of transaction
    :ivar dest: optional signal which specifies destination of transaction
    :ivar data: main data signal
    :ivar keep: optional signal which signalize which bytes
                should be keept and which should be discarted
    :ivar strb: optional signal which signalize which bytes are valid
    :ivar last: signal which if high this data is last in this frame
    """

    def _config(self):
        self.IS_BIGENDIAN = Param(False)
        self.USE_STRB = Param(False)
        self.USE_KEEP = Param(False)

        Axi_id._config(self)
        self.DEST_WIDTH = Param(0)
        self.DATA_WIDTH = Param(64)
        Axi_user._config(self)

    def _declr(self):
        Axi_id._declr(self)

        if self.DEST_WIDTH:
            self.dest = VectSignal(self.DEST_WIDTH)

        self.data = VectSignal(self.DATA_WIDTH)

        if self.USE_STRB:
            Axi_strb._declr(self)

        if self.USE_KEEP:
            self.keep = VectSignal(self.DATA_WIDTH // 8)

        Axi_user._declr(self)
        self.last = Signal()

        super(AxiStream, self)._declr()

    def _getIpCoreIntfClass(self):
        return IP_AXIStream

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AxiStreamAgent(sim, self)


class AxiStreamAgent(BaseAxiAgent):
    """
    Simulation agent for :class:`.AxiStream` interface

    input/output data stored in list under "data" property
    data contains tuples

    Format of data tules is derived from signals on AxiStream interface
    Order of values coresponds to definition of interface signals.
    If all signals are present fotmat of tuple will be
    (id, dest, data, strb, keep, user, last)


    :ivar _signals: tuple of data signals of this interface
    :ivar _sigCnt: len(_signals)
    """

    def __init__(self, sim: HdlSimulator, intf: AxiStream, allowNoReset=False):
        BaseAxiAgent.__init__(self, sim, intf, allowNoReset=allowNoReset)

        signals = []
        for i in intf._interfaces:
            if i is not intf.ready and i is not intf.valid:
                signals.append(i)
        self._signals = tuple(signals)
        self._sigCnt = len(signals)

    def get_data(self):
        return tuple(sig.read() for sig in self._signals)

    def set_data(self, data):
        if data is None:
            for sig in self._signals:
                sig.write(None)
        else:
            assert len(data) == self._sigCnt, (len(data),
                                               self._signals, self.intf._getFullName())
            for sig, val in zip(self._signals, data):
                sig.write(val)


def packAxiSFrame(dataWidth, structVal, withStrb=False):
    """
    pack data of structure into words on axis interface
    """
    if withStrb:
        maskAll = mask(dataWidth // 8)

    words = iterBits(structVal, bitsInOne=dataWidth,
                     skipPadding=False, fillup=True)
    for last, d in iter_with_last(words):
        assert d._dtype.bit_length() == dataWidth, d._dtype.bit_length()
        if withStrb:
            # [TODO] mask in last resolved from size of datatype,
            #        mask for padding
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


class IP_AXIStream(IntfIpMeta):
    """
    Class which specifies how to describe AxiStream interfaces in IP-core
    """

    def __init__(self):
        super().__init__()
        self.name = "axis"
        self.quartus_name = "axi4stream"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {
            'id': "TID",
            'dest': "TDEST",
            'data': "TDATA",
            'strb': "TSTRB",
            'keep': "TKEEP",
            'user': 'TUSER',
            'last': "TLAST",
            'valid': "TVALID",
            'ready': "TREADY"
        }
        self.quartus_map = {
            k: v.lower() for k, v in self.map.items()
        }
