from hwt.synthesizer.interface import Interface
from hwt.interfaces.std import VectSignal, Signal, Handshaked, VldSynced
from ipCorePackager.constants import DIRECTION
from hwt.hdl.types.defs import BIT_N, BIT
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.bits import Bits
from hwt.interfaces.structIntf import HdlType_to_Interface


class Utmi_8b_rx(VldSynced):

    def _config(self):
        VldSynced._config(self)
        self.DATA_WIDTH = 8

    def _declr(self):
        VldSynced._declr(self)
        self.active = Signal()
        self.error = Signal()


utmi_function_control_t = HStruct(
    (Bits(2), "XcvrSelect"),
    (BIT, "TermSelect"),
    (Bits(2), "OpMode"),
    (BIT, "Reset"),
    (BIT, "SuspendM"),
    (BIT, None),
)

utmi_interface_control_t = HStruct(
    (BIT, "FsLsSerialMode_6pin"),
    (BIT, "FsLsSerialMode_3pin"),
    (BIT, "CarkitMode"),
    (BIT, "ClockSuspendM"),
    (BIT, "AutoResume"),
    (BIT, "IndicatorComplement"),
    (BIT, "IndicatorPassThru"),
    (BIT, "InterfaceProtectDisable"),
)

utmi_otg_control_t = HStruct(
    (BIT, "IdPullup"),
    (BIT, "DpPulldown"),
    (BIT, "DmPulldown"),
    (BIT, "DischrgVbus"),
    (BIT, "ChrgVbus"),
    (BIT, "DrvVbus"),
    (BIT, "DrvVbusExternal"),
    (BIT, "UseExternalVbusIndicator"),
)

utmi_interrupt_t = HStruct(
    (BIT, "HostDisconnect"),
    (BIT, "VbusValid"),
    (BIT, "SessValid"),
    (BIT, "SessEnd"),
    (BIT, "IdGnd"),
    (Bits(3), None),
)


class Utmi_8b(Interface):
    """
    UTMI+ (USB 2.0 Transceiver Macrocell Interace) Level 3 8b variant only

    https://www.intel.com/content/dam/www/public/us/en/documents/technical-specifications/usb2-transceiver-macrocell-interface-specification.pdf
    http://ww1.microchip.com/downloads/en/DeviceDoc/00002142A.pdf
    """

    class XCVR_SELECT():
        HS = 0
        FS = 1

    class TERM_SELECT():
        HS = 0
        FS = 1

    class OP_MODE():
        NORMAL = 0b00
        NON_DRIVING = 0b01
        DISABLE_BIT_STUFFING_AND_NRZI = 0b10
        # 0b11 is reserved

    class LINE_STATE():
        SE0 = 0b00  # (D+, D-)=  (0, 0)
        J = 0b01  # (D+, D-)=  (0, 1)
        K = 0b10  # (D+, D-)=  (1, 0)
        SE1 = 0b11  # (D+, D-)=  (1, 1)

    class LINE_STATE_BIT():
        DP = 0  # data + pin
        DM = 1  # data - pin

    def _declr(self):
        self.LineState = VectSignal(2)
        self.function_control = HdlType_to_Interface().apply(utmi_function_control_t, masterDir=DIRECTION.IN)
        self.otg_control = HdlType_to_Interface().apply(utmi_otg_control_t, masterDir=DIRECTION.IN)
        self.interrupt = HdlType_to_Interface().apply(utmi_interrupt_t)

        self.tx = Handshaked(masterDir=DIRECTION.IN)
        self.tx.DATA_WIDTH = 8

        self.rx = Utmi_8b_rx()
