from hwt.code import If, Switch, Concat
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import INT, SLICE, STR, BIT, FLOAT64
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Signal
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwt.code_utils import rename_signal

class usb_fs_in_pe(Unit):
    """ The IN Protocol Engine sends data to the host.

    """
    def _config(self):
        self.NUM_IN_EPS = Param(11)
        self.MAX_IN_PACKET_SIZE = Param(32)

    def _declr(self):
        NUM_IN_EPS, MAX_IN_PACKET_SIZE = \
        self.NUM_IN_EPS, self.MAX_IN_PACKET_SIZE
        # ports
        self.clk = Signal()
        self.reset = Signal()
        self.reset_ep = Signal(Bits(NUM_IN_EPS + 1))
        self.dev_addr = Signal(Bits(8))
        #//////////////////
        # endpoint interface
        #//////////////////
        self.in_ep_data_free = Signal(Bits(NUM_IN_EPS + 1))._m()
        self.in_ep_data_put = Signal(Bits(NUM_IN_EPS + 1))
        self.in_ep_data = Signal(Bits(9))
        self.in_ep_data_done = Signal(Bits(NUM_IN_EPS + 1))
        self.in_ep_stall = Signal(Bits(NUM_IN_EPS + 1))
        self.in_ep_acked = Signal(Bits(NUM_IN_EPS + 1))._m()
        #//////////////////
        # rx path
        #//////////////////
        # Strobed on reception of packet.
        self.rx_pkt_start = Signal()
        self.rx_pkt_end = Signal()
        self.rx_pkt_valid = Signal()
        # Most recent packet received.
        self.rx_pid = Signal(Bits(5))
        self.rx_addr = Signal(Bits(8))
        self.rx_endp = Signal(Bits(5))
        self.rx_frame_num = Signal(Bits(12))
        #//////////////////
        # tx path
        #//////////////////
        # Strobe to send new packet.
        self.tx_pkt_start = Signal()._m()
        self.tx_pkt_end = Signal()
        # Packet type to send
        self.tx_pid = Signal(Bits(5))._m()
        # Data payload to send if any
        self.tx_data_avail = Signal()._m()
        self.tx_data_get = Signal()
        self.tx_data = Signal(Bits(9))._m()
        # component instances

    def _impl(self):
        NUM_IN_EPS, MAX_IN_PACKET_SIZE, clk, reset, reset_ep, dev_addr, in_ep_data_free, in_ep_data_put, in_ep_data, in_ep_data_done, in_ep_stall, \
        in_ep_acked, rx_pkt_start, rx_pkt_end, rx_pkt_valid, rx_pid, rx_addr, rx_endp, rx_frame_num, tx_pkt_start, tx_pkt_end, \
        tx_pid, tx_data_avail, tx_data_get, tx_data = \
        self.NUM_IN_EPS, self.MAX_IN_PACKET_SIZE, self.clk, self.reset, self.reset_ep, self.dev_addr, self.in_ep_data_free, self.in_ep_data_put, self.in_ep_data, self.in_ep_data_done, self.in_ep_stall, \
        self.in_ep_acked, self.rx_pkt_start, self.rx_pkt_end, self.rx_pkt_valid, self.rx_pid, self.rx_addr, self.rx_endp, self.rx_frame_num, self.tx_pkt_start, self.tx_pkt_end, \
        self.tx_pid, self.tx_data_avail, self.tx_data_get, self.tx_data
        # internal signals
        #//////////////////////////////////////////////////////////////////////////////
        # endpoint state machine
        #//////////////////////////////////////////////////////////////////////////////
        ep_state = self._sig("ep_state", Bits(3)[NUM_IN_EPS])
        ep_state_next = self._sig("ep_state_next", Bits(3)[NUM_IN_EPS])
        # latched on valid IN token
        current_endp = self._sig("current_endp", Bits(5), def_val=0)
        current_ep_state = rename_signal(self, ep_state[current_endp][2:0], "current_ep_state")
        READY_FOR_PKT = 0
        PUTTING_PKT = 1
        GETTING_PKT = 2
        STALL = 3

        #//////////////////////////////////////////////////////////////////////////////
        # in transfer state machine
        #//////////////////////////////////////////////////////////////////////////////
        IDLE = 0
        RCVD_IN = 1
        SEND_DATA = 2
        WAIT_ACK = 3
        in_xfr_state = self._reg("in_xfr_state", Bits(3), def_val=IDLE)
        in_xfr_start = self._sig("in_xfr_start", def_val=0)
        in_xfr_end = self._sig("in_xfr_end", def_val=0)
        # data toggle state
        data_toggle = self._sig("data_toggle", Bits(NUM_IN_EPS + 1), def_val=0)
        # endpoint data buffer
        in_data_buffer = self._sig("in_data_buffer", Bits(9)[MAX_IN_PACKET_SIZE * NUM_IN_EPS])
        ep_put_addr = self._sig("ep_put_addr", Bits(7)[NUM_IN_EPS])
        ep_get_addr = self._sig("ep_get_addr", Bits(7)[NUM_IN_EPS])
        #integer i = 0;
        #initial begin
        # for (i = 0; i < NUM_IN_EPS; i = i + 1) begin
        #   ep_put_addr[i] <= 0;
        #   ep_get_addr[i] <= 0;
        #   ep_state[i] <= 0;
        # end
        #end
        in_ep_num = self._sig("in_ep_num", Bits(5))
        buffer_put_addr = rename_signal(self, in_ep_num[4:0]._concat(ep_put_addr[in_ep_num][5:0]), "buffer_put_addr")
        buffer_get_addr = rename_signal(self, current_endp[4:0]._concat(ep_get_addr[current_endp][5:0]), "buffer_get_addr")
        # endpoint data packet buffer has a data packet ready to send
        endp_ready_to_send = self._sig("endp_ready_to_send", Bits(NUM_IN_EPS + 1), def_val=0)
        # endpoint has some space free in its buffer
        endp_free = self._sig("endp_free", Bits(NUM_IN_EPS + 1), def_val=0)
        token_received = rename_signal(self, (((rx_pkt_end._isOn() & rx_pkt_valid._isOn())._isOn() & rx_pid[2:0]._eq(0b01)._isOn())._isOn() & rx_addr._eq(dev_addr)._isOn())._isOn() & (rx_endp < NUM_IN_EPS)._isOn(), "token_received")
        setup_token_received = rename_signal(self, token_received._isOn() & rx_pid[4:2]._eq(0b11)._isOn(), "setup_token_received")
        in_token_received = rename_signal(self, token_received._isOn() & rx_pid[4:2]._eq(0b10)._isOn(), "in_token_received")
        ack_received = rename_signal(self, (rx_pkt_end._isOn() & rx_pkt_valid._isOn())._isOn() & rx_pid._eq(0b0010)._isOn(), "ack_received")
        more_data_to_send = rename_signal(self, ep_get_addr[current_endp][6:0] < ep_put_addr[current_endp][6:0], "more_data_to_send")
        current_ep_get_addr = rename_signal(self, ep_get_addr[current_endp][6:0], "current_ep_get_addr")
        current_ep_put_addr = rename_signal(self, ep_put_addr[current_endp][6:0], "current_ep_put_addr")
        tx_data_avail_i = rename_signal(self, in_xfr_state._eq(SEND_DATA)._isOn() & more_data_to_send._isOn(), "tx_data_avail_i")
        ep_num_decoder = self._sig("ep_num_decoder", INT)
        #//////////////////////////////////////////////////////////////////////////////
        # in transfer state machine
        #//////////////////////////////////////////////////////////////////////////////
        rollback_in_xfr = self._sig("rollback_in_xfr")

        tx_data_avail(tx_data_avail_i)
        for ep_num  in range(NUM_IN_EPS):

            in_ep_acked[ep_num](0),
            ep_state_next[ep_num](ep_state[ep_num]),
            If(in_ep_stall[ep_num],
                ep_state_next[ep_num](STALL)
            ).Else(
                Switch(ep_state[ep_num])\
                    .Case(READY_FOR_PKT,
                        ep_state_next[ep_num](PUTTING_PKT))\
                    .Case(PUTTING_PKT,
                        If(in_ep_data_done[ep_num]._isOn() | ep_put_addr[ep_num][5]._isOn(),
                            ep_state_next[ep_num](GETTING_PKT)
                        ).Else(
                            ep_state_next[ep_num](PUTTING_PKT)
                        ))\
                    .Case(GETTING_PKT,
                        If(in_xfr_end._isOn() & current_endp._eq(ep_num)._isOn(),
                            ep_state_next[ep_num](READY_FOR_PKT),
                            in_ep_acked[ep_num](1)
                        ).Else(
                            ep_state_next[ep_num](GETTING_PKT)
                        ))\
                    .Case(STALL,
                        If(setup_token_received._isOn() & rx_endp._eq(ep_num)._isOn(),
                            ep_state_next[ep_num](READY_FOR_PKT)
                        ).Else(
                            ep_state_next[ep_num](STALL)
                        ))\
                    .Default(
                        ep_state_next[ep_num](READY_FOR_PKT))
            ),
            endp_free[ep_num](~ep_put_addr[ep_num][5]._isOn()),
            in_ep_data_free[ep_num](endp_free[ep_num]._isOn() & ep_state[ep_num]._eq(PUTTING_PKT)._isOn()),

            If(clk._onRisingEdge(),
                If(reset._isOn() | reset_ep[ep_num]._isOn(),
                    ep_state[ep_num](READY_FOR_PKT)
                ).Else(
                    ep_state[ep_num](ep_state_next[ep_num]),
                    Switch(ep_state[ep_num])\
                        .Case(READY_FOR_PKT,
                            ep_put_addr[ep_num][6:0](0))\
                        .Case(PUTTING_PKT,
                            If(in_ep_data_put[ep_num],
                                ep_put_addr[ep_num][6:0](ep_put_addr[ep_num][6:0] + 1)
                            ))\
                        .Case(GETTING_PKT,
                        )\
                        .Case(STALL,
                        )
                )
            )

        in_ep_num(0),
        ep_num_decoder(0)
        for ep_num_decoder in range(NUM_IN_EPS):
            If(in_ep_data_put[ep_num_decoder],
                in_ep_num(ep_num_decoder)
            )

        If(clk._onRisingEdge(),
            Switch(ep_state[in_ep_num])\
                .Case(PUTTING_PKT,
                    If(in_ep_data_put[in_ep_num]._isOn() & (~ep_put_addr[in_ep_num][5]._isOn())._isOn(),
                        in_data_buffer[buffer_put_addr](in_ep_data)
                    ))
        )

        in_xfr_start(0),
        in_xfr_end(0),
        tx_pkt_start(0),
        tx_pid(0b0000),
        rollback_in_xfr(0),
        Switch(in_xfr_state)\
            .Case(IDLE,
                rollback_in_xfr(1),
                If(in_token_received,
                    in_xfr_state(RCVD_IN)
                ).Else(
                    in_xfr_state(IDLE)
                ))\
            .Case(RCVD_IN,
                tx_pkt_start(1),
                If(ep_state[current_endp]._eq(STALL),
                    in_xfr_state(IDLE),
                    tx_pid(0b1110)
                ).Elif(ep_state[current_endp]._eq(GETTING_PKT),
                    in_xfr_state(SEND_DATA),
                    tx_pid(data_toggle[current_endp]._concat(0b011)),
                    in_xfr_start(1)
                ).Else(
                    in_xfr_state(IDLE),
                    tx_pid(0b1010)
                ))\
            .Case(SEND_DATA,
                If(~more_data_to_send._isOn(),
                    in_xfr_state(WAIT_ACK)
                ).Else(
                    in_xfr_state(SEND_DATA)
                ))\
            .Case(WAIT_ACK,
                # FIXME: need to handle smash/timeout
                If(ack_received,
                    in_xfr_state(IDLE),
                    in_xfr_end(1)
                ).Elif(in_token_received,
                    in_xfr_state(RCVD_IN),
                    rollback_in_xfr(1)
                ).Elif(rx_pkt_end,
                    in_xfr_state(IDLE),
                    rollback_in_xfr(1)
                ).Else(
                    in_xfr_state(WAIT_ACK)
                ))

        If(clk._onRisingEdge(),
            tx_data(in_data_buffer[buffer_get_addr])
        )

        If(clk._onRisingEdge(),
            If(reset,
                in_xfr_state(IDLE)
            ).Else(
                in_xfr_state(in_xfr_state_next),
                If(setup_token_received,
                    data_toggle[rx_endp](1)
                ),
                If(in_token_received,
                    current_endp(rx_endp)
                ),
                If(rollback_in_xfr,
                    ep_get_addr[current_endp][6:0](0)
                ),
                Switch(in_xfr_state)\
                    .Case(IDLE,
                    )\
                    .Case(RCVD_IN,
                    )\
                    .Case(SEND_DATA,
                        If(tx_data_get._isOn() & tx_data_avail_i._isOn(),
                            ep_get_addr[current_endp][6:0](ep_get_addr[current_endp][6:0] + 1)
                        ))\
                    .Case(WAIT_ACK,
                        If(ack_received,
                            data_toggle[current_endp](~data_toggle[current_endp]._isOn())
                        ))
            ),
            j(0)
            while j < NUM_IN_EPS:
                If(reset._isOn() | reset_ep[j]._isOn(),
                    data_toggle[j](0),
                    ep_get_addr[j][6:0](0)
                )
        )
