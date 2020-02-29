from math import inf
from typing import Optional, List, Callable, Tuple

from hwt.code import If, Switch, log2ceil, SwitchLogic, Or, And
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.streamAlignmentUtils import resolve_input_bytes_destinations,\
    streams_to_all_possible_frame_formats
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frame_join_utils import input_B_dst_to_fsm,\
    StateTransItem
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.interface import Interface
from hwt.serializer.mode import serializeParamsUniq
from pyMathBitPrecise.bit_utils import mask


def bit_list_to_int(bl):
    """
    in list LSB first, in result little endian ([1, 0] -> 0b01)
    """
    v = 0
    for i, b in enumerate(bl):
        v |= b << i
    return v


class UnalignedJoinRegIntf(Interface):

    def _config(self):
        AxiStream._config(self)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.keep = VectSignal(self.DATA_WIDTH // 8)
        self.last = Signal()


@serializeParamsUniq
class FrameJoinInputReg(Unit):
    """
    Pipeline of registers for AxiStream with keep mask and flushing
    """

    def _config(self):
        self.REG_CNT = Param(2)
        AxiStream._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.dataIn = AxiStream()
            self.regs = HObjList(
                UnalignedJoinRegIntf()._m()
                for _ in range(self.REG_CNT))
        self.keep_masks = HObjList(
            VectSignal(self.DATA_WIDTH // 8)
            for _ in range(self.REG_CNT)
        )
        self.ready = Signal()

    def _impl(self):
        data_t = HStruct(
            (Bits(self.DATA_WIDTH), "data"),
            (Bits(self.DATA_WIDTH//8, force_vector=True), "keep"),  # valid= keep != 0
            (BIT, "last"),
        )
        # regs[0] connected to output as first, regs[-1] connected to input
        regs = [
            self._reg("r%d" % (r_i), data_t, def_val={"keep": 0,
                                                      "last": 0})
            for r_i in range(self.REG_CNT)
        ]
        ready = self.ready
        keep_masks = self.keep_masks
        for i, (is_last_r, r) in enumerate(iter_with_last(regs)):
            keep_mask_all = mask(r.keep._dtype.bit_length())
            prev_keep_mask = self._sig("prev_keep_mask_%d_tmp" % i, r.keep._dtype)
            prev_last_mask = self._sig("prev_last_mask_%d_tmp" % i)

            if is_last_r:
                # is register connected directly to dataIn
                r_prev = self.dataIn
                If(r_prev.valid,
                   prev_keep_mask(keep_mask_all),
                   prev_last_mask(1)
                ).Else(
                   # flush (invalid input but the data can be dispersed
                   # in registers so we need to collapse it)
                   prev_keep_mask(0),
                   prev_last_mask(0),
                )
                if self.REG_CNT > 1:
                    next_empty = regs[i - 1].keep._eq(0)
                else:
                    next_empty = 0

                r_prev.ready(r.keep._eq(0) | ready | next_empty)
            else:
                r_prev = regs[i + 1]
                prev_last_mask(1)
                If(r.keep._eq(0),
                    # flush
                   prev_keep_mask(keep_mask_all),
                ).Else(
                   prev_keep_mask(keep_masks[i + 1]),
                )

            if i == 0:
                # last register in path
                fully_consumed = (r.keep & keep_masks[i])._eq(0)
                If((ready & fully_consumed) | r.keep._eq(0),
                   r.data(r_prev.data),
                   r.keep(r_prev.keep & prev_keep_mask),
                   r.last(r_prev.last & prev_last_mask),
                ).Elif(ready,
                   r.keep(r.keep & keep_masks[i]),
                )
            else:
                next_fully_consumed = self._sig("r%d_prev_fully_consumed" % i)
                next_fully_consumed((regs[i - 1].keep & keep_masks[i - 1])._eq(0))
                If((ready & next_fully_consumed) | r.keep._eq(0) | regs[i - 1].keep._eq(0),
                   r.data(r_prev.data),
                   r.keep(r_prev.keep & prev_keep_mask),
                   r.last(r_prev.last & prev_last_mask),
                )
        for rout, rin in zip(self.regs, regs):
            rout.data(rin.data)
            rout.keep(rin.keep)
            rout.last(rin.last)


class AxiS_FrameJoin(Unit):
    """
    Join frames from multiple input streams and use keep signal
    to remove invalid bytes from body of the final packet.
    Can be also used to translate alignment of data.

    :note: delay=0
    :note: This component generates differen frame joining logic
        for each specific case of data alignment which can happen based on configuration.
        This means that the implementation can be just straight wire or very complicated
        pipelined shift logic.

    :note: The schematic is ilustrative

    .. aafig::

        +---+---+      +---+---+        +---+---+
        | X | 1 |      | 3 | 4 |        | 1 | 2 |
        +---+---+   +  +---+---+  ->    +---+---+
        | 2 | X |      | X | X |        | 3 | 4 |
        +---+---+      +---+---+        +---+---+

    """

    def _config(self):
        self.T = Param(HStruct(
            (HStream(Bits(8), frame_len=(1, inf),
                     start_offsets=[0]), "f0"),
            (HStream(Bits(16), frame_len=(1, 1)), "f1"),
        ))
        AxiStream._config(self)
        self.DATA_WIDTH = 16
        self.USE_KEEP = True
        self.OUT_OFFSET = Param(0)

    def _declr(self):
        t = self.T
        word_bytes = self.word_bytes = self.DATA_WIDTH // 8
        input_cnt = self.input_cnt = len(t.fields)
        frames = streams_to_all_possible_frame_formats(
            t, word_bytes, self.OUT_OFFSET)
        input_B_dst = resolve_input_bytes_destinations(
            frames, len(t.fields), word_bytes)
        self.state_trans_table = input_B_dst_to_fsm(
            word_bytes, input_cnt, input_B_dst)

        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = AxiStream()._m()
            self.dataIn = HObjList(AxiStream() for _ in range(self.input_cnt))

    def generate_input_register(self, input_i, reg_cnt):
        in_reg = FrameJoinInputReg()
        in_reg._updateParamsFrom(self)
        in_reg.REG_CNT = reg_cnt
        setattr(self, "in_reg%d" % input_i, in_reg)
        in_reg.dataIn(self.dataIn[input_i])
        return in_reg.regs, in_reg.keep_masks, in_reg.ready

    def generate_output_byte_mux(self, regs):
        out_mux_values = [set() for _ in range(self.word_bytes)]
        for st in self.state_trans_table.state_trans:
            for stt in st:
                for o_mux_val, out_mux_val_set in zip(stt.out_byte_mux_sel,
                                                      out_mux_values):
                    if o_mux_val is not None:
                        out_mux_val_set.add(o_mux_val)
        out_mux_values = [sorted(x) for x in out_mux_values]

        def index_byte(sig, byte_i):
            return sig[(byte_i+1)*8:byte_i*8]

        def get_in_byte(input_i, time_offset, byte_i):
            return index_byte(regs[input_i][time_offset].data, byte_i)

        out_byte_sel = []
        for out_B_i, out_byte_mux_vals in enumerate(out_mux_values):
            sel_w = log2ceil(len(out_byte_mux_vals))
            sel = self._sig("out_byte%d_sel" % out_B_i, Bits(sel_w))
            out_byte_sel.append(sel)

            out_B = index_byte(self.dataOut.data, out_B_i)
            Switch(sel).addCases(
                (i, out_B(get_in_byte(*val)))
                for i, val in enumerate(out_byte_mux_vals))

        return out_byte_sel, out_mux_values

    @staticmethod
    def add_cond_bit(cond, bit, bit_val):
        if bit_val is None:
            return
        if bit_val == 0:
            bit = ~bit
        cond.append(bit)

    def state_trans_cond(self, sst: StateTransItem, input_regs):
        cond = []
        assert len(sst.input) == len(input_regs)
        for in_metas, in_regs in zip(sst.input, input_regs):
            assert len(in_metas) == len(in_regs)
            for in_meta, in_reg in zip(in_metas, in_regs):
                for k_i, k in enumerate(in_meta.keep):
                    self.add_cond_bit(cond, in_reg.keep[k_i], k)
                self.add_cond_bit(cond, in_reg.last, in_meta.last)

        return And(*cond)

    def get_conds_for_unique_values(self, st_ts: List[StateTransItem],
                                    input_regs,
                                    key: Callable[[StateTransItem], None]):
        # output value : List[RtlSignal]
        value_conds = {}
        for st_t in st_ts:
            k = key(st_t)
            cond_list = value_conds.setdefault(k, [])
            cond = self.state_trans_cond(st_t, input_regs)
            cond_list.append(cond)

        return [(Or(*v), k) for k, v in value_conds.items()]

    def _generate_driver_for_state_trans_dependent_out(
            self, st_transs: List[StateTransItem],
            input_regs,
            value_getter: Callable[[StateTransItem], object],
            connect_out_fn,
            make_defult_case: Optional[Callable[[], object]]):
        """
        specific variant of :func:`generate_driver_for_state_trans_dependent_out` for a single state
        """
        cases = []
        for cond, value in self.get_conds_for_unique_values(
                st_transs, input_regs,
                key=value_getter):
            cases.append((cond, connect_out_fn(value)))
        if make_defult_case is None:
            return SwitchLogic(cases)
        else:
            return SwitchLogic(cases, default=make_defult_case())

    def generate_driver_for_state_trans_dependent_out(
            self, st_reg: Optional[RtlSignal],
            state_trans: List[List[StateTransItem]],
            input_regs,
            value_getter: Callable[[StateTransItem], object],
            connect_out_fn,
            make_defult_case=None):
        """
        Construct driver for output signal which is driven from input registers
        and state transition logic
        """
        cases = []
        for st_i, st_transs in enumerate(state_trans):
            case = self._generate_driver_for_state_trans_dependent_out(
                st_transs, input_regs, value_getter, connect_out_fn,
                make_defult_case)
            if st_reg is None:
                # single state variant without any st_reg
                assert len(state_trans) == 1
                return case
            cases.append((st_i, case))

        mux = Switch(st_reg).addCases(cases)
        if make_defult_case is not None:
            mux.Default(make_defult_case())

        return mux

    def generate_fsm(self, input_regs, out_sel: List[RtlSignal],
                     out_mux_values: List[List[Tuple[int, int, int]]],
                     in_keep_masks: List[List[RtlSignal]],
                     ready: List[RtlSignal]):
        state_trans = self.state_trans_table.state_trans
        # next state logic (only i required)
        st_cnt = len(state_trans)
        assert st_cnt > 0
        if st_cnt > 1:
            state = self._reg("state", Bits(log2ceil(st_cnt)), def_val=0)
            # state next logic
            If(self.dataOut.ready,
                self.generate_driver_for_state_trans_dependent_out(
                     state, state_trans, input_regs,
                     lambda stt: stt.state_next,
                     lambda v: state(v))
            )
        else:
            state = None
        # out_sel driver
        for out_B_i, (_out_mux_values, _out_sel) in enumerate(zip(out_mux_values, out_sel)):
            def connect_out_sel(v):
                if v is not None:
                    v = _out_mux_values.index(v)
                return _out_sel(v)
            self.generate_driver_for_state_trans_dependent_out(
                state, state_trans, input_regs,
                lambda stt: stt.out_byte_mux_sel[out_B_i],
                connect_out_sel,
                lambda: _out_sel(None),
            )
        # out.keep driver
        self.generate_driver_for_state_trans_dependent_out(
            state, state_trans, input_regs,
            lambda stt: tuple(stt.output_keep),
            lambda v: self.dataOut.keep(bit_list_to_int(v)),
            lambda: self.dataOut.keep(None)
        )
        # out.last driver
        self.generate_driver_for_state_trans_dependent_out(
            state, state_trans, input_regs,
            lambda stt: stt.last,
            lambda v: self.dataOut.last(v),
            lambda: self.dataOut.last(None)
        )
        # out.valid
        self.generate_driver_for_state_trans_dependent_out(
            state, state_trans, input_regs,
            lambda stt: any(o is not None for o in stt.out_byte_mux_sel),
            lambda v: self.dataOut.valid(v),
            lambda: self.dataOut.valid(0),
        )
        # in.ready driver
        for in_i, _ready in enumerate(ready):
            self.generate_driver_for_state_trans_dependent_out(
                state, state_trans, input_regs,
                lambda stt: stt.input_rd[in_i],
                lambda v: _ready(self.dataOut.ready & v),
                lambda: _ready(0),
            )
        for in_i, in_keeps in enumerate(in_keep_masks):
            for in_t, in_keep in enumerate(in_keeps):
                self.generate_driver_for_state_trans_dependent_out(
                    state, state_trans, input_regs,
                    lambda stt: tuple(stt.input_keep_mask[in_i][in_t]),
                    lambda v: in_keep(bit_list_to_int(v)),
                    lambda: in_keep(0)
                )

    def _impl(self):
        regs = []
        keep_masks = []
        ready = []
        max_lookahead_for_input = self.state_trans_table.max_lookahead_for_input
        for input_i, stage_cnt in enumerate(max_lookahead_for_input):
            _regs, _keep_masks, _ready = self.generate_input_register(
                                                input_i, stage_cnt + 1)
            regs.append(_regs)
            keep_masks.append(_keep_masks)
            ready.append(_ready)
        out_sel, out_mux_values = self.generate_output_byte_mux(regs)
        self.generate_fsm(regs, out_sel, out_mux_values, keep_masks, ready)
        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiS_FrameJoin()
    D_B = 2
    u.DATA_WIDTH = 8 * D_B
    u.T = HStruct(
        (HStream(Bits(8*D_B), (1, inf), [1]), "frame0"),
        #(HStream(Bits(8*D_B), (1, inf), [0]), "frame1"),
    )
    print(toRtl(u))
