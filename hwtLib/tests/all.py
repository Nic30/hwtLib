#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing
from unittest import TestLoader, TextTestRunner, TestSuite

from hwtLib.amba.axi4_rDatapump_test import Axi4_rDatapumpTC, Axi3_rDatapumpTC
from hwtLib.amba.axi4_wDatapump_test import Axi4_wDatapumpTC, \
    Axi3_wDatapump_direct_TC
from hwtLib.amba.axi_test import AxiTC
from hwtLib.amba.axis_comp.measuringFifo_test import AxiS_measuringFifoTC
from hwtLib.amba.axis_comp.resizer_test import AxiS_resizer_upscale_TC, \
    AxiS_resizer_downscale_TC
from hwtLib.amba.interconnect.rStrictOrder_test import RStrictOrderInterconnectTC
from hwtLib.amba.interconnect.wStrictOrder_test import WStrictOrderInterconnectTC
from hwtLib.handshaked.fifo_test import HsFifoTC
from hwtLib.handshaked.fork_test import HsForkTC, HsFork_randomized_TC
from hwtLib.handshaked.joinFair_test import HsJoinFair_2inputs_TC, \
    HsJoinFair_3inputs_TC
from hwtLib.handshaked.join_test import HsJoinTC, HsJoin_randomized_TC
from hwtLib.handshaked.reg2_test import HsReg2TC
from hwtLib.handshaked.reg_test import HsRegTC
from hwtLib.logic.oneHotToBin_test import OneHotToBinTC
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
from hwtLib.samples.iLvl.errors.errorsTestCase import ErrorsTC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit_test import SimpleSubunitTC
from hwtLib.samples.iLvl.ipCoreCompatibleWrap_test import IpCoreWrapperTC
from hwtLib.samples.iLvl.mem.ram_test import RamTC as SampleRamTC
from hwtLib.samples.iLvl.mem.reg_test import DRegTC
from hwtLib.samples.iLvl.mem.rom_test import RomTC
from hwtLib.samples.iLvl.operators.indexing_test import IndexingTC
from hwtLib.samples.iLvl.simple_test import SimpleTC
from hwtLib.samples.iLvl.statements.constDriver_test import ConstDriverTC
from hwtLib.samples.iLvl.statements.fsm_test import FsmExampleTC, HadrcodedFsmExampleTC
from hwtLib.samples.iLvl.statements.ifStm_test import IfStmTC
from hwtLib.samples.iLvl.statements.switchStm_test import SwitchStmTC
from hwtLib.structManipulators.arrayBuff_writer_test import ArrayBuff_writer_TC
from hwtLib.structManipulators.arrayItemGetter_test import ArrayItemGetterTC
from hwtLib.structManipulators.cLinkedListReader_test import CLinkedListReaderTC
from hwtLib.structManipulators.cLinkedListWriter_test import CLinkedListWriterTC
from hwtLib.tests.operators import OperatorTC
from hwtLib.tests.statementTrees import StatementTreesTC
from hwtLib.tests.statements import StatementsTC
from hwtLib.tests.synthesizer.interfaceLevel.interfaceSynthesizerTC import InterfaceSynthesizerTC
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import SubunitsSynthesisTC
from hwtLib.tests.synthesizer.rtlLevel.optimalizator import Expr2CondTC
from hwtLib.tests.synthesizer.rtlLevel.synthesis import TestCaseSynthesis
from hwtLib.tests.synthesizer.value import ValueTC
from hwtLib.uart.rx_test import UartRxTC
from hwtLib.uart.tx_test import UartTxTC


if __name__ == "__main__":
    def testSuiteFromTCs(*tcs):
        loader = TestLoader()
        for tc in tcs:
            tc._multiprocess_can_split_ = True
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
        ErrorsTC,

        # component verifications
        ConstDriverTC,
        SimpleTC,
        SimpleSubunitTC,
        IfStmTC,
        SwitchStmTC,
        LutRamTC,
        FsmExampleTC,
        HadrcodedFsmExampleTC,
        OneHotToBinTC,
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
        HsJoinTC,
        HsJoin_randomized_TC,
        HsJoinFair_2inputs_TC,
        HsJoinFair_3inputs_TC,
        FlipRegTC,
        FlipCntrTC,
        HsForkTC,
        HsFork_randomized_TC,
        HsFifoTC,
        HsRegTC,
        HsReg2TC,
        CamTC,
        UartTxTC,
        UartRxTC,
        SimpleAxiRegsTC,
        AxiTC,
        Axi4_rDatapumpTC,
        Axi3_rDatapumpTC,
        Axi4_wDatapumpTC,
        Axi3_wDatapump_direct_TC,
        AxiS_measuringFifoTC,
        AxiS_resizer_upscale_TC,
        AxiS_resizer_downscale_TC,

        RStrictOrderInterconnectTC,
        WStrictOrderInterconnectTC,

        ArrayItemGetterTC,
        ArrayBuff_writer_TC,
        CLinkedListReaderTC,
        CLinkedListWriterTC,

        IpCoreWrapperTC,
    )
    runner = TextTestRunner(verbosity=2)

    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallerlTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallerlTest = False

    if useParallerlTest:
        # Run same tests across 4 processes
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests(multiprocessing.cpu_count()))
        runner.run(concurrent_suite)
    else:
        runner.run(suite)
