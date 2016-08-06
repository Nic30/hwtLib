#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from unittest import TestLoader, TextTestRunner, TestSuite

from hwtLib.mem.clkSynchronizer_test import ClkSynchronizerTC
from hwtLib.mem.fifo_test import FifoTC
from hwtLib.mem.ram_test import RamTC

from hwtLib.samples.iLvl.arithmetic.cntr_test import CntrTC
from hwtLib.samples.iLvl.arithmetic.twoCntrs_test import TwoCntrsTC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit_test import SimpleSubunitTC
from hwtLib.samples.iLvl.mem.ram_test import RamTC as SampleRamTC
from hwtLib.samples.iLvl.mem.reg_test import DRegTC
from hwtLib.samples.iLvl.mem.rom_test import RomTC
from hwtLib.samples.iLvl.operators.indexing_test import IndexingTC
from hwtLib.samples.iLvl.simple_test import SimpleTC
from hwtLib.samples.iLvl.statements.constDriver_test import ConstDriverTC
from hwtLib.samples.iLvl.statements.ifStm_test import IfStmTC
from hwtLib.samples.iLvl.statements.switchStm_test import SwitchStmTC

from hwtLib.tests.hierarchyExtractor import HierarchyExtractorTC
from hwtLib.tests.operators import OperatorTC
from hwtLib.tests.parser import ParserTC
from hwtLib.tests.statementTrees import StatementTreesTC
from hwtLib.tests.statements import StatementsTC
from hwtLib.tests.synthetisator.interfaceLevel.interfaceSyntherisatorTC import InterfaceSyntherisatorTC 
from hwtLib.tests.synthetisator.interfaceLevel.subunitsSynthesisTC import SubunitsSynthesisTC
from hwtLib.tests.synthetisator.interfaceLevel.verilogCodesign import VerilogCodesignTC
from hwtLib.tests.synthetisator.interfaceLevel.vhdlCodesign import VhdlCodesignTC
from hwtLib.tests.synthetisator.rtlLevel.optimalizator import Expr2CondTC
from hwtLib.tests.synthetisator.rtlLevel.synthesis import TestCaseSynthesis
from hwtLib.tests.synthetisator.value import ValueTC


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
        
        ConstDriverTC,
        SimpleTC,
        IfStmTC,
        SwitchStmTC,
        CntrTC,
        TwoCntrsTC,
        SimpleSubunitTC,
        SampleRamTC,
        DRegTC,
        RomTC,
        IndexingTC,
        ClkSynchronizerTC,
        RamTC,
        FifoTC,
        
    )
    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
