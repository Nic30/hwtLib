#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import unittest

from hwt.hdlObjects.statements import IfContainer, SwitchContainer
from hwt.hdlObjects.types.defs import INT
from hwt.hdlObjects.types.enum import Enum
from hwt.serializer.vhdl.formater import formatVhdl
from hwt.synthesizer.assigRenderer import renderIfTree
from hwt.code import c, If, Switch
from hwt.synthesizer.rtlLevel.netlist import RtlNetlist


rmWhitespaces = re.compile(r'\s+', re.MULTILINE)


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

    def strStructureCmp(self, tmpl, cont):  
        cont = formatVhdl(str(cont))
        _tmpl = rmWhitespaces.sub(" ", tmpl).strip()
        _cont = rmWhitespaces.sub(" ", cont).strip()

        self.assertEquals(_tmpl, _cont, "%s\n\nshould be\n\n%s" % (cont, tmpl))

    def test_baicIf(self):
        a = self.n.sig('a')
        b = self.n.sig('b')

        assigs = If(a,
                    c(1, b)
                    ).Else(
                       c(0, b)
                    )

        container = list(renderIfTree(assigs))
        self.assertEqual(len(container), 1)
        container = container[0]
        tmpl = IfContainer([a], ifTrue=[c(1, b)], ifFalse=[c(0, b)])

        self.compareStructure(tmpl, container)

    def test_basicSwitch(self):
        a = self.n.sig('a', typ=INT)
        b = self.n.sig('b', typ=INT)

        assigs = Switch(a).addCases([(i, c(i, b)) for i in range(4)])
        cont = list(renderIfTree(assigs))
        self.assertEqual(len(cont), 1)
        cont = cont[0]

        tmpl = SwitchContainer(a, [(i, c(i, b)) for i in range(3)] + [(None, c(3, b))])
        self.compareStructure(tmpl, cont)

    def test_ifsInSwitch(self):
        n = self.n
        stT = Enum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, defVal=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic():
            return If(sd0 & sd1,
                      c(stT.lenExtr, st)
                      ).Else(
                       c(stT.ts1Wait, st)
                       )
        assigs = Switch(st)\
                 .Case(stT.idle,
                       tsWaitLogic()
                 ).Case(stT.tsWait,
                        tsWaitLogic()
                 ).Case(stT.ts0Wait,
                        If(sd0,
                           c(stT.lenExtr, st)
                        ).Else(
                           c(st, st)
                        )
                 ).Case(stT.ts1Wait,
                        If(sd1,
                           c(stT.lenExtr, st)
                        ).Else(
                           c(st, st)
                        )
                 ).Case(stT.lenExtr,
                        If(cntrlFifoVld & cntrlFifoLast,
                           c(stT.idle, st)
                        ).Else(
                          c(st, st)
                        )
                 )

        cont = list(renderIfTree(assigs))
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        CASE st IS
            WHEN idle =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSE 
                    st_next <= ts1Wait;
                END IF;
            WHEN tsWait =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSE 
                    st_next <= ts1Wait;
                END IF;
            WHEN ts0Wait =>
                IF (sd0)='1' THEN 
                    st_next <= lenExtr;
                ELSE 
                    st_next <= st;
                END IF;
            WHEN ts1Wait =>
                IF (sd1)='1' THEN 
                    st_next <= lenExtr;
                ELSE 
                    st_next <= st;
                END IF;
            WHEN OTHERS =>
                IF (ctrlFifoVld AND ctrlFifoLast)='1' THEN
                    st_next <= idle;
                ELSE 
                    st_next <= st;
                END IF;
        END CASE

        """
        self.strStructureCmp(tmpl, cont)

    def test_ifs2LvlInSwitch(self):
        n = self.n
        stT = Enum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, defVal=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic(ifNoTsRd):
            return If(sd0 & sd1,
                      c(stT.lenExtr, st)
                   ).Else(
                       ifNoTsRd
                   )
        assigs = Switch(st)\
                .Case(stT.idle,
                      tsWaitLogic(
                                 If(cntrlFifoVld,
                                    c(stT.tsWait, st)
                                 ).Else(
                                    c(st, st)
                                 )
                                 )
                ).Case(stT.tsWait,
                       tsWaitLogic(c(st, st))
                ).Case(stT.ts0Wait,
                       If(sd0,
                          c(stT.lenExtr, st)
                       ).Else(
                          c(st, st)
                       )
                ).Case(stT.ts1Wait,
                       If(sd1,
                          c(stT.lenExtr, st)
                       ).Else(
                          c(st, st)
                       )
                ).Case(stT.lenExtr,
                       If(cntrlFifoVld & cntrlFifoLast,
                          c(stT.idle, st)
                       ).Else(
                          c(st, st)
                       )
                )

        cont = list(renderIfTree(assigs))
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        CASE st IS
            WHEN idle =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSIF (ctrlFifoVld)='1' THEN
                    st_next <= tsWait;
                ELSE
                    st_next <= st;
                END IF;
            WHEN tsWait =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts0Wait =>
                IF (sd0)='1' THEN
                    st_next <= lenExtr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts1Wait =>
                IF (sd1)='1' THEN
                    st_next <= lenExtr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN OTHERS =>
                IF (ctrlFifoVld AND ctrlFifoLast)='1' THEN
                    st_next <= idle;
                ELSE
                    st_next <= st;
                END IF;
        END CASE

        """
        self.strStructureCmp(tmpl, cont)

    def test_ifs3LvlInSwitch(self):
        n = self.n
        stT = Enum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
        clk = n.sig('clk')
        rst = n.sig("rst")

        st = n.sig('st', stT, clk=clk, syncRst=rst, defVal=stT.idle)
        sd0 = n.sig('sd0')
        sd1 = n.sig('sd1')
        cntrlFifoVld = n.sig('ctrlFifoVld')
        cntrlFifoLast = n.sig('ctrlFifoLast')

        def tsWaitLogic(ifNoTsRd):
            return  If(sd0 & sd1,
                       c(stT.lenExtr, st)
                    ).Elif(sd0,
                       c(stT.ts1Wait, st)
                    ).Else(
                       ifNoTsRd
                    )
        assigs = Switch(st)\
            .Case(stT.idle,
                tsWaitLogic(
                    If(cntrlFifoVld,
                       c(stT.tsWait, st)
                    ).Else(
                       c(st, st)
                    )
                )
            ).Case(stT.tsWait,
                tsWaitLogic(c(st, st))
            ).Case(stT.ts0Wait,
                If(sd0,
                   c(stT.lenExtr, st)
                ).Else(
                   c(st, st)
                )
            ).Case(stT.ts1Wait,
                If(sd1,
                   c(stT.lenExtr, st)
                ).Else(
                   c(st, st)
                )
            ).Case(stT.lenExtr,
                If(cntrlFifoVld & cntrlFifoLast,
                   c(stT.idle, st)
                ).Else(
                   c(st, st)
                )
            )
    
        cont = list(renderIfTree(assigs))
        self.assertEqual(len(cont), 1)
        cont = cont[0]
        tmpl = """
        CASE st IS
            WHEN idle =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSIF (sd0)='1' THEN
                    st_next <= ts1Wait;
                ELSIF (ctrlFifoVld)='1' THEN
                    st_next <= tsWait;
                ELSE
                    st_next <= st;
                END IF;
            WHEN tsWait =>
                IF (sd0 AND sd1)='1' THEN
                    st_next <= lenExtr;
                ELSIF (sd0)='1' THEN
                    st_next <= ts1Wait;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts0Wait =>
                IF (sd0)='1' THEN
                    st_next <= lenExtr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN ts1Wait =>
                IF (sd1)='1' THEN
                    st_next <= lenExtr;
                ELSE
                    st_next <= st;
                END IF;
            WHEN OTHERS =>
                IF (ctrlFifoVld AND ctrlFifoLast)='1' THEN
                    st_next <= idle;
                ELSE
                    st_next <= st;
                END IF;
        END CASE

        """
        self.strStructureCmp(tmpl, cont)
if __name__ == '__main__':
    suite = unittest.TestSuite()
    # suite.addTest(StatementTreesTC('test_ifs3LvlInSwitch'))
    suite.addTest(unittest.makeSuite(StatementTreesTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
