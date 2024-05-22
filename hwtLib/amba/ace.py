from hwt.hwIOs.std import HwIOVectSignal, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi3Lite import Axi3Lite_bAgent
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi_common import Axi_hs
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class DOMAIN():
    NON_SHARABLE = 0
    INNER_SHARABLE = 1
    OUTER_SHARABLE = 2
    SYSTEM = 3


class CACHE():
    DEVICE = 0
    NON_CACHEABLE = 0b0011
    WRITE_THROUGH = 0b0111
    WRITE_BACK = 0b1011


class BAR():
    NORMAL = 0b00
    BARRIER = 0b01
    IGNORE = 0b10
    SYNCHRONIZATION = 0b11


class AR_MODE():

    class NO_SNOOP():

        class READ():
            NON = (BAR.NORMAL, DOMAIN.NON_SHARABLE, 0b0000)
            SYSTEM = (BAR.NORMAL, DOMAIN.SYSTEM, 0b0000)

    class COHERENT():

        class READ_ONCE():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b0000)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b0000)

        class READ_SHARED():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b0001)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b0001)

        class READ_CLEAN():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b0010)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b0010)

        class READ_NOT_SHARED_DIRTY():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b0011)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b0011)

        class READ_UNIQUE():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b0111)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b0111)

        class CLEAN_UNIQUE():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1011)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1011)

        class MAKE_UNIQUE():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1100)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1100)

    class CACHE_MAINTENANCE():

        class CLEAN_SHARED():
            NON = (BAR.NORMAL, DOMAIN.NON_SHARABLE, 0b1000)
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1000)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1000)

        class CLEAN_INVALID():
            NON = (BAR.NORMAL, DOMAIN.NON_SHARABLE, 0b1001)
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1001)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1001)

        class MAKE_INVALID():
            NON = (BAR.NORMAL, DOMAIN.NON_SHARABLE, 0b1101)
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1101)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1101)

    class BARRIER():
        NON = (BAR.BARRIER, DOMAIN.NON_SHARABLE, 0b0000)
        INNER = (BAR.BARRIER, DOMAIN.INNER_SHARABLE, 0b0000)
        OUTER = (BAR.BARRIER, DOMAIN.OUTER_SHARABLE, 0b0000)
        SYSTEM = (BAR.BARRIER, DOMAIN.SYSTEM, 0b0000)

    class DVM():

        class COMPLETE():
            INNER = (BAR.NORMAL, DOMAIN.INNER_SHARABLE, 0b1110)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1110)

        class MESSAGE():
            INNER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1111)
            OUTER = (BAR.NORMAL, DOMAIN.OUTER_SHARABLE, 0b1111)


def setAceArMode(arbar, ardomain, arsnoop, transactionType):
    bar, dom, snoop = transactionType
    arbar(bar)
    ardomain(dom)
    arsnoop(snoop)


class Ace_addr(Axi4_addr):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        Axi4_addr.hwDeclr(self)
        self.domain = HwIOVectSignal(2)
        self.region = HwIOVectSignal(4)
        self.snoop = HwIOVectSignal(3)
        self.bar = HwIOVectSignal(2)


class AceSnoop_addr(Axi_hs):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.SNOOP_ADDR_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.SNOOP_ADDR_WIDTH)
        self.snoop = HwIOVectSignal(4)
        self.prot = HwIOVectSignal(3)
        Axi_hs.hwDeclr(self)


class AceSnoop_resp(Axi_hs):
    """
    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        self.resp = HwIOVectSignal(4)
        Axi_hs.hwDeclr(self)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi3Lite_bAgent(sim, self)


class AceSnoop_data(Axi_hs):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.SNOOP_DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        self.data = HwIOVectSignal(self.SNOOP_DATA_WIDTH)
        self.last = HwIOSignal()
        Axi_hs.hwDeclr(self)


class Ace(Axi4):
    """
    :ivar ac: Coherent address channel.
        snoop address input to the master
    :ivar cr: Coherent response channel.
        used by the master to signal the response to snoops to the interconnect
    :ivar cd: Coherent data channel.
        output from the master to transfer snoop data

    https://static.docs.arm.com/ihi0022/d/IHI0022D_amba_axi_protocol_spec.pdf

    .. hwt-autodoc::
    """
    AW_CLS = Ace_addr
    AR_CLS = Ace_addr

    @override
    def hwConfig(self):
        Axi4.hwConfig(self)
        self.SNOOP_ADDR_WIDTH = HwParam(32)
        self.SNOOP_DATA_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        super(Ace, self).hwDeclr()
        with self._hwParamsShared():
            self.ac = AceSnoop_addr(masterDir=DIRECTION.IN)
            self.cr = AceSnoop_resp()
            self.cd = AceSnoop_data()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()

    @override
    def _getIpCoreIntfClass(self):
        raise NotImplementedError()
