from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import VectSignal, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from pyMathBitPrecise.bit_utils import mask


class UnalignedJoinRegIntf(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        AxiStream._config(self)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.keep = VectSignal(self.DATA_WIDTH // 8)
        if self.USE_STRB:
            self.strb = VectSignal(self.DATA_WIDTH // 8)
        self.relict = Signal()
        self.last = Signal()


@serializeParamsUniq
class FrameJoinInputReg(Unit):
    """
    Pipeline of registers for AxiStream with keep mask and flushing

    .. hwt-autodoc::
    """

    def _config(self):
        self.REG_CNT = Param(2)
        AxiStream._config(self)
        self.USE_KEEP = True

    def _declr(self):
        assert self.USE_KEEP
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

        # used to shift whole register pipeline using input keep_mask
        self.ready = Signal()
        if self.ID_WIDTH or self.USER_WIDTH or self.DEST_WIDTH:
            raise NotImplementedError("It is not clear how id/user/dest"
                                      " should be managed between the frames")

    def _impl(self):
        mask_t = Bits(self.DATA_WIDTH // 8, force_vector=True)
        data_fieds = [
            (Bits(self.DATA_WIDTH), "data"),
            (mask_t, "keep"),  # valid= keep != 0
            (BIT, "relict"),  # flag for partially consumed word
            (BIT, "last"),  # flag for end of frame
        ]
        if self.USE_STRB:
            data_fieds.append((mask_t, "strb"),
)
        data_t = HStruct(*data_fieds)
        # regs[0] connected to output as first, regs[-1] connected to input
        regs = [
            self._reg(f"r{r_i:d}", data_t, def_val={"keep": 0,
                                                    "last": 0,
                                                    "relict": 0})
            for r_i in range(self.REG_CNT)
        ]
        ready = self.ready
        keep_masks = self.keep_masks
        fully_consumed_flags = []
        for i, r in enumerate(regs):
            _fully_consumed = (r.keep & keep_masks[i])._eq(0)
            if i == 0:
                _fully_consumed = _fully_consumed & self.ready

            fully_consumed_flags.append(rename_signal(self, _fully_consumed, f"r{i:d}_fully_consumed"))

        for i, (is_first_on_input_r, r) in enumerate(iter_with_last(regs)):
            keep_mask_all = mask(r.keep._dtype.bit_length())
            prev_keep_mask = self._sig(f"prev_keep_mask_{i:d}_tmp", r.keep._dtype)
            prev_last_mask = self._sig(f"prev_last_mask_{i:d}_tmp")

            is_empty = rename_signal(self, r.keep._eq(0) & ~(r.last & r.relict), f"r{i:d}_is_empty")

            if is_first_on_input_r:
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
                    next_r = regs[i - 1]
                    next_empty = next_r.keep._eq(0) & ~(next_r.relict & next_r.last)
                else:
                    next_empty = 0

                whole_pipeline_shift = (ready & (regs[0].keep & self.keep_masks[0])._eq(0))
                r_prev.ready(is_empty  # last input reg empty
                             | whole_pipeline_shift
                             | next_empty)
            else:
                r_prev = regs[i + 1]
                prev_last_mask(1)
                If(is_empty,
                   # flush
                   prev_keep_mask(keep_mask_all),
                ).Else(
                   prev_keep_mask(keep_masks[i + 1]),
                )

            data_drive = [r.data(r_prev.data), ]
            if self.USE_STRB:
                data_drive.append(r.strb(r_prev.strb))

            fully_consumed = fully_consumed_flags[i]
            if i == 0:
                # last register in path
                If((ready & fully_consumed) | is_empty,
                    *data_drive,
                    r.keep(r_prev.keep & prev_keep_mask),
                    r.last(r_prev.last & prev_last_mask),
                    r.relict(
                        r_prev.valid & r_prev.keep._eq(0)
                        if is_first_on_input_r else
                        # [TODO] potentially it should not be keep[0] but fist keep with 1
                        r_prev.relict | (r_prev.last & (r_prev.keep[0] & ~keep_masks[i + 1][0] & ~fully_consumed_flags[i + 1]))
                    )
                ).Elif(ready,
                   r.keep(r.keep & keep_masks[i]),
                   r.relict(1),  # became relict if there is some 1 in keep (== not fully consumed)
                )
            else:
                next_fully_consumed = fully_consumed_flags[i - 1]
                next_r = regs[i - 1]
                next_is_empty = next_r.keep._eq(0) & ~(next_r.relict & next_r.last)
                if is_first_on_input_r:
                    is_relict = r_prev.valid & r_prev.keep._eq(0)
                else:
                    prev_fully_consumed = fully_consumed_flags[i + 1]
                    is_relict = r_prev.relict | ~prev_fully_consumed

                If((ready & next_fully_consumed) | is_empty | next_is_empty,
                   *data_drive,
                   r.keep(r_prev.keep & prev_keep_mask),
                   r.last(r_prev.last & prev_last_mask),
                   r.relict(is_relict)
                )

        for rout, rin in zip(self.regs, regs):
            rout.data(rin.data)
            if self.USE_STRB:
                rout.strb(rin.strb)
            rout.keep(rin.keep)
            rout.relict(rin.relict)
            rout.last(rin.last)

