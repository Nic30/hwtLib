from hwt.synthesizer.interface import Interface
from hwt.interfaces.std import Clk
from hwt.interfaces.tristate import TristateSig
from pyMathBitPrecise.bit_utils import mask, get_bit
from hwt.synthesizer.param import Param
from hwt.simulator.agentBase import SyncAgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.process_utils import OnRisingCallbackLoop, OnFallingCallbackLoop
from collections import deque
from typing import Deque, Tuple
from hwtSimApi.triggers import WaitWriteOnly, WaitCombStable,\
    Edge, Timer
from hwtSimApi.constants import Time
from hwtSimApi.simCalendar import DONE
from ipCorePackager.intfIpMeta import IntfIpMeta
from hwt.hdl.types.bits import Bits


class Mdio(Interface):
    """
    Management Data Input/Output (MDIO), also known as Serial Management Interface (SMI)
    or Media Independent Interface Management (MIIM), is a serial bus defined
    for the Ethernet family of IEEE 802.3 standards for the Media Independent Interface,

    :note: Typical clock frequency is 2.5 MHz

    * MDIO packet format: <PRE><ST><OP><PA><RA><TA><D>

        * PRE: 32b preamble
        * ST: 2b start field
        * OP: 2b operation code
        * PA: 5b PHY address
        * RA: 5b register address
        * TA: 2b turn arround
        * D 16b data

    :note: When data is being written to the slave, the master writes '10' to the MDIO line.
        When data is being read, the master releases the MDIO line and slave sets the second bit to 1.

    .. hwt-autodoc::
    """
    # http://ww1.microchip.com/downloads/en/devicedoc/00002165b.pdf
    PRE_W = 32
    ST_W = 2
    OP_W = 2
    PA_W = 5
    RA_W = 5
    TA_W = 2
    ADDR_BLOCK_W = ST_W + OP_W + PA_W + RA_W
    D_W = 16

    PRE = Bits(PRE_W).from_py(mask(PRE_W))
    ST = Bits(ST_W).from_py(0b01)
    TA = Bits(TA_W).from_py(0b10)

    class OP:
        READ = 0b10
        WRITE = 0b01

    DEFAULT_FREQ = int(2.5e6)

    def _config(self):
        self.FREQ = Param(self.DEFAULT_FREQ)

    def _declr(self):
        self.c = Clk()
        self.c.FREQ = self.FREQ
        with self._associated(clk=self.c):
            self.io = TristateSig()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = MdioAgent(sim, self)

    def _getIpCoreIntfClass(self):
        return IP_mdio


def pop_int(bits: Deque[int], bit_cnt: int):
    res = 0
    for _ in range(bit_cnt):
        b = bits.popleft()
        res <<= 1
        res |= b
    return res


class MdioAgent(SyncAgentBase):
    PULL = 1

    def __init__(self, sim: HdlSimulator, intf, allowNoReset=False,
                 wrap_monitor_and_driver_in_edge_callback=True):
        super(MdioAgent, self).__init__(sim, intf, allowNoReset=allowNoReset,
                                        wrap_monitor_and_driver_in_edge_callback=False)
        self.intf.io._initSimAgent(sim)
        if wrap_monitor_and_driver_in_edge_callback:
            self.rx_bits = OnRisingCallbackLoop(
                sim, intf.c, self.rx_bits, lambda: True)
            self.tx_bits = OnFallingCallbackLoop(
                sim, intf.c, self.tx_bits, lambda: True)
        self.rx_bits_tmp = deque()
        self.tx_bits_tmp = deque()
        self.reset_state()
        self.data = {}

    def reset_state(self):
        self.preamble_detected = False
        self.start_detected = False
        self.turn_arround_check = False
        self.rx_w_data = False
        # (opcode, phyaddr, regaddr)
        self.acutal_req = (None, None, None)

    def on_read(self, phyaddr, regaddr):
        data = self.data[(phyaddr, regaddr)]
        D_W = self.intf.D_W
        tx_bits = self.tx_bits_tmp
        # turn arround (1 is actually Z but due to open-drain...)
        tx_bits.append(1)
        tx_bits.append(0)
        for i in range(D_W):
            # MSB first
            tx_bits.append(get_bit(data, D_W - i - 1))
        #print(tx_bits)

    def on_write(self, phyaddr, regaddr, data):
        self.data[(phyaddr, regaddr)] = data

    def tx_bits(self):
        """
        Transmit bit to io tristate signal on falling edge of c clock
        """
        if self.sim._current_time_slot.write_only is DONE:
            yield Timer(1)

        yield WaitWriteOnly()
        tx_bits = self.tx_bits_tmp
        if tx_bits:
            b = tx_bits.popleft()
            self.intf.io.i.write(b)
            if not tx_bits:
                yield Edge(self.intf.c)
                self.reset_state()
                # release the io bus
                if self.sim._current_time_slot.write_only is DONE:
                    yield Timer(1)
                    yield self.intf.io._ag.monitor()

    def unpack_addr(self, rx_bits) -> Tuple[int, int, int]:
        # <OP><PA><RA>
        mdio = self.intf
        op = pop_int(rx_bits, mdio.OP_W)
        pa = pop_int(rx_bits, mdio.PA_W)
        ra = pop_int(rx_bits, mdio.RA_W)
        return int(op), int(pa), int(ra)

    def rx_bits(self):
        """
        Recieve bit from io tristate signal on rising edge of c clock
        """
        yield WaitCombStable()
        rx_bits = self.rx_bits_tmp
        mdio = self.intf
        b = mdio.io._ag._read()
        b = int(b)
        # print(self.sim.now/ Time.ns, b)
        if not self.preamble_detected:
            rx_bits.append(b)
            if len(rx_bits) == Mdio.PRE_W:
                self.preamble_detected = True
                rx_bits.clear()
                #print(self.sim.now / Time.ns, "preamble_detected")

        elif not self.start_detected:
            if not rx_bits:
                if not b:
                    rx_bits.append(b)
                # else skip an extra 1 from potentiall idle or preamble
            else:
                # because start condition is 0b01
                assert b == 1, (self.sim.now / Time.ns, b)
                rx_bits.clear()
                self.start_detected = True
                #print(self.sim.now / Time.ns, "start_detected")

        elif self.turn_arround_check:
            rx_bits.append(b)
            if len(rx_bits) == mdio.TA_W:
                if self.acutal_req[0] != mdio.OP.READ:
                    assert rx_bits[0] == 1, rx_bits
                    assert rx_bits[1] == 0, rx_bits
                else:
                    self.rx_w_data = True
                rx_bits.clear()
                self.turn_arround_check = False
                #print(self.sim.now / Time.ns, "turn_arround_check_passed")

        elif self.rx_w_data:
            rx_bits.append(b)
            if len(rx_bits) >= mdio.D_W:
                data = pop_int(rx_bits, mdio.D_W)
                self.on_write(self.acutal_req[1], self.acutal_req[2], data)
                self.reset_state()
                #print(self.sim.now / Time.ns, "write_data_recieved")
                assert not rx_bits

        elif self.tx_bits_tmp:
            # responding with read data
            pass
        else:
            # <OP><PA><RA>
            rx_bits.append(b)
            if len(rx_bits) >= mdio.OP_W + mdio.PA_W + mdio.RA_W:
                opcode, phyaddr, regaddr = self.unpack_addr(rx_bits)
                self.acutal_req = (opcode, phyaddr, regaddr)

                if opcode == mdio.OP.READ:
                    #print(self.sim.now / Time.ns, ("READ",  phyaddr, regaddr))
                    self.on_read(phyaddr, regaddr)
                elif opcode == mdio.OP.WRITE:
                    self.rx_w_data = True
                    self.turn_arround_check = True
                    #print(self.sim.now / Time.ns, ("WRITE",  phyaddr, regaddr))
                else:
                    raise ValueError(opcode)

                rx_bits.clear()

    def getMonitors(self):
        return [
            *self.intf.io._ag.getMonitors(),
            self.rx_bits(),
            self.tx_bits(),
        ]


class IP_mdio(IntfIpMeta):

    def __init__(self):
        super().__init__()
        self.name = "mdio"
        self.version = "1.0"
        self.vendor = "xilinx.com"
        self.library = "interface"
        self.map = {"c": "MDC",
                    "io": {"t": "MDIO_T",
                           "i": "MDIO_I",
                           "o": "MDIO_O"}
                    }
