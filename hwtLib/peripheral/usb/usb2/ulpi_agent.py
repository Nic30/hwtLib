from collections import deque

from hwt.simulator.agentBase import SyncAgentBase
from hwtLib.peripheral.usb.constants import USB_LINE_STATE
from hwtLib.peripheral.usb.usb2.ulpi import Ulpi, ulpi_reg_usb_interrupt_status_t, \
    ulpi_reg_usb_interrupt_status_t_reset_default, ULPI_TX_CMD
from hwtLib.types.ctypes import uint8_t
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.triggers import WaitWriteOnly, WaitCombRead
from pyMathBitPrecise.bit_utils import mask, ValidityError


class UlpiAgent(SyncAgentBase):
    """
    Agent for :class:`hwtLib.peripheral.usb.usb2.ulpi.Ulpi` interface.
    It allows for receiving and transmiting raw data over ULPI, it does not implement USB stack.

    :note: the RX is always from PHY to Link, the TX is always from Link to PHY
    :note: in link->phy nxt works as a handshake ready and stp as handshake valid_n
        and data is data.o

    :note in phy->link nxt works as a handshake valid (but when set to 0 rx_cmd is send instead of data)
        and the stp works as handshake ready_n, if stp is set to 1 the transmission of whole packet is interrupted.
    """

    def __init__(self, sim:HdlSimulator, intf: Ulpi, allowNoReset=False, wrap_monitor_and_driver_in_edge_callback=True):
        super(UlpiAgent, self).__init__(
            sim, intf, allowNoReset=allowNoReset,
            wrap_monitor_and_driver_in_edge_callback=wrap_monitor_and_driver_in_edge_callback)
        self.link_to_phy_packets = deque()
        self.phy_to_link_packets = deque()

        self.actual_link_to_phy_packet = None
        self.actual_phy_to_link_packet = None

        self.dir = Ulpi.DIR.PHY  # defalut state of the PHY in reset
        self.in_turnarround = False
        self.reg_interrupt = ulpi_reg_usb_interrupt_status_t.from_py(ulpi_reg_usb_interrupt_status_t_reset_default)
        self.RxEvent_RxActive = 0
        self.RxEvent_RxError = 0
        self.HostDisconnected = 0

    def on_link_to_phy_packet(self, packet: list):
        # [TODO] could be register write/read which needs to be processed
        self.link_to_phy_packets.append(packet)

    def on_phy_to_link_packet(self, packet: list):
        self.phy_to_link_packets.append(packet)

    def build_RX_CMD(self):
        LineState = USB_LINE_STATE.J
        inter = self.reg_interrupt
        if inter.SessEnd & ~inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b00
        elif ~inter.SessEnd & ~inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b01
        elif inter.SessValid & ~inter.VbusValid:
            VbusSate = 0b10
        elif inter.VbusValid:
            VbusSate = 0b11
        RxActive = self.RxEvent_RxActive
        RxError = self.RxEvent_RxError
        HostDisconnected = self.HostDisconnected
        if ~RxActive and ~RxError and ~HostDisconnected:
            RxEvent = 0b00
        elif RxActive and ~RxError and ~HostDisconnected:
            RxEvent = 0b01
        elif RxActive and RxError and ~HostDisconnected:
            RxEvent = 0b11
        elif HostDisconnected:
            RxEvent = 0b10
        IdGnd = 0
        alt_int = 0
        return (alt_int << 7) | (IdGnd << 6) | (RxEvent << 4) | (VbusSate << 2) | LineState

    def parse_RX_CMD(self, ulpi_data: int):
        ulpi_data = uint8_t.from_py(ulpi_data)
        LineState = int(ulpi_data[2:0])
        if LineState != USB_LINE_STATE.J:
            raise NotImplementedError()

        _inter = int(ulpi_data[4:2])
        inter = self.reg_interrupt
        if _inter == 0b00:
            inter.SessEnd = 1
            inter.SessValid = 0
            inter.VbusValid = 0
        elif _inter == 0b01:
            inter.SessEnd = 0
            inter.SessValid = 0
            inter.VbusValid = 0
        elif _inter == 0b10:
            inter.SessValid = 1
            inter.VbusValid = 0
        elif _inter == 0b11:
            inter.VbusValid = 1

        ae = int(ulpi_data[6:4])
        if ae == 0b00:
            rxactive = 0
            rxerror = 0
        elif ae == 0b01:
            rxactive = 1
            rxerror = 0
        elif ae == 0b10:
            self.HostDisconnect = 1
        elif ae == 0b11:
            rxactive = 1
            rxerror = 1
        self.RxEvent_RxActive = rxactive
        self.RxEvent_RxError = rxerror

        IdGnd = int(ulpi_data[6])
        if IdGnd != 0:
            raise NotImplementedError(IdGnd)
        alt_int = int(ulpi_data[7])
        if alt_int != 0:
            raise NotImplementedError(alt_int)

    def data_read(self):
        return self.intf.data.o._sigInside.read()

    def driver(self):
        """
        Drive ULPI interface as a PHY (and host) does

        Inputs:

            * data.t (should be 0 in rx and turnaround else mask(8))
            * data.o (only in tx, 1st byt is cmd, rest is data)
            * stp (1 for 1 clk after last word in tx)

        Outputs:

            * data.i (None in tx, else depending on nxt)
            * dir
            * nxt (0 if tx should stall or rx is stalled and sending rxd cmd instead)

        """
        yield WaitWriteOnly()
        intf = self.intf
        intf.dir._sigInside.write(self.dir)

        yield WaitCombRead()
        en = self.notReset() and self._enabled
        if not en:
            return

        if self.in_turnarround:
            # entirely skip the turnaround cycle
            yield WaitWriteOnly()
            # print("%d: %r PHY: turnaround ->%s" % (self.sim.now, intf, "PHY" if self.dir == Ulpi.DIR.PHY else "LINK"))
            self.in_turnarround = False
            intf.data.i._sigInside.write(None)
            if self.dir == Ulpi.DIR.PHY:
                # nxt=1 in turnarround means thatat the next RX_CMD contains RxActive
                intf.nxt._sigInside.write(int(bool(self.phy_to_link_packets)))

            yield WaitCombRead()
            t = int(intf.data.t._sigInside.read())
            assert t == 0, (self.sim.now, intf, t, "data signal has to be in high-impedance state during turnaround")
            return

        if self.dir == Ulpi.DIR.PHY:
            # RX from PHY
            yield WaitWriteOnly()

            # some data in packet, if NOP sending RX_CMD
            to_link_pkt = self.actual_phy_to_link_packet
            if not to_link_pkt and self.phy_to_link_packets:
                to_link_pkt = self.actual_phy_to_link_packet = self.phy_to_link_packets.popleft()
                assert to_link_pkt, ("ULPI pakcet has to have at least PID")

            if to_link_pkt is None:
                d = self.build_RX_CMD()
            else:
                d = to_link_pkt.popleft()
            self.RxEvent_RxActive = int(bool(to_link_pkt))

            intf.data.i._sigInside.write(d)
            intf.nxt._sigInside.write(int(
                self._enabled and
                to_link_pkt is not None
            ))

            yield WaitCombRead()
            t = int(intf.data.t._sigInside.read())
            assert t == 0, (self.sim.now, intf, t, "link must not write data when PHY is the master of this bus")
            stp = int(intf.stp._sigInside.read())
            if stp != 0:
                raise NotImplementedError()

            if not to_link_pkt:
                # has no data, now is the time to swith to tx
                self.dir = Ulpi.DIR.LINK
                self.in_turnarround = True
                self.actual_phy_to_link_packet = None

        else:
            # TX to PHY
            yield WaitWriteOnly()
            intf.nxt._sigInside.write(int(self._enabled))

            yield WaitCombRead()
            try:
                t = int(intf.data.t._sigInside.read())
            except ValidityError:
                raise AssertionError(self.sim.now, intf.data.t._getFullName(),
                                     "in invalid state (this would result in burned IO)")

            assert t == mask(8), (self.sim.now, intf, t,
                                  "link must write the data when it is the master of this bus")

            try:
                stp = int(intf.stp._sigInside.read())
            except ValueError:
                raise AssertionError(
                    (self.sim.now, intf._getFullName(), "stp signal in invalid state"
                     "(this would cause desynchronization)"))
            try:
                d = int(self.data_read())
            except ValidityError:
                raise AssertionError(self.sim.now, intf.data.t._getFullName(), "invalid data from LINK")

            p = self.actual_link_to_phy_packet
            if stp or (p is None and d == ULPI_TX_CMD.NOOP):
                assert d == ULPI_TX_CMD.NOOP, d
                # end of packet or link has no data to send, the current data is not valid (this is an idle word after last word in packet)
                if p is not None:
                    assert p
                    self.on_link_to_phy_packet(p)
                    self.actual_link_to_phy_packet = None
                self.dir = Ulpi.DIR.PHY
                self.in_turnarround = True
            else:
                if p is None:
                    # first word of packet is txd cmd
                    if d == ULPI_TX_CMD.NOOP:
                        pass
                    elif ULPI_TX_CMD.is_USB_PID(d):
                        p = self.actual_link_to_phy_packet = deque()
                        p.append(d)
                    else:
                        raise NotImplementedError(d)
                        # self.actual_link_to_phy_packet = deque()
                else:
                    p.append(d)

    def monitor(self):
        """
        Emulate behavior of the link (and device)

        Inputs:

            * data.i
            * dir
            * nxt

        Outputs:

            * data.t
            * data.o
            * stp

        """
        intf = self.intf
        yield WaitCombRead()
        en = self.notReset() and self._enabled
        if not en:
            return

        yield WaitWriteOnly()
        yield WaitCombRead()
        direction = int(intf.dir._sigInside.read())
        if direction != self.dir:
            self.in_turnarround = True
            self.dir = direction

        yield WaitWriteOnly()
        if self.in_turnarround:
            # print("%d: %r LINK: turnaround ->%s" % (self.sim.now, intf, "PHY" if self.dir == Ulpi.DIR.PHY else "LINK"))
            # check if it was in the middle of recieving of the packet (end of rx packet)
            if direction == Ulpi.DIR.LINK:  # the direction is now reversed than it was
                p = self.actual_phy_to_link_packet
                if p is not None:
                    assert p, (self.sim.now, intf, "The packet needs to have at least PID and other members of header")
                    self.on_phy_to_link_packet(p)
                    self.actual_phy_to_link_packet = None
            # entirely skip the turnaround cycle
            intf.data.o._sigInside.write(None)
            intf.data.t._sigInside.write(0)
            self.in_turnarround = False
            return

        else:
            if direction == Ulpi.DIR.LINK:
                stp = int(not self.actual_link_to_phy_packet and self.actual_link_to_phy_packet is not None)
                m = mask(8)
                if self.actual_link_to_phy_packet:
                    d = self.actual_link_to_phy_packet[0]  # ULPI_TX_CMD.USB_PID(tx_pid)
                else:
                    d = ULPI_TX_CMD.NOOP
            else:
                stp = 0
                m = 0
                d = None

            intf.stp._sigInside.write(stp)
            intf.data.t._sigInside.write(m)
            intf.data.o._sigInside.write(d)

        yield WaitCombRead()
        nxt = int(intf.nxt._sigInside.read())
        if direction == Ulpi.DIR.LINK:
            # tx/write
            if nxt:
                if self.actual_link_to_phy_packet:
                    self.actual_link_to_phy_packet.popleft()
                elif self.link_to_phy_packets:
                    self.actual_link_to_phy_packet = self.link_to_phy_packets.popleft()
                else:
                    self.actual_link_to_phy_packet = None
        else:
            assert direction == Ulpi.DIR.PHY
            # rx/read
            try:
                data = int(intf.data.i._sigInside.read())
            except ValueError:
                raise AssertionError(
                    ("%r: data signal for interface %r is in invalid state") %
                    (self.sim.now, intf))
            if nxt:
                # rx data
                p = self.actual_phy_to_link_packet
                if p is None:
                    p = self.actual_phy_to_link_packet = deque()
                p.append(data)
            else:
                # rx_cmd
                self.parse_RX_CMD(data)
