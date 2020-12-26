from hwt.hdl.constants import INTF_DIRECTION
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class UnitWrapper(Unit):
    """
    Class which creates wrapper around original unit instance,
    original unit will be stored inside as subunit named baseUnit

    :note: This is example of lazy loaded interfaces
        and generating of external interfaces based on internal structure.
    """

    def __init__(self, baseUnit: Unit):
        """
        :param baseUnit: An :class:`hwt.synthesizer.unit.Unit` instance which should be hidden in this wrapper.
        """
        super(UnitWrapper, self).__init__()
        self._baseUnit = baseUnit

    def _copyParamsAndInterfaces(self):
        for p in self._baseUnit._params:
            myP = Param(p.get_value())
            self._registerParameter(p._name, myP)
            myP.set_value(p.get_value())

        origToWrapInfMap = {}

        for intf in self.baseUnit._interfaces:
            # clone interface
            myIntf = intf.__copy__()
            # sub-interfaces are not instantiated yet
            # myIntf._direction = intf._direction
            myIntf._direction = INTF_DIRECTION.opposite(intf._direction)

            self._registerInterface(intf._name, myIntf)
            object.__setattr__(self, intf._name, myIntf)

            origToWrapInfMap[intf] = myIntf

        ei = self._ctx.interfaces
        for i in self._interfaces:
            self._loadInterface(i, True)
            assert i._isExtern
            i._signalsForInterface(self._ctx, ei,
                                   self._store_manager.name_scope,
                                   reverse_dir=True)

        return origToWrapInfMap

    def _getDefaultName(self):
        return self._baseUnit._getDefaultName()

    def _get_hdl_doc(self):
        return self._baseUnit._get_hdl_doc()

    def _connectBaseUnitToThisWrap(self, origToWrapInfMap):
        for baseIntf, wrapIntf in origToWrapInfMap.items():
            if baseIntf._direction is INTF_DIRECTION.MASTER:
                wrapIntf(baseIntf)
            else:
                baseIntf(wrapIntf)

    def _impl(self):
        self.baseUnit = self._baseUnit
        origToWrapInfMap = self._copyParamsAndInterfaces()
        self._connectBaseUnitToThisWrap(origToWrapInfMap)
