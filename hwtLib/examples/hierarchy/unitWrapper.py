from hwt.hdl.constants import INTF_DIRECTION
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


class UnitWrapper(Unit):
    """
    Class which creates wrapper around original unit instance,
    original unit will be stored inside as subunit named baseUnit

    :note: This is example of lazy loaded interfaces
        and generating of external interfaces based on internal stucture.
    """

    def __init__(self, baseUnit):
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
            # subinterfaces are not instanciated yet
            # myIntf._direction = intf._direction
            myIntf._direction = INTF_DIRECTION.opposite(intf._direction)

            self._registerInterface(intf._name, myIntf)
            object.__setattr__(self, intf._name, myIntf)

            origToWrapInfMap[intf] = myIntf

        for i in self._interfaces:
            self._loadInterface(i, True)

        return origToWrapInfMap

    def _getDefaultName(self):
        return self._baseUnit.__class__.__name__

    def _lazyLoadParamsAndInterfaces(self):
        self._ctx.params = self._buildParams()

        # prepare signals for interfaces
        for i in self._interfaces:
            assert i._isExtern
            signals = i._signalsForInterface(self._ctx)
            self._externInterf.extend(signals)

    def _connectBaseUnitToThisWrap(self, origToWrapInfMap):
        for baseIntf, wrapIntf in origToWrapInfMap.items():
            if baseIntf._direction is INTF_DIRECTION.MASTER:
                if isinstance(wrapIntf, list):
                    for i, _wrapIntf in enumerate(wrapIntf):
                        _wrapIntf(baseIntf[i])
                else:
                    wrapIntf(baseIntf)
            else:
                if isinstance(wrapIntf, list):
                    for i, _wrapIntf in enumerate(wrapIntf):
                        baseIntf[i](_wrapIntf)
                else:
                    baseIntf(wrapIntf)

    def _impl(self):
        self.baseUnit = self._baseUnit
        origToWrapInfMap = self._copyParamsAndInterfaces()
        self._lazyLoadParamsAndInterfaces()
        self._connectBaseUnitToThisWrap(origToWrapInfMap)
