#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf
from typing import Optional, List, Callable, Tuple

from hwt.code import If, Switch, SwitchLogic, Or, And
from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.frame_utils.alignment_utils import FrameAlignmentUtils
from hwtLib.abstract.frame_utils.join.fsm import input_B_dst_to_fsm
from hwtLib.abstract.frame_utils.join.state_trans_item import StateTransItem
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frame_join.input_reg import FrameJoinInputReg, \
    UnalignedJoinRegIntf
from pyMathBitPrecise.bit_utils import bit_list_to_int


class AxiS_FrameJoin(Unit):
    """
    Join frames from multiple input streams and use keep signal
    to remove invalid bytes from body of the final packet.
    Can be also used to translate alignment of data.

    :note: delay=0
    :note: This component generates different frame joining logic
        for each specific case of data alignment, cunk size, frame lens, etc.
        which can happen based on configuration. This means that the implementation
        can be just straight wire or very complicated pipelined shift logic.

    :note: The figure is ilustrative

    .. aafig::

        +---+---+       +---+---+       +---+---+
        | X | 1 |       | 3 | 4 |       | 1 | 2 |
        +---+---+   +   +---+---+  ->   +---+---+
        | 2 | X |       | X | X |       | 3 | 4 |
        +---+---+       +---+---+       +---+---+

    .. hwt-autodoc::
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
        assert self.USE_KEEP
        t = self.T
        assert isinstance(t, HStruct)
        word_bytes = self.word_bytes = self.DATA_WIDTH // 8
        input_cnt = self.input_cnt = len(t.fields)
        streams = [f.dtype for f in t.fields]
        fju = FrameAlignmentUtils(word_bytes, self.OUT_OFFSET)
        input_B_dst = fju.resolve_input_bytes_destinations(
            streams)
        self.state_trans_table = input_B_dst_to_fsm(
            word_bytes, input_cnt, input_B_dst, fju.can_produce_zero_len_frame(streams))
        addClkRstn(self)
        with self._paramsShared():
            self.dataOut = AxiStream()._m()
            self.dataIn = HObjList(AxiStream() for _ in range(self.input_cnt))

    def generate_input_register(self, input_i: int, reg_cnt: int) -> Tuple[List[UnalignedJoinRegIntf], List[RtlSignal], RtlSignal]:
        in_reg = FrameJoinInputReg()
        in_reg._updateParamsFrom(self)
        in_reg.REG_CNT = reg_cnt
        setattr(self, f"in_reg{input_i:d}", in_reg)
        in_reg.dataIn(self.dataIn[input_i])
        return in_reg.regs, in_reg.keep_masks, in_reg.ready

    def generate_output_byte_mux(self, regs: List[List[UnalignedJoinRegIntf]]) -> Tuple[List[RtlSignal], List[List[RtlSignal]]]:
        out_mux_values = [set() for _ in range(self.word_bytes)]
        for st in self.state_trans_table.state_trans:
            for stt in st:
                for o_mux_val, out_mux_val_set in zip(stt.out_byte_mux_sel,
                                                      out_mux_values):
                    if o_mux_val is not None:
                        out_mux_val_set.add(o_mux_val)
        out_mux_values = [sorted(x) for x in out_mux_values]

        def index_byte(sig, byte_i: int) -> RtlSignal:
            return sig[(byte_i + 1) * 8:byte_i * 8]

        def get_in_byte(input_i: int, time_offset: int, byte_i: int) -> HdlAssignmentContainer:
            return index_byte(regs[input_i][time_offset].data, byte_i)

        def data_drive(out_B: RtlSignal, out_strb_b: RtlSignal,
                       input_i: int, time_offset: int, byte_i: int) -> List[HdlAssignmentContainer]:
            res = [
                out_B(get_in_byte(input_i, time_offset, byte_i))
            ]
            if self.USE_STRB:
                res.append(
                   out_strb_b(regs[input_i][time_offset].strb[byte_i])
                )
            return res

        out_byte_sel = []
        for out_B_i, out_byte_mux_vals in enumerate(out_mux_values):
            # +1 because last value is used to invalidate data
            sel_w = log2ceil(len(out_byte_mux_vals) + 1)
            sel = self._sig(f"out_byte{out_B_i:d}_sel", Bits(sel_w))
            out_byte_sel.append(sel)

            out_B = self._sig(f"out_byte{out_B_i:d}", Bits(8))
            index_byte(self.dataOut.data, out_B_i)(out_B)

            if self.USE_STRB:
                out_strb_b = self._sig(f"out_strb{out_B_i:d}")
                self.dataOut.strb[out_B_i](out_strb_b)
            else:
                out_strb_b = None

            sw = Switch(sel).add_cases(
                (i, data_drive(out_B, out_strb_b, *val))
                for i, val in enumerate(out_byte_mux_vals))
            # :note: default case is threre for the case of faulire where
            #     sel has non predicted value
            default_case = [out_B(None)]
            if self.USE_STRB:
                default_case.append(out_strb_b(0))
            sw.Default(*default_case)
        return out_byte_sel, out_mux_values

    @staticmethod
    def add_cond_bit(cond, bit: RtlSignal, bit_val: Optional[int]):
        if bit_val is None:
            return
        if bit_val == 0:
            bit = ~bit

        cond.append(bit)

    def state_trans_cond(self, sst: StateTransItem,
                         input_regs: List[List[UnalignedJoinRegIntf]]) -> RtlSignal:
        cond = []
        assert len(sst.input) == len(input_regs)
        for in_metas, in_regs in zip(sst.input, input_regs):
            assert len(in_metas) == len(in_regs)
            for in_meta, in_reg in zip(in_metas, in_regs):
                in_reg: UnalignedJoinRegIntf
                for k_i, k in enumerate(in_meta.keep):
                    self.add_cond_bit(cond, in_reg.keep[k_i], k)
                self.add_cond_bit(cond, in_reg.relict, in_meta.relict)
                self.add_cond_bit(cond, in_reg.last, in_meta.last)

        return And(*cond)

    def get_conds_for_unique_values(self, st_ts: List[StateTransItem],
                                    input_regs: List[List[UnalignedJoinRegIntf]],
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
            input_regs: List[List[UnalignedJoinRegIntf]],
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
            input_regs: List[List[UnalignedJoinRegIntf]],
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

        mux = Switch(st_reg).add_cases(cases)
        if make_defult_case is not None:
            mux.Default(make_defult_case())

        return mux

    def generate_fsm(self, input_regs: List[List[UnalignedJoinRegIntf]],
                     out_sel: List[RtlSignal],
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

            def connect_out_sel(v: Optional[Tuple[int, int, int]]) -> HdlAssignmentContainer:
                if v is None:
                    v = len(_out_mux_values)
                else:
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
            # valid if any output or output is 0B frame
            lambda stt: any(o is not None for o in stt.out_byte_mux_sel) or all(stt.input_rd),
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
        # lookahead specifies how many words from inputs has to be loaded
        # in order to resolve output word, it corresponds to a number of input registers-1
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
    from hwt.synthesizer.utils import to_rtl_str
    u = AxiS_FrameJoin()
    D_B = 2
    u.DATA_WIDTH = 8 * D_B
    #u.USE_STRB = True
    u.T = HStruct(
        (HStream(Bits(8 * 1), (1, inf), [0, 1, 2, 3]), "frame0"),
        (HStream(Bits(8 * 4), (1, 1), [0]), "frame1"),
    )
    u.T = HStruct(
        (HStream(Bits(8 * 1), (0, inf), [0]), "frame0"),
        (HStream(Bits(8 * 1), (0, inf), [0]), "frame1"),
        (HStream(Bits(8 * 1), (0, inf), [0]), "frame2"),
    )
    print(to_rtl_str(u))
