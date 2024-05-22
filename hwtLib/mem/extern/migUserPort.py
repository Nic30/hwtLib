from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from ipCorePackager.constants import DIRECTION


class MIG_CMD():
    WRITE = 0b000
    READ = 0b001
    WR_BYTES = 0b011


class MigUserPortWDF(HwIO):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        # DDR data to write
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        # DDR write burst end
        self.end = HwIOSignal()
        # DDR mask of data to write (select which bytes will be written)
        self.mask = HwIOVectSignal(self.DATA_WIDTH // 8)
        # DDR write enable
        self.wren = HwIOSignal()
        # DDR driver is ready to accept write request
        self.rdy = HwIOSignal(masterDir=DIRECTION.IN)


class MigUserPortRD(HwIO):

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        # DDR read dataslv_array_2d_t
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        # DDR read burst end
        self.end = HwIOSignal()
        # DDR read data valid
        self.valid = HwIOSignal()


class MigUserPort(HwIO):
    """
    HwIO used to control Xilinx MIG (Memory HwIO Generator) DDR4 controller

    https://www.xilinx.com/support/documentation/ip_documentation/ultrascale_memory_ip/v1_4/pg150-ultrascale-memory-ip.pdf
    p. 122
    """

    @override
    def hwConfig(self):
        self.DATA_WIDTH = HwParam(64)
        self.ADDR_WIDTH = HwParam(32)

    @override
    def hwDeclr(self):
        IN = DIRECTION.IN
        # Calibration complete
        self.calib_complete = HwIOSignal(masterDir=IN)
        # DDR address
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        # DDR command
        self.cmd = HwIOVectSignal(3)
        # DDR enable signal
        self.en = HwIOSignal()
        # DDR driver is ready to accept read request
        self.RDY = HwIOSignal(masterDir=IN)
        with self._hwParamsShared():
            # data write channel
            self.wdf = MigUserPortWDF()
            # data read channel
            self.rd = MigUserPortRD(masterDir=IN)
