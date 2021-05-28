#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, CodeBlock
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.unit import Unit


class BlockStm_complete_override0(Unit):

    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.c = Signal()._m()

    def _impl(self):
        # results in c = b
        CodeBlock(
            self.c(self.a),
            self.c(self.b),
        )


class BlockStm_complete_override1(BlockStm_complete_override0):

    def _impl(self):
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

    def _impl(self):
        # results in c = a
        CodeBlock(
            If(self.b,
               self.c(0),
            ),
            self.c(self.a),
        )

class BlockStm_nop_val_optimized_out(BlockStm_complete_override0):

    def _declr(self):
        addClkRstn(self)
        BlockStm_complete_override0._declr(self)

    def _impl(self):
        r = self._reg("r")
        CodeBlock(
            If(self.b,
               r(self.a),
            ),
            self.c(self.a),
        )

class BlockStm_nop_val(BlockStm_nop_val_optimized_out):

    def _declr(self):
        BlockStm_nop_val_optimized_out._declr(self)
        self.c1 = Signal()._m()

    def _impl(self):
        r = self._reg("r")
        CodeBlock(
            If(self.b,
               r(self.a),
            ),
            self.c(self.a),
        )
        self.c1(r)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # u = BlockStm_complete_override0()
    # print(to_rtl_str(u))
    u = BlockStm_nop_val()
    print(to_rtl_str(u))
    # u = BlockStm_complete_override2()
    # print(to_rtl_str(u))

