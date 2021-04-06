#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

from hwt.code import If, Switch
from hwt.hdl.statements.ifContainter import IfContainer
from hwt.hdl.statements.switchContainer import SwitchContainer
from hwt.hdl.types.defs import INT
from hwt.hdl.types.enum import HEnum
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist
from hwtLib.examples.base_serialization_TC import BaseSerializationTC


class StatementTreesTC(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.n = RtlNetlist()

    def compareStructure(self, template, cont):
        self.assertIsInstance(cont, template.__class__)
        if isinstance(template, IfContainer):
            self.assertEqual(template.cond, cont.cond)

            self.assertEqual(len(template.ifTrue), len(template.ifTrue))
            self.assertEqual(len(template.elIfs), len(template.elIfs))
            self.assertEqual(len(template.ifFalse), len(template.ifFalse))
        elif isinstance(template, SwitchContainer):
            self.assertEqual(template.switchOn, template.switchOn)
            self.assertEqual(len(template.cases), len(template.cases))

    def test_baicIf(self):
        a = self.n.sig('a')
        b = self.n.sig('b')

        obj = If(a,
            b(1)
        ).Else(
            b(0)
        )

        container, io_change = obj._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(container), 1)
        container = container[0]
        tmpl = IfContainer(a,
                           ifTrue=[b(1)],
                           ifFalse=[b(0)])
        self.compareStructure(tmpl, container)

    def test_basicSwitch(self):
        a = self.n.sig('a', dtype=INT)
        b = self.n.sig('b', dtype=INT)

        obj = Switch(a).add_cases([(i, b(i)) for i in range(4)])
        cont, io_change = obj._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(cont), 1)
        cont = cont[0]

        tmpl = SwitchContainer(a, [(i, b(i)) for i in range(3)]
                               + [(None, b(3))])
        self.compareStructure(tmpl, cont)

    def test_ifsInSwitch(self):
        n = self.n
        stT = HEnum('t_state', ["idle", "tsWait", "ts0Wait",
                                "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, def_val=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic():
            return If(sd0 & sd1,
                      st(stT.lenExtr)
            ).Else(
                st(stT.ts1Wait)
            )
        obj = Switch(st)\
            .Case(stT.idle,
                  tsWaitLogic())\
            .Case(stT.tsWait,
                  tsWaitLogic())\
            .Case(stT.ts0Wait,
                  If(sd0,
                     st(stT.lenExtr)
                  ).Else(
                      st(st)
                  ))\
            .Case(stT.ts1Wait,
                  If(sd1,
                        st(stT.lenExtr)
                  ).Else(
                        st(st)
                  ))\
            .Case(stT.lenExtr,
                  If(cntrlFifoVld & cntrlFifoLast,
                     st(stT.idle)
                  ).Else(
                      st(st)
                  )
            )

        cont, io_change = obj._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        Switch(st)\\
        .Case(t_state.idle,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(t_state.ts1Wait)
            ))\\
        .Case(t_state.tsWait,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(t_state.ts1Wait)
            ))\\
        .Case(t_state.ts0Wait,
            If(sd0._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.ts1Wait,
            If(sd1._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Default(
            If((ctrlFifoVld & ctrlFifoLast)._eq(1),
                st_next(t_state.idle)
            ).Else(
                st_next(st)
            ))
        """
        BaseSerializationTC.strStructureCmp(self, cont, tmpl)

    def test_ifs2LvlInSwitch(self):
        n = self.n
        stT = HEnum('t_state', ["idle", "tsWait",
                                "ts0Wait", "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, def_val=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic(ifNoTsRd):
            return If(sd0 & sd1,
                      st(stT.lenExtr)
                      ).Else(
                ifNoTsRd
            )
        obj = Switch(st)\
            .Case(stT.idle,
                  tsWaitLogic(
                      If(cntrlFifoVld,
                         st(stT.tsWait)
                         ).Else(
                          st(st)
                      )
                  ))\
            .Case(stT.tsWait,
                  tsWaitLogic(st(st)))\
            .Case(stT.ts0Wait,
                  If(sd0,
                     st(stT.lenExtr)
                  ).Else(
                      st(st)
                  ))\
            .Case(stT.ts1Wait,
                  If(sd1,
                     st(stT.lenExtr)
                  ).Else(
                      st(st)
                  ))\
            .Case(stT.lenExtr,
                  If(cntrlFifoVld & cntrlFifoLast,
                     st(stT.idle)
                  ).Else(
                      st(st)
                  )
            )

        cont, io_change = obj._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        Switch(st)\\
        .Case(t_state.idle,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Elif(ctrlFifoVld._eq(1),
                st_next(t_state.tsWait)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.tsWait,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.ts0Wait,
            If(sd0._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.ts1Wait,
            If(sd1._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Default(
            If((ctrlFifoVld & ctrlFifoLast)._eq(1),
                st_next(t_state.idle)
            ).Else(
                st_next(st)
            ))
        """
        BaseSerializationTC.strStructureCmp(self, cont, tmpl)

    def test_ifs3LvlInSwitch(self):
        n = self.n
        stT = HEnum('t_state', ["idle", "tsWait",
                                "ts0Wait", "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, def_val=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic(ifNoTsRd):
            return If(sd0 & sd1,
                st(stT.lenExtr)
            ).Elif(sd0,
               st(stT.ts1Wait)
            ).Else(
               ifNoTsRd
            )
        obj = Switch(st)\
            .Case(stT.idle,
                  tsWaitLogic(
                      If(cntrlFifoVld,
                         st(stT.tsWait)
                      ).Else(
                          st(st)
                      )
                  ))\
            .Case(stT.tsWait,
                  tsWaitLogic(st(st)))\
            .Case(stT.ts0Wait,
                  If(sd0,
                     st(stT.lenExtr)
                  ).Else(
                      st(st)
                  ))\
            .Case(stT.ts1Wait,
                  If(sd1,
                     st(stT.lenExtr)
                  ).Else(
                     st(st)
                  ))\
            .Case(stT.lenExtr,
                  If(cntrlFifoVld & cntrlFifoLast,
                     st(stT.idle)
                  ).Else(
                     st(st)
                  )
                                              )

        cont, io_change = obj._try_reduce()
        self.assertFalse(io_change)
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        Switch(st)\\
        .Case(t_state.idle,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Elif(sd0._eq(1),
                st_next(t_state.ts1Wait)
            ).Elif(ctrlFifoVld._eq(1),
                st_next(t_state.tsWait)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.tsWait,
            If((sd0 & sd1)._eq(1),
                st_next(t_state.lenExtr)
            ).Elif(sd0._eq(1),
                st_next(t_state.ts1Wait)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.ts0Wait,
            If(sd0._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Case(t_state.ts1Wait,
            If(sd1._eq(1),
                st_next(t_state.lenExtr)
            ).Else(
                st_next(st)
            ))\\
        .Default(
            If((ctrlFifoVld & ctrlFifoLast)._eq(1),
                st_next(t_state.idle)
            ).Else(
                st_next(st)
            ))
        """
        BaseSerializationTC.strStructureCmp(self, cont, tmpl)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(StatementTreesTC('test_ifs3LvlInSwitch'))
    suite.addTest(unittest.makeSuite(StatementTreesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
