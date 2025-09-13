from hwt.constants import INTF_DIRECTION
from hwt.hwIO import HwIO
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam


class HwModuleWrapper(HwModule):
    """
    Class which creates wrapper around original unit instance,
    original unit will be stored inside as subunit named baseModule

    :note: This is example of lazy loaded interfaces
        and generating of external interfaces based on internal structure.
    """

    def __init__(self, baseModule: HwModule):
        """
        :param baseModule: An :class:`hwt.hwModule.HwModule` instance which should be hidden in this wrapper.
        """
        super(HwModuleWrapper, self).__init__()
        self._baseModule = baseModule

    def _copyParamsAndInterfaces(self):
        for p in self._baseModule._hwParams:
            myP = HwParam(p.get_value())
            self._registerParameter(p._name, myP)
            myP.set_value(p.get_value())

        origToWrapInfMap = {}

        for hwIO in self.baseModule._hwIOs:
            # clone interface
            hwIO_copy = hwIO.__copy__()
            hwIO_copy: HwIO
            # sub-interfaces are not instantiated yet
            # hwIO_copy._direction = hwIO._direction
            hwIO_copy._direction = INTF_DIRECTION.opposite(hwIO._direction)

            self._registerHwIO(hwIO._name, hwIO_copy, hwIO._onParentPropertyPath, False)
            object.__setattr__(self, hwIO._name, hwIO_copy)

            origToWrapInfMap[hwIO] = hwIO_copy

        ei = self._rtlCtx.hwIOs
        for hwIO in self._hwIOs:
            self._loadHwIODeclarations(hwIO, True)
            assert hwIO._isExtern
            hwIO._signalsForHwIO(self._rtlCtx, ei,
                                   self._store_manager.name_scope,
                                   reverse_dir=True)

        return origToWrapInfMap

    def _getDefaultName(self):
        return self._baseModule._getDefaultName()

    def _get_hdl_doc(self):
        return self._baseModule._get_hdl_doc()

    def _connectBaseModuleToThisWrap(self, origToWrapHwIOMap):
        for baseHwIO, wrapHwIO in origToWrapHwIOMap.items():
            if baseHwIO._direction is INTF_DIRECTION.MASTER:
                wrapHwIO(baseHwIO)
            else:
                baseHwIO(wrapHwIO)

    def hwImpl(self):
        self.baseModule = self._baseModule
        origToWrapInfMap = self._copyParamsAndInterfaces()
        self._connectBaseModuleToThisWrap(origToWrapInfMap)
