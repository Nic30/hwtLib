#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from unittest import TestLoader, TextTestRunner, TestSuite

from hwt.simulator.simTestCase import SimTestCase
from hwtLib.abstract.busEndpoint_test import BusEndpointTC
from hwtLib.abstract.frame_utils.alignment_utils_test import FrameAlignmentUtilsTC
from hwtLib.abstract.frame_utils.join.test import FrameJoinUtilsTC
from hwtLib.abstract.template_configured_test import TemplateConfigured_TC
from hwtLib.amba.axiLite_comp.buff_test import AxiRegTC
from hwtLib.amba.axiLite_comp.endpoint_arr_test import AxiLiteEndpointArrTCs
from hwtLib.amba.axiLite_comp.endpoint_fromInterfaces_test import \
    AxiLiteEndpoint_fromInterfaceTC, AxiLiteEndpoint_fromInterface_arr_TC
from hwtLib.amba.axiLite_comp.endpoint_struct_test import \
    AxiLiteEndpoint_arrayStruct_TC, AxiLiteEndpoint_struct_TC
from hwtLib.amba.axiLite_comp.endpoint_test import AxiLiteEndpointTCs
from hwtLib.amba.axiLite_comp.to_axi_test import AxiLite_to_Axi_TC
from hwtLib.amba.axi_comp.cache.cacheWriteAllocWawOnlyWritePropagating_test import AxiCacheWriteAllocWawOnlyWritePropagatingTCs
from hwtLib.amba.axi_comp.cache.pseudo_lru_test import PseudoLru_TC
from hwtLib.amba.axi_comp.interconnect.matrixAddrCrossbar_test import\
    AxiInterconnectMatrixAddrCrossbar_TCs
from hwtLib.amba.axi_comp.interconnect.matrixCrossbar_test import \
    AxiInterconnectMatrixCrossbar_TCs
from hwtLib.amba.axi_comp.interconnect.matrixR_test import AxiInterconnectMatrixR_TCs
from hwtLib.amba.axi_comp.interconnect.matrixW_test import AxiInterconnectMatrixW_TCs
from hwtLib.amba.axi_comp.lsu.read_aggregator_test import AxiReadAggregator_TCs
from hwtLib.amba.axi_comp.lsu.store_queue_write_propagating_test import AxiStoreQueueWritePropagating_TCs
from hwtLib.amba.axi_comp.lsu.write_aggregator_test import AxiWriteAggregator_TCs
from hwtLib.amba.axi_comp.oooOp.examples.counterArray_test import OooOpExampleCounterArray_TCs
from hwtLib.amba.axi_comp.oooOp.examples.counterHashTable_test import OooOpExampleCounterHashTable_TC
from hwtLib.amba.axi_comp.resize_test import AxiResizeTC
from hwtLib.amba.axi_comp.sim.ag_test import Axi_ag_TC
from hwtLib.amba.axi_comp.slave_timeout_test import AxiSlaveTimeoutTC
from hwtLib.amba.axi_comp.static_remap_test import AxiStaticRemapTCs
from hwtLib.amba.axi_comp.stream_to_mem_test import Axi4_streamToMemTC
from hwtLib.amba.axi_comp.tester_test import AxiTesterTC
from hwtLib.amba.axi_comp.to_axiLite_test import Axi_to_AxiLite_TC
from hwtLib.amba.axi_test import AxiTC
from hwtLib.amba.axis_comp.en_test import AxiS_en_TC
from hwtLib.amba.axis_comp.fifoDrop_test import AxiSFifoDropTC
from hwtLib.amba.axis_comp.fifoMeasuring_test import AxiS_fifoMeasuringTC
from hwtLib.amba.axis_comp.frameGen_test import AxisFrameGenTC
from hwtLib.amba.axis_comp.frame_deparser.test import AxiS_frameDeparser_TC
from hwtLib.amba.axis_comp.frame_join.test import AxiS_FrameJoin_TCs
from hwtLib.amba.axis_comp.frame_parser.footer_split_test import AxiS_footerSplitTC
from hwtLib.amba.axis_comp.frame_parser.test import AxiS_frameParserTC
from hwtLib.amba.axis_comp.resizer_test import AxiS_resizer_TCs
from hwtLib.amba.axis_comp.storedBurst_test import AxiSStoredBurstTC
from hwtLib.amba.axis_comp.strformat_test import AxiS_strFormat_TC
from hwtLib.amba.datapump.interconnect.rStrictOrder_test import \
    RStrictOrderInterconnectTC
from hwtLib.amba.datapump.interconnect.wStrictOrderComplex_test import \
    WStrictOrderInterconnectComplexTC
from hwtLib.amba.datapump.interconnect.wStrictOrder_test import \
    WStrictOrderInterconnectTC, WStrictOrderInterconnect2TC
from hwtLib.amba.datapump.r_aligned_test import Axi_rDatapump_alignedTCs
from hwtLib.amba.datapump.r_unaligned_test import Axi_rDatapump_unalignedTCs
from hwtLib.amba.datapump.w_test import Axi_wDatapumpTCs
from hwtLib.avalon.axiToMm_test import AxiToAvalonMm_TCs
from hwtLib.avalon.endpoint_test import AvalonMmEndpointTCs
from hwtLib.avalon.mm_buff_test import AvalonMmBuff_TC
from hwtLib.avalon.sim.mmAgent_test import AvalonMmAgentTC
from hwtLib.avalon.sim.stAgent_test import AvalonStAgentTC
from hwtLib.cesnet.mi32.axi4Lite_bridges_test import Mi32Axi4LiteBrigesTC
from hwtLib.cesnet.mi32.endpoint_test import Mi32EndpointTCs
from hwtLib.cesnet.mi32.interconnectMatrix_test import Mi32InterconnectMatrixTC
from hwtLib.cesnet.mi32.mi32agent_test import Mi32AgentTC
from hwtLib.cesnet.mi32.sliding_window_test import Mi32SlidingWindowTC
from hwtLib.cesnet.mi32.to_axi4Lite_test import Mi32_to_Axi4LiteTC
from hwtLib.clocking.cdc_test import CdcTC
from hwtLib.common_nonstd_interfaces.addr_data_hs_to_Axi_test import AddrDataHs_to_Axi_TCs
from hwtLib.examples.arithmetic.cntr_test import CntrTC, CntrResourceAnalysisTC
from hwtLib.examples.arithmetic.multiplierBooth_test import MultiplierBoothTC
from hwtLib.examples.arithmetic.privateSignals_test import PrivateSignalsOfStructTypeTC
from hwtLib.examples.arithmetic.selfRefCntr_test import SelfRefCntrTC
from hwtLib.examples.arithmetic.twoCntrs_test import TwoCntrsTC
from hwtLib.examples.arithmetic.vhdl_vector_auto_casts import VhdlVectorAutoCastExampleTC
from hwtLib.examples.arithmetic.widthCasting import WidthCastingExampleTC
from hwtLib.examples.axi.debugbusmonitor_test import DebugBusMonitorExampleAxiTC
from hwtLib.examples.axi.simpleAxiRegs_test import SimpleAxiRegsTC
from hwtLib.examples.builders.ethAddrUpdater_test import EthAddrUpdaterTCs
from hwtLib.examples.builders.handshakedBuilderSimple import \
    HandshakedBuilderSimpleTC
from hwtLib.examples.builders.hsBuilderSplit_test import HsBuilderSplit_TC
from hwtLib.examples.builders.hwException_test import HwExceptionCatch_TC
from hwtLib.examples.builders.pingResponder_test import PingResponderTC
from hwtLib.examples.emptyUnitWithSpi import EmptyUnitWithSpiTC
from hwtLib.examples.errors.combLoops import CombLoopAnalysisTC
from hwtLib.examples.errors.errors_test import ErrorsTC
from hwtLib.examples.hdlComments_test import HdlCommentsTC
from hwtLib.examples.hdlObjLists.listOfInterfaces0 import ListOfInterfacesSample0TC
from hwtLib.examples.hdlObjLists.listOfInterfaces1 import ListOfInterfacesSample1TC
from hwtLib.examples.hdlObjLists.listOfInterfaces2 import ListOfInterfacesSample2TC
from hwtLib.examples.hdlObjLists.listOfInterfaces3 import ListOfInterfacesSample3TC
from hwtLib.examples.hdlObjLists.listOfInterfaces4 import ListOfInterfacesSample4TC
from hwtLib.examples.hierarchy.hierarchySerialization_test import \
    HierarchySerializationTC
from hwtLib.examples.hierarchy.simpleSubunit2 import SimpleSubunit2TC
from hwtLib.examples.hierarchy.simpleSubunit3 import SimpleSubunit3TC
from hwtLib.examples.hierarchy.simpleSubunit_test import SimpleSubunitTC
from hwtLib.examples.hierarchy.unitToUnitConnection import \
    UnitToUnitConnectionTC
from hwtLib.examples.hierarchy.unitWrapper_test import UnitWrapperTC
from hwtLib.examples.mem.avalonmm_ram_test import AvalonMmBram_TC
from hwtLib.examples.mem.axi_ram_test import Axi4BRam_TC
from hwtLib.examples.mem.bram_wire import BramWireTC
from hwtLib.examples.mem.ram_test import RamResourcesTC, \
    SimpleAsyncRamTC, SimpleSyncRamTC
from hwtLib.examples.mem.reg_test import DRegTC, RegSerializationTC, \
    DoubleRRegTC, DReg_asyncRstTC
from hwtLib.examples.mem.rom_test import SimpleRomTC, SimpleSyncRomTC, \
    RomResourcesTC
from hwtLib.examples.operators.cast_test import CastTc
from hwtLib.examples.operators.concat_test import ConcatTC
from hwtLib.examples.operators.indexing_test import IndexingTC
from hwtLib.examples.parametrization_test import ParametrizationTC
from hwtLib.examples.rtlLvl.rtlLvl_test import RtlLvlTC
from hwtLib.examples.showcase0_test import Showcase0TC
from hwtLib.examples.simple2withNonDirectIntConnection import \
    Simple2withNonDirectIntConnectionTC
from hwtLib.examples.simpleAxiStream_test import SimpleUnitAxiStream_TC
from hwtLib.examples.simpleWithNonDirectIntConncetion import \
    SimpleWithNonDirectIntConncetionTC
from hwtLib.examples.simpleWithParam import SimpleUnitWithParamTC
from hwtLib.examples.simple_test import SimpleTC
from hwtLib.examples.specialIntfTypes.intfWithArray import InterfaceWithArrayTypesTC
from hwtLib.examples.statements.codeBlockStm_test import CodeBlokStmTC
from hwtLib.examples.statements.constCondition import ConstConditionTC
from hwtLib.examples.statements.constDriver_test import ConstDriverTC
from hwtLib.examples.statements.forLoopCntrl_test import StaticForLoopCntrlTC
from hwtLib.examples.statements.fsm_test import FsmExampleTC, \
    HadrcodedFsmExampleTC, FsmSerializationTC
from hwtLib.examples.statements.ifStm_test import IfStmTC
from hwtLib.examples.statements.switchStm_test import SwitchStmTC
from hwtLib.examples.statements.vldMaskConflictsResolving_test import \
    VldMaskConflictsResolvingTC
from hwtLib.examples.timers import TimerTC
from hwtLib.handshaked.cdc_test import HandshakedCdc_slow_to_fast_TC, \
    HandshakedCdc_fast_to_slow_TC
from hwtLib.handshaked.fifoAsync_test import HsFifoAsyncTC
from hwtLib.handshaked.fifo_test import HsFifoTC
from hwtLib.handshaked.handshakedToAxiStream_test import HandshakedToAxiStreamTCs
from hwtLib.handshaked.joinFair_test import HsJoinFair_2inputs_TC, \
    HsJoinFair_3inputs_TC
from hwtLib.handshaked.joinPrioritized_test import HsJoinPrioritizedTC, \
    HsJoinPrioritized_randomized_TC
from hwtLib.handshaked.ramAsHs_test import RamAsHs_TCs
from hwtLib.handshaked.reg_test import HandshakedRegTCs
from hwtLib.handshaked.resizer_test import HsResizerTC
from hwtLib.handshaked.splitCopy_test import HsSplitCopyTC, \
    HsSplitCopy_randomized_TC
from hwtLib.img.charToBitmap_test import CharToBitmapTC
from hwtLib.logic.bcdToBin_test import BcdToBinTC
from hwtLib.logic.binToBcd_test import BinToBcdTC
from hwtLib.logic.binToOneHot import BinToOneHotTC
from hwtLib.logic.bitonicSorter import BitonicSorterTC
from hwtLib.logic.cntrGray import GrayCntrTC
from hwtLib.logic.countLeading_test import CountLeadingTC
from hwtLib.logic.crcComb_test import CrcCombTC
from hwtLib.logic.crcUtils_test import CrcUtilsTC
from hwtLib.logic.crc_test import CrcTC
from hwtLib.logic.lfsr import LfsrTC
from hwtLib.logic.oneHotToBin_test import OneHotToBinTC
from hwtLib.mem.atomic.flipCntr_test import FlipCntrTC
from hwtLib.mem.atomic.flipRam_test import FlipRamTC
from hwtLib.mem.atomic.flipReg_test import FlipRegTC
from hwtLib.mem.bramEndpoint_test import BramPortEndpointTCs
from hwtLib.mem.cam_test import CamTC
from hwtLib.mem.cuckooHashTableWithRam_test import CuckooHashTableWithRamTCs
from hwtLib.mem.fifoArray_test import FifoArrayTC
from hwtLib.mem.fifoAsync_test import FifoAsyncTC
from hwtLib.mem.fifo_test import FifoWriterAgentTC, FifoReaderAgentTC, FifoTC
from hwtLib.mem.hashTableCoreWithRam_test import HashTableCoreWithRamTC
from hwtLib.mem.lutRam_test import LutRamTC
from hwtLib.mem.ramTransactional_test import RamTransactionalTCs
from hwtLib.mem.ramXor_test import RamXorSingleClockTC
from hwtLib.mem.ram_test import RamTC
from hwtLib.peripheral.displays.hd44780.driver_test import Hd44780Driver8bTC
from hwtLib.peripheral.displays.segment7_test import Segment7TC
from hwtLib.peripheral.ethernet.mac_rx_test import EthernetMac_rx_TCs
from hwtLib.peripheral.ethernet.mac_tx_test import EthernetMac_tx_TCs
from hwtLib.peripheral.ethernet.rmii_adapter_test import RmiiAdapterTC
from hwtLib.peripheral.i2c.masterBitCntrl_test import I2CMasterBitCntrlTC
from hwtLib.peripheral.mdio.master_test import MdioMasterTC
from hwtLib.peripheral.spi.master_test import SpiMasterTC
from hwtLib.peripheral.uart.rx_test import UartRxTC, UartRxBasicTC
from hwtLib.peripheral.uart.tx_rx_test import UartTxRxTC
from hwtLib.peripheral.uart.tx_test import UartTxTC
from hwtLib.peripheral.usb.sim.usb_agent_test import UsbAgentTC
from hwtLib.peripheral.usb.sim.usbip.test import UsbipTCs
from hwtLib.peripheral.usb.usb2.device_cdc_test import Usb2CdcTC
from hwtLib.peripheral.usb.usb2.sie_rx_test import Usb2SieDeviceRxTC
from hwtLib.peripheral.usb.usb2.sie_tx_test import Usb2SieDeviceTxTC
from hwtLib.peripheral.usb.usb2.ulpi_agent_test import UlpiAgent_TCs
from hwtLib.peripheral.usb.usb2.utmi_agent_test import UtmiAgentTCs
from hwtLib.peripheral.usb.usb2.utmi_to_ulpi_test import Utmi_to_UlpiTC
from hwtLib.structManipulators.arrayBuff_writer_test import ArrayBuff_writer_TC
from hwtLib.structManipulators.arrayItemGetter_test import ArrayItemGetterTC, \
    ArrayItemGetter2in1WordTC
from hwtLib.structManipulators.cLinkedListReader_test import \
    CLinkedListReaderTC
from hwtLib.structManipulators.cLinkedListWriter_test import \
    CLinkedListWriterTC
from hwtLib.structManipulators.mmu2pageLvl_test import MMU_2pageLvl_TC
from hwtLib.structManipulators.structReader_test import StructReaderTC
from hwtLib.structManipulators.structWriter_test import StructWriter_TC
from hwtLib.tests.constraints.xdc_clock_related_test import ConstraintsXdcClockRelatedTC
from hwtLib.tests.frameTmpl_test import FrameTmplTC
from hwtLib.tests.pyUtils.arrayQuery_test import ArrayQueryTC
from hwtLib.tests.pyUtils.fileUtils_test import FileUtilsTC
from hwtLib.tests.rdSynced_agent_test import RdSynced_agent_TC
from hwtLib.tests.repr_of_hdlObjs_test import ReprOfHdlObjsTC
from hwtLib.tests.resourceAnalyzer_test import ResourceAnalyzer_TC
from hwtLib.tests.serialization.hdlReaname_test import SerializerHdlRename_TC
from hwtLib.tests.serialization.ipCorePackager_test import IpCorePackagerTC
from hwtLib.tests.serialization.modes_test import SerializerModes_TC
from hwtLib.tests.serialization.tmpVar_test import Serializer_tmpVar_TC
from hwtLib.tests.serialization.vhdl_test import Vhdl2008Serializer_TC
from hwtLib.tests.simulator.basicRtlSimulatorVcdTmpDirs_test import BasicRtlSimulatorVcdTmpDirs_TCs
from hwtLib.tests.simulator.json_log_test import HsFifoJsonLogTC
from hwtLib.tests.simulator.utils_test import SimulatorUtilsTC
from hwtLib.tests.structIntf_operator_test import StructIntf_operatorTC
from hwtLib.tests.synthesizer.astNodeIoReplacing_test import AstNodeIoReplacingTC
from hwtLib.tests.synthesizer.interfaceLevel.interfaceSynthesizerTC import \
    InterfaceSynthesizerTC
from hwtLib.tests.synthesizer.interfaceLevel.subunitsSynthesisTC import \
    SubunitsSynthesisTC
from hwtLib.tests.synthesizer.rtlLevel.basic_signal_methods_test import BasicSignalMethodsTC
from hwtLib.tests.synthesizer.rtlLevel.statements_consystency_test import StatementsConsystencyTC
from hwtLib.tests.synthesizer.statementTreesInternal_test import StatementTreesInternalTC
from hwtLib.tests.synthesizer.statementTrees_test import StatementTreesTC
from hwtLib.tests.synthesizer.statements_test import StatementsTC
from hwtLib.tests.transTmpl_test import TransTmpl_TC
from hwtLib.tests.types.bitsSlicing_test import BitsSlicingTC
from hwtLib.tests.types.hstructVal_test import HStructValTC
from hwtLib.tests.types.hvalue_test import HValueTC
from hwtLib.tests.types.operators_test import OperatorTC
from hwtLib.tests.types.union_test import UnionTC
from hwtLib.tests.unionIntf_test import UnionIntfTC
from hwtLib.xilinx.ipif.axi4Lite_to_ipif_test import Axi4Lite_to_IpifTC
from hwtLib.xilinx.ipif.buff_test import IpifBuffTC
from hwtLib.xilinx.ipif.endpoint_test import IpifEndpointTC, \
    IpifEndpointDenseTC, IpifEndpointDenseStartTC, IpifEndpointArray
from hwtLib.xilinx.ipif.interconnectMatrix_test import IpifInterconnectMatrixTC
from hwtLib.xilinx.locallink.axis_conv_test import AxiS_localLinkConvTC
from hwtLib.xilinx.primitive.examples.dsp48e1Add_test import Dsp48e1Add_TCs
from hwtLib.xilinx.slr_crossing_test import HsSlrCrossingTC


# from hwt.simulator.simTestCase import SimTestCase
def testSuiteFromTCs(*tcs):
    loader = TestLoader()
    for tc in tcs:
        if not issubclass(tc, SimTestCase):
            tc._multiprocess_can_split_ = True
    loadedTcs = [
        loader.loadTestsFromTestCase(tc) for tc in tcs
        # if not issubclass(tc, SimTestCase)  # [debug] skip simulations
    ]
    suite = TestSuite(loadedTcs)
    return suite


suite = testSuiteFromTCs(
    # basic tests
    FileUtilsTC,
    ArrayQueryTC,
    RtlLvlTC,
    ReprOfHdlObjsTC,
    HdlCommentsTC,
    InterfaceSynthesizerTC,
    SubunitsSynthesisTC,
    EmptyUnitWithSpiTC,
    Simple2withNonDirectIntConnectionTC,
    SimpleWithNonDirectIntConncetionTC,
    SimpleSubunit3TC,
    UnitToUnitConnectionTC,
    OperatorTC,
    StructIntf_operatorTC,
    CastTc,
    BitsSlicingTC,
    HStructValTC,
    ParametrizationTC,
    BasicSignalMethodsTC,
    StatementsConsystencyTC,
    HValueTC,
    StatementTreesInternalTC,
    StatementTreesTC,
    StatementsTC,
    AstNodeIoReplacingTC,
    ErrorsTC,
    StaticForLoopCntrlTC,
    SimpleUnitWithParamTC,
    SimpleSubunit2TC,
    HierarchySerializationTC,
    ListOfInterfacesSample0TC,
    ListOfInterfacesSample1TC,
    ListOfInterfacesSample2TC,
    ListOfInterfacesSample3TC,
    ListOfInterfacesSample4TC,
    PrivateSignalsOfStructTypeTC,
    FrameTmplTC,
    Showcase0TC,
    SimulatorUtilsTC,
    HsFifoJsonLogTC,
    RdSynced_agent_TC,
    Segment7TC,
    SerializerModes_TC,
    Serializer_tmpVar_TC,
    SerializerHdlRename_TC,
    VhdlVectorAutoCastExampleTC,
    TransTmpl_TC,
    UnionTC,
    UnionIntfTC,
    ResourceAnalyzer_TC,
    CombLoopAnalysisTC,
    Vhdl2008Serializer_TC,
    CodeBlokStmTC,
    IfStmTC,
    SwitchStmTC,
    SimpleRomTC,
    SimpleSyncRomTC,
    RomResourcesTC,
    DRegTC,
    DoubleRRegTC,
    DReg_asyncRstTC,
    RegSerializationTC,
    CntrTC,
    CntrResourceAnalysisTC,
    ConstConditionTC,
    TemplateConfigured_TC,
    FrameAlignmentUtilsTC,
    FrameJoinUtilsTC,
    HwExceptionCatch_TC,
    PseudoLru_TC,

    # tests of simple units
    TimerTC,
    ConcatTC,
    VldMaskConflictsResolvingTC,
    ConstDriverTC,
    WidthCastingExampleTC,
    SimpleTC,
    SimpleSubunitTC,
    RamTC,
    RamXorSingleClockTC,
    *RamTransactionalTCs,
    BramWireTC,
    LutRamTC,
    FsmSerializationTC,
    FsmExampleTC,
    HadrcodedFsmExampleTC,
    OneHotToBinTC,
    BinToBcdTC,
    BcdToBinTC,
    AxiS_strFormat_TC,
    BinToOneHotTC,
    GrayCntrTC,
    TwoCntrsTC,
    SelfRefCntrTC,
    CountLeadingTC,
    MultiplierBoothTC,
    IndexingTC,
    CdcTC,
    RamResourcesTC,
    SimpleAsyncRamTC,
    SimpleSyncRamTC,
    SimpleUnitAxiStream_TC,
    FifoWriterAgentTC,
    FifoReaderAgentTC,
    FifoTC,
    FifoAsyncTC,
    FifoArrayTC,
    HsJoinPrioritizedTC,
    HsJoinPrioritized_randomized_TC,
    HsJoinFair_2inputs_TC,
    HsJoinFair_3inputs_TC,
    HandshakedCdc_slow_to_fast_TC,
    HandshakedCdc_fast_to_slow_TC,
    *HandshakedToAxiStreamTCs,
    *RamAsHs_TCs,
    LfsrTC,
    BitonicSorterTC,
    InterfaceWithArrayTypesTC,

    FlipRegTC,
    FlipCntrTC,
    FlipRamTC,
    HsSplitCopyTC,
    HsSplitCopy_randomized_TC,
    HsFifoTC,
    HsFifoAsyncTC,
    *HandshakedRegTCs,
    HsResizerTC,
    HsBuilderSplit_TC,
    CamTC,
    UartTxTC,
    UartRxBasicTC,
    UartRxTC,
    UartTxRxTC,
    SpiMasterTC,
    I2CMasterBitCntrlTC,
    *EthernetMac_rx_TCs,
    *EthernetMac_tx_TCs,
    MdioMasterTC,
    Hd44780Driver8bTC,
    CrcUtilsTC,
    CrcCombTC,
    CrcTC,
    UsbAgentTC,
    *UlpiAgent_TCs,
    *UtmiAgentTCs,
    Utmi_to_UlpiTC,
    Usb2SieDeviceRxTC,
    Usb2SieDeviceTxTC,
    Usb2CdcTC,
    *UsbipTCs,

    BusEndpointTC,

    *BramPortEndpointTCs,

    # avalon tests
    AvalonMmAgentTC,
    *AvalonMmEndpointTCs,
    AvalonMmBram_TC,
    *AxiToAvalonMm_TCs,
    AvalonStAgentTC,
    AvalonMmBuff_TC,

    # axi tests
    SimpleAxiRegsTC,
    AxiTC,
    *AxiLiteEndpointTCs,
    *AxiLiteEndpointArrTCs,
    AxiLiteEndpoint_struct_TC,
    AxiLiteEndpoint_arrayStruct_TC,
    AxiLiteEndpoint_fromInterfaceTC,
    AxiLiteEndpoint_fromInterface_arr_TC,
    AxiLite_to_Axi_TC,
    Axi_to_AxiLite_TC,
    AxiRegTC,
    AxiTesterTC,
    *AxiStaticRemapTCs,
    AxiResizeTC,

    AxisFrameGenTC,
    *AddrDataHs_to_Axi_TCs,
    Axi4BRam_TC,
    *Axi_rDatapump_alignedTCs,
    *Axi_rDatapump_unalignedTCs,
    *Axi_wDatapumpTCs,
    AxiSlaveTimeoutTC,
    AxiSStoredBurstTC,
    AxiS_en_TC,
    AxiS_fifoMeasuringTC,
    AxiSFifoDropTC,
    *AxiS_resizer_TCs,
    AxiS_frameDeparser_TC,
    AxiS_localLinkConvTC,
    AxiS_footerSplitTC,
    AxiS_frameParserTC,
    *AxiS_FrameJoin_TCs,
    HandshakedBuilderSimpleTC,
    *EthAddrUpdaterTCs,

    RStrictOrderInterconnectTC,
    WStrictOrderInterconnectTC,
    WStrictOrderInterconnect2TC,
    WStrictOrderInterconnectComplexTC,

    *AxiInterconnectMatrixAddrCrossbar_TCs,
    *AxiInterconnectMatrixCrossbar_TCs,
    *AxiInterconnectMatrixR_TCs,
    *AxiInterconnectMatrixW_TCs,

    *AxiWriteAggregator_TCs,
    *AxiReadAggregator_TCs,
    *AxiStoreQueueWritePropagating_TCs,
    *AxiCacheWriteAllocWawOnlyWritePropagatingTCs,

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
    *OooOpExampleCounterArray_TCs,
    OooOpExampleCounterHashTable_TC,

    # ipif tests
    IpifEndpointTC,
    IpifEndpointDenseTC,
    IpifEndpointDenseStartTC,
    IpifEndpointArray,
    IpifBuffTC,
    Axi4Lite_to_IpifTC,
    IpifInterconnectMatrixTC,

    Mi32AgentTC,
    Mi32InterconnectMatrixTC,
    Mi32_to_Axi4LiteTC,
    Mi32Axi4LiteBrigesTC,
    Mi32SlidingWindowTC,
    *Mi32EndpointTCs,

    # complex units tests
    UnitWrapperTC,
    IpCorePackagerTC,
    CharToBitmapTC,
    HashTableCoreWithRamTC,
    *CuckooHashTableWithRamTCs,
    PingResponderTC,
    DebugBusMonitorExampleAxiTC,

    RmiiAdapterTC,
    ConstraintsXdcClockRelatedTC,
    HsSlrCrossingTC,
    *Dsp48e1Add_TCs,
    *BasicRtlSimulatorVcdTmpDirs_TCs,
)


def main():
    # runner = TextTestRunner(verbosity=2, failfast=True)
    runner = TextTestRunner(verbosity=2)

    try:
        from concurrencytest import ConcurrentTestSuite, fork_for_tests
        useParallerlTest = True
    except ImportError:
        # concurrencytest is not installed, use regular test runner
        useParallerlTest = False
    # useParallerlTest = False

    if useParallerlTest:
        concurrent_suite = ConcurrentTestSuite(suite, fork_for_tests())
        res = runner.run(concurrent_suite)
    else:
        res = runner.run(suite)
    if not res.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    main()
