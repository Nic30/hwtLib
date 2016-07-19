#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestLoader, TextTestRunner, TestSuite

from hwtLib.tests.hierarchyExtractor import HierarchyExtractorTC
from hwtLib.tests.operators import OperatorTC
from hwtLib.tests.parser import ParserTC

from hwtLib.tests.synthetisator.value import ValueTC

from hwtLib.tests.synthetisator.interfaceLevel.interfaceSyntherisatorTC import InterfaceSyntherisatorTC 
from hwtLib.tests.synthetisator.interfaceLevel.vhdlCodesign import VhdlCodesignTC
from hwtLib.tests.synthetisator.interfaceLevel.verilogCodesign import VerilogCodesignTC
from hwtLib.tests.synthetisator.interfaceLevel.subunitsSynthesisTC import SubunitsSynthesisTC


from hwtLib.tests.synthetisator.rtlLevel.optimalizator import Expr2CondTC
from hwtLib.tests.synthetisator.rtlLevel.synthesis import TestCaseSynthesis
from hwtLib.tests.statementTrees import StatementTreesTC
from hwtLib.tests.statements import StatementsTC

from hwtLib.samples.iLvl.twoCntrs_test import TwoCntrsTC
from hwtLib.samples.iLvl.cntr_test import CntrTC
from hwtLib.samples.iLvl.dReg_test import DRegTC

if __name__ == "__main__":
    def testSuiteFromTCs(*tcs):
        loader = TestLoader()
        loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
        suite = TestSuite(loadedTcs)
        return suite

    suite = testSuiteFromTCs(
        HierarchyExtractorTC,
        ParserTC,
        InterfaceSyntherisatorTC,
        VhdlCodesignTC,
        VerilogCodesignTC,
        SubunitsSynthesisTC,
        Expr2CondTC,
        OperatorTC,
        TestCaseSynthesis,
        ValueTC,
        StatementTreesTC,
        StatementsTC,
        DRegTC,
        CntrTC,
        TwoCntrsTC,
        
    )
    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
