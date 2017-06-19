#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing
from unittest import TestLoader, TextTestRunner, TestSuite

from hwt.simulator.hdlSimConfig import HdlSimConfig
from hwt.simulator.hdlSimulator import HdlSimulator
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.busEndpoint_test import BusEndpointTC
from hwtLib.amba.axi4_rDatapump_test import Axi4_rDatapumpTC, Axi3_rDatapumpTC
from hwtLib.amba.axi4_streamToMem_test import Axi4_streamToMemTC
from hwtLib.amba.axi4_wDatapump_test import Axi4_wDatapumpTC, \
    Axi3_wDatapump_direct_TC, Axi3_wDatapump_small_splitting_TC
from hwtLib.amba.axiLite_comp.endpoint_arr_test import AxiLiteEndpointArray, \
    AxiLiteEndpointStructsInArray
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTC, \
    AxiLiteEndpointDenseStartTC, AxiLiteEndpointDenseTC
from hwtLib.amba.axi_ag_test import Axi_ag_TC
from hwtLib.amba.axi_test import AxiTC
from hwtLib.amba.axis_comp.append_test import AxiS_append_TC
from hwtLib.amba.axis_comp.en_test import AxiS_en_TC
from hwtLib.amba.axis_comp.frameForge_test import AxiS_frameForge_TC
from hwtLib.amba.axis_comp.frameGen_test import AxisFrameGenTC
from hwtLib.amba.axis_comp.frameLinkConv_test import AxiS_frameLinkConvTC
from hwtLib.amba.axis_comp.frameParser_test import AxiS_frameParserTC
from hwtLib.amba.axis_comp.measuringFifo_test import AxiS_measuringFifoTC
from hwtLib.amba.axis_comp.resizer_test import AxiS_resizer_upscale_TC, \
    AxiS_resizer_downscale_TC, AxiS_resizer_downAndUp_TC, \
    AxiS_resizer_upAndDown_TC
from hwtLib.amba.axis_comp.storedBurst_test import AxiSStoredBurstTC
from hwtLib.amba.interconnect.rStrictOrder_test import RStrictOrderInterconnectTC
from hwtLib.amba.interconnect.wStrictOrderComplex_test import WStrictOrderInterconnectComplexTC
from hwtLib.amba.interconnect.wStrictOrder_test import WStrictOrderInterconnectTC, \
    WStrictOrderInterconnect2TC
from hwtLib.clocking.clkDivider import ClkDiv3TC
from hwtLib.handshaked.fifo_test import HsFifoTC
from hwtLib.handshaked.fork_test import HsForkTC, HsFork_randomized_TC
from hwtLib.handshaked.joinFair_test import HsJoinFair_2inputs_TC, \
    HsJoinFair_3inputs_TC
from hwtLib.handshaked.join_test import HsJoinTC, HsJoin_randomized_TC
from hwtLib.handshaked.ramAsHs_test import RamAsHs_TC
from hwtLib.handshaked.reg_test import HsRegL1D0TC, HsRegL2D1TC
from hwtLib.handshaked.resizer_test import HandshakedResizerTC
from hwtLib.i2c.masterBitCntrl_test import I2CMasterBitCntrlTC
from hwtLib.img.charToBitmap_test import CharToBitmapTC
from hwtLib.ipif.endpoint_test import IpifEndpointTC, \
    IpifEndpointDenseTC, IpifEndpointDenseStartTC, IpifEndpointArray
from hwtLib.ipif.reg_test import IpifRegTC
from hwtLib.logic.binToOneHot import BinToOneHotTC
from hwtLib.logic.cntrGray import GrayCntrTC
from hwtLib.logic.crcUtils_test import CrcUtilsTC
from hwtLib.logic.crc_test import CrcCombTC
from hwtLib.logic.lsfr import LsfrTC
from hwtLib.logic.oneHotToBin_test import OneHotToBinTC
from hwtLib.mem.atomic.flipCntr_test import FlipCntrTC
from hwtLib.mem.atomic.flipRam_test import FlipRamTC
from hwtLib.mem.atomic.flipReg_test import FlipRegTC
from hwtLib.mem.bramEndpoint_test import BramPortEndpointTC, \
    BramPortEndpointDenseTC, BramPortEndpointArray, BramPortEndpointDenseStartTC
from hwtLib.mem.cam_test import CamTC
from hwtLib.mem.clkSynchronizer_test import ClkSynchronizerTC
from hwtLib.mem.fifoAsync_test import FifoAsyncTC
from hwtLib.mem.fifo_test import FifoTC
from hwtLib.mem.lutRam_test import LutRamTC
from hwtLib.mem.ram_test import RamTC
from hwtLib.samples.iLvl.arithmetic.cntr_test import CntrTC
from hwtLib.samples.iLvl.arithmetic.selfRefCntr_test import SelfRefCntrTC
from hwtLib.samples.iLvl.arithmetic.twoCntrs_test import TwoCntrsTC
from hwtLib.samples.iLvl.arithmetic.widthCasting import WidthCastingExampleTC
from hwtLib.samples.iLvl.axi.simpleAxiRegs_test import SimpleAxiRegsTC
from hwtLib.samples.iLvl.builders.ethAddrUpdater_test import EthAddrUpdaterTC
from hwtLib.samples.iLvl.builders.handshakedBuilderSimple import HandshakedBuilderSimpleTC
from hwtLib.samples.iLvl.emptyUnitWithSpi import EmptyUnitWithSpiTC
from hwtLib.samples.iLvl.errors.errorsTestCase import ErrorsTC
from hwtLib.samples.iLvl.hdlComments_test import HdlCommentsTC
from hwtLib.samples.iLvl.hierarchy.netFilter_test import NetFilterTC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit3 import SimpleSubunit3TC
from hwtLib.samples.iLvl.hierarchy.simpleSubunit_test import SimpleSubunitTC
from hwtLib.samples.iLvl.hierarchy.unitToUnitConnection import UnitToUnitConnectionTC
from hwtLib.samples.iLvl.intfArray.interfaceArray0 import InterfaceArraySample0TC
from hwtLib.samples.iLvl.intfArray.interfaceArray1 import InterfaceArraySample1TC
from hwtLib.samples.iLvl.intfArray.interfaceArray2 import InterfaceArraySample2TC
from hwtLib.samples.iLvl.intfArray.interfaceArray3 import InterfaceArraySample3TC
from hwtLib.samples.iLvl.intfArray.interfaceArray4 import InterfaceArraySample4TC
from hwtLib.samples.iLvl.ipCoreCompatibleWrap_test import IpCoreWrapperTC
from hwtLib.samples.iLvl.mem.ram_test import RamTC as SampleRamTC
from hwtLib.samples.iLvl.mem.reg_test import DRegTC
from hwtLib.samples.iLvl.mem.rom_test import RomTC
from hwtLib.samples.iLvl.operators.concat_test import ConcatTC
from hwtLib.samples.iLvl.operators.indexing_test import IndexingTC
from hwtLib.samples.iLvl.simple2withNonDirectIntConnection import Simple2withNonDirectIntConnectionTC
from hwtLib.samples.iLvl.simpleAxiStream_test import SimpleUnitAxiStream_TC
from hwtLib.samples.iLvl.simpleWithNonDirectIntConncetion import SimpleWithNonDirectIntConncetionTC
from hwtLib.samples.iLvl.simpleWithParam import SimpleUnitWithParamTC
from hwtLib.samples.iLvl.simple_test import SimpleTC
from hwtLib.samples.iLvl.statements.constDriver_test import ConstDriverTC
from hwtLib.samples.iLvl.statements.forLoopCntrl_test import StaticForLoopCntrlTC
from hwtLib.samples.iLvl.statements.fsm_test import FsmExampleTC, HadrcodedFsmExampleTC
from hwtLib.samples.iLvl.statements.ifStm_test import IfStmTC
from hwtLib.samples.iLvl.statements.switchStm_test import SwitchStmTC
from hwtLib.samples.iLvl.statements.vldMaskConflictsResolving_test import VldMaskConflictsResolvingTC
from hwtLib.samples.iLvl.timers import TimerTC
from hwtLib.samples.rtlLvl.rtlLvl_test import RtlLvlTC
from hwtLib.spi.master_test import SpiMasterTC
from hwtLib.structManipulators.arrayBuff_writer_test import ArrayBuff_writer_TC
from hwtLib.structManipulators.arrayItemGetter_test import ArrayItemGetterTC, \
    ArrayItemGetter2in1WordTC
from hwtLib.structManipulators.cLinkedListReader_test import CLinkedListReaderTC
from hwtLib.structManipulators.cLinkedListWriter_test import CLinkedListWriterTC
from hwtLib.structManipulators.mmu2pageLvl_test import MMU_2pageLvl_TC
from hwtLib.structManipulators.structReader_test import StructReaderTC
from hwtLib.structManipulators.structWriter_test import StructWriter_TC
from hwtLib.tests.frameTemplate_test import FrameTemplateTC
from hwtLib.tests.ipCorePackager_test import IpCorePackagerTC
from hwtLib.tests.operators import OperatorTC
from hwtLib.tests.statementTrees import StatementTreesTC
from hwtLib.tests.statementTreesInternal import StatementTreesInternalTC
from hwtLib.tests.statements import StatementsTC
from hwtLib.tests.synthesizer.interfaceLevel.interfaceSynthesizerTC import InterfaceSynthesizerTC
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import SubunitsSynthesisTC
from hwtLib.tests.synthesizer.rtlLevel.optimalizator import Expr2CondTC
from hwtLib.tests.synthesizer.rtlLevel.synthesis import TestCaseSynthesis
from hwtLib.tests.synthesizer.value import ValueTC
from hwtLib.uart.rx_test import UartRxTC, UartRxBasicTC
from hwtLib.uart.tx_rx_test import UartTxRxTC
from hwtLib.uart.tx_test import UartTxTC


def doSimWithoutLog(self, time):
    sim = HdlSimulator()
    # dummy config
    sim.config = HdlSimConfig()
    # run simulation, stimul processes are register after initial initialization
    sim.simUnit(self.model, time=time, extraProcesses=self.procs)
    return sim


def testSuiteFromTCs(*tcs):
    loader = TestLoader()
    for tc in tcs:
        if issubclass(tc, SimTestCase):
            tc.doSim = doSimWithoutLog
        tc._multiprocess_can_split_ = True
    loadedTcs = [loader.loadTestsFromTestCase(tc) for tc in tcs]
    suite = TestSuite(loadedTcs)
    return suite


suite = testSuiteFromTCs(
    RtlLvlTC,
    HdlCommentsTC,
    InterfaceSynthesizerTC,
    SubunitsSynthesisTC,
    EmptyUnitWithSpiTC,
    Simple2withNonDirectIntConnectionTC,
    SimpleWithNonDirectIntConncetionTC,
    SimpleSubunit3TC,
    UnitToUnitConnectionTC,
    Expr2CondTC,
    OperatorTC,
    TestCaseSynthesis,
    ValueTC,
    StatementTreesInternalTC,
    StatementTreesTC,
    StatementsTC,
    ErrorsTC,
    StaticForLoopCntrlTC,
    SimpleUnitWithParamTC,
    SimpleSubunit2TC,
    TimerTC,
    NetFilterTC,
    InterfaceArraySample0TC,
    InterfaceArraySample1TC,
    InterfaceArraySample2TC,
    InterfaceArraySample3TC,
    InterfaceArraySample4TC,
    FrameTemplateTC,

    # component verifications
    ConcatTC,
    VldMaskConflictsResolvingTC,
    ConstDriverTC,
    WidthCastingExampleTC,
    SimpleTC,
    SimpleSubunitTC,
    IfStmTC,
    SwitchStmTC,
    LutRamTC,
    FsmExampleTC,
    HadrcodedFsmExampleTC,
    OneHotToBinTC,
    CntrTC,
    BinToOneHotTC,
    GrayCntrTC,
    TwoCntrsTC,
    SampleRamTC,
    SelfRefCntrTC,
    DRegTC,
    RomTC,
    IndexingTC,
    ClkSynchronizerTC,
    RamTC,
    SimpleUnitAxiStream_TC,
    FifoTC,
    FifoAsyncTC,
    HsJoinTC,
    HsJoin_randomized_TC,
    HsJoinFair_2inputs_TC,
    HsJoinFair_3inputs_TC,
    RamAsHs_TC,
    BramPortEndpointTC,
    BramPortEndpointDenseTC,
    BramPortEndpointDenseStartTC,
    BramPortEndpointArray,
    LsfrTC,
    ClkDiv3TC,

    FlipRegTC,
    FlipCntrTC,
    FlipRamTC,
    HsForkTC,
    HsFork_randomized_TC,
    HsFifoTC,
    HsRegL1D0TC,
    HsRegL2D1TC,
    HandshakedResizerTC,
    CamTC,
    UartTxTC,
    UartRxBasicTC,
    UartRxTC,
    UartTxRxTC,
    SpiMasterTC,
    I2CMasterBitCntrlTC,
    CrcUtilsTC,
    CrcCombTC,
    SimpleAxiRegsTC,
    AxiTC,
    BusEndpointTC,
    AxiLiteEndpointTC,
    AxiLiteEndpointDenseStartTC,
    AxiLiteEndpointDenseTC,
    AxiLiteEndpointArray,
    AxiLiteEndpointStructsInArray,
    AxisFrameGenTC,
    Axi4_rDatapumpTC,
    Axi3_rDatapumpTC,
    Axi4_wDatapumpTC,
    Axi3_wDatapump_direct_TC,
    Axi3_wDatapump_small_splitting_TC,
    AxiSStoredBurstTC,
    AxiS_en_TC,
    AxiS_measuringFifoTC,
    AxiS_resizer_upscale_TC,
    AxiS_resizer_downscale_TC,
    AxiS_resizer_downAndUp_TC,
    AxiS_resizer_upAndDown_TC,
    AxiS_frameForge_TC,
    AxiS_append_TC,
    AxiS_frameLinkConvTC,
    AxiS_frameParserTC,
    HandshakedBuilderSimpleTC,
    EthAddrUpdaterTC,

    RStrictOrderInterconnectTC,
    WStrictOrderInterconnectTC,
    WStrictOrderInterconnect2TC,
    WStrictOrderInterconnectComplexTC,

    Axi_ag_TC,
    Axi4_streamToMemTC,
    ArrayItemGetterTC,
    ArrayItemGetter2in1WordTC,
    ArrayBuff_writer_TC,
    CLinkedListReaderTC,
    CLinkedListWriterTC,
    MMU_2pageLvl_TC,
    StructWriter_TC,
    StructReaderTC,

    IpifEndpointTC,
    IpifEndpointDenseTC,
    IpifEndpointDenseStartTC,
    IpifEndpointArray,
    IpifRegTC,

    IpCoreWrapperTC,
    IpCorePackagerTC,
    CharToBitmapTC,
)


if __name__ == '__main__':
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
