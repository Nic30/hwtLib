#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, CodeBlock
from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override


class BlockStm_complete_override0(HwModule):

    @override
    def hwDeclr(self):
        self.a = HwIOSignal()
        self.b = HwIOSignal()
        self.c = HwIOSignal()._m()

    @override
    def hwImpl(self):
        # results in c = b
        CodeBlock(
            self.c(self.a),
            self.c(self.b),
        )


class BlockStm_complete_override1(BlockStm_complete_override0):

    @override
    def hwImpl(self):
        # results in
        # c = a
        # if b:
        #    c = 0
        CodeBlock(
            self.c(self.a),
            If(self.b,
               self.c(0),
            )
        )


class BlockStm_complete_override2(BlockStm_complete_override0):

    @override
    def hwImpl(self):
        # results in c = a
        CodeBlock(
            If(self.b,
               self.c(0),
            ),
            self.c(self.a),
        )

class BlockStm_nop_val_optimized_out(BlockStm_complete_override0):

    @override
    def hwDeclr(self):
        addClkRstn(self)
        BlockStm_complete_override0.hwDeclr(self)

    @override
    def hwImpl(self):
        r = self._reg("r")
        CodeBlock(
            If(self.b,
               r(self.a),
            ),
            self.c(self.a),
        )

class BlockStm_nop_val(BlockStm_nop_val_optimized_out):

    @override
    def hwDeclr(self):
        BlockStm_nop_val_optimized_out.hwDeclr(self)
        self.c1 = HwIOSignal()._m()

    @override
    def hwImpl(self):
        r = self._reg("r")
        CodeBlock(
            If(self.b,
               r(self.a),
            ),
            self.c(self.a),
        )
        self.c1(r)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    # m = BlockStm_complete_override0()
    # print(to_rtl_str(m))
    m = BlockStm_nop_val()
    print(to_rtl_str(m))
    # m = BlockStm_complete_override2()
    # print(to_rtl_str(m))

