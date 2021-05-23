from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from ipCorePackager.constants import DIRECTION


class MIG_CMD():
    WRITE = 0b000
    READ = 0b001
    WR_BYTES = 0b011


class MigUserPortWDF(Interface):

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        # DDR data to write
        self.data = VectSignal(self.DATA_WIDTH)
        # DDR write burst end
        self.end = Signal()
        # DDR mask of data to write (select which bytes will be written)
        self.mask = VectSignal(self.DATA_WIDTH // 8)
        # DDR write enable
        self.wren = Signal()
        # DDR driver is ready to accept write request
        self.rdy = Signal(masterDir=DIRECTION.IN)


class MigUserPortRD(Interface):

    def _config(self):
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        # DDR read dataslv_array_2d_t
        self.data = VectSignal(self.DATA_WIDTH)
        # DDR read burst end
        self.end = Signal()
        # DDR read data valid
        self.valid = Signal()


class MigUserPort(Interface):
    """
    Interface used to control Xilinx MIG (Memory Interface Generator) DDR4 controller

    https://www.xilinx.com/support/documentation/ip_documentation/ultrascale_memory_ip/v1_4/pg150-ultrascale-memory-ip.pdf
    p. 122
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        IN = DIRECTION.IN
        # Calibration complete
        self.calib_complete = Signal(masterDir=IN)
        # DDR address
        self.addr = VectSignal(self.ADDR_WIDTH)
        # DDR command
        self.cmd = VectSignal(3)
        # DDR enable signal
        self.en = Signal()
        # DDR driver is ready to accept read request
        self.RDY = Signal(masterDir=IN)
        with self._paramsShared():
            # data write channel
            self.wdf = MigUserPortWDF()
            # data read channel
            self.rd = MigUserPortRD(masterDir=IN)
