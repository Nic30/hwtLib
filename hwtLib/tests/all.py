#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import TestLoader, TextTestRunner, TestSuite

from hwtLib.axi.axi4_rDatapump_test import Axi4_rDatapumpTC, Axi3_rDatapumpTC
from hwtLib.axi.axi4_wDatapump_test import Axi4_wDatapumpTC, \
    Axi3_wDatapump_direct_TC
from hwtLib.axi.axi_test import AxiTC
from hwtLib.axi.axis_measuringFifo_test import AxiS_measuringFifoTC
from hwtLib.handshaked.fifo_test import HsFifoTC
from hwtLib.handshaked.fork_test import HsForkTC, HsFork_randomized_TC
from hwtLib.handshaked.reg2_test import HsReg2TC
from hwtLib.handshaked.reg_test import HsRegTC
from hwtLib.mem.atomic.flipCntr_test import FlipCntrTC
from hwtLib.mem.atomic.flipReg_test import FlipRegTC
from hwtLib.mem.cam_test import CamTC
from hwtLib.mem.clkSynchronizer_test import ClkSynchronizerTC
from hwtLib.mem.fifo_test import FifoTC
from hwtLib.mem.lutRam_test import LutRamTC
from hwtLib.mem.ram_test import RamTC
from hwtLib.samples.iLvl.arithmetic.cntr_test import CntrTC
from hwtLib.samples.iLvl.arithmetic.selfRefCntr_test import SelfRefCntrTC
from hwtLib.samples.iLvl.arithmetic.twoCntrs_test import TwoCntrsTC
from hwtLib.samples.iLvl.axi.simpleAxiRegs_test import SimpleAxiRegsTC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit_test import SimpleSubunitTC
from hwtLib.samples.iLvl.mem.ram_test import RamTC as SampleRamTC
from hwtLib.samples.iLvl.mem.reg_test import DRegTC
from hwtLib.samples.iLvl.mem.rom_test import RomTC
from hwtLib.samples.iLvl.operators.indexing_test import IndexingTC
from hwtLib.samples.iLvl.simple_test import SimpleTC
from hwtLib.samples.iLvl.statements.constDriver_test import ConstDriverTC
from hwtLib.samples.iLvl.statements.fsm_test import FsmExampleTC, HadrcodedFsmExampleTC
from hwtLib.samples.iLvl.statements.ifStm_test import IfStmTC
from hwtLib.samples.iLvl.statements.switchStm_test import SwitchStmTC
from hwtLib.structManipulators.cLinkedListReader_test import CLinkedListReaderTC
from hwtLib.tests.operators import OperatorTC
from hwtLib.tests.statementTrees import StatementTreesTC
from hwtLib.tests.statements import StatementsTC
from hwtLib.tests.synthesizer.interfaceLevel.interfaceSynthesizerTC import InterfaceSynthesizerTC 
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import SubunitsSynthesisTC
from hwtLib.tests.synthesizer.rtlLevel.optimalizator import Expr2CondTC
from hwtLib.tests.synthesizer.rtlLevel.synthesis import TestCaseSynthesis
from hwtLib.tests.synthesizer.value import ValueTC


if __name__ == "__main__":
    def testSuiteFromTCs(*tcs):
        loader = TestLoader()
        loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
        suite = TestSuite(loadedTcs)
        return suite

    suite = testSuiteFromTCs(
        InterfaceSynthesizerTC,
        SubunitsSynthesisTC,
        Expr2CondTC,
        OperatorTC,
        TestCaseSynthesis,
        ValueTC,
        StatementTreesTC,
        StatementsTC,
        
        # component verifications
        ConstDriverTC,
        SimpleTC,
        SimpleSubunitTC,
        IfStmTC,
        SwitchStmTC,
        LutRamTC,
        FsmExampleTC,
        HadrcodedFsmExampleTC,
        CntrTC,
        TwoCntrsTC,
        SampleRamTC,
        SelfRefCntrTC,
        DRegTC,
        RomTC,
        IndexingTC,
        ClkSynchronizerTC,
        RamTC,
        FifoTC,
        FlipRegTC,
        FlipCntrTC,
        HsForkTC,
        HsFork_randomized_TC,
        HsFifoTC,
        HsRegTC,
        HsReg2TC,
        CamTC,
        SimpleAxiRegsTC,
        AxiTC,
        Axi4_rDatapumpTC,
        Axi3_rDatapumpTC,
        Axi4_wDatapumpTC,
        Axi3_wDatapump_direct_TC,
        AxiS_measuringFifoTC,
        
        CLinkedListReaderTC,
    )
    runner = TextTestRunner(verbosity=2)
    runner.run(suite)
