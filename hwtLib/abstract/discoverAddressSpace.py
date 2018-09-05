from hwt.hdl.assignment import Assignment
from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import AllOps, isEventDependentOp
from hwt.hdl.portItem import PortItem
from hwt.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.abstract.busInterconnect import BusInterconnect


def getEpSignal(sig, op):
    """
    :param sig: main signal
    :param op: operator on this signal

    :return: signal modified by this operator or none if this operator
        is creating new datapath
    """
    # we do not follow results of indexing like something[sig]
    if op.operator == AllOps.INDEX:
        if op.operands[0] is not sig:
            return
    if op.operator not in [AllOps.INDEX,
                           AllOps.ADD,
                           AllOps.SUB,
                           AllOps.MUL,
                           AllOps.DIV,
                           AllOps.CONCAT]:
        return

    if sig in op.operands:
        return op.result


def getParentUnit(sig):
    try:
        intf = sig._interface
    except AttributeError:
        return  # if there is no interface it cant have parent unit

    while not isinstance(intf._parent, UnitBase):
        intf = intf._parent
    return intf._parent


class AddressSpaceProbe(object):

    def __init__(self, topIntf, getMainSigFn, offset=0):
        """
        :param topIntf: interface on which should discovery start
        :param getMainSigFn: function which gets the main signal
            form interface which should this code care about
            usually address
        """
        self.topIntf = topIntf
        self.getMainSigFn = getMainSigFn
        self.offset = offset
        self.seen = set([None, ])
        self.discovered = self._discoverAddressSpace(self.topIntf,
                                                     self.offset)

    def _extractStruct(self, converter, offset):
        t = converter.STRUCT_TEMPLATE

        for transTmpl in converter._bramPortMapped:
            # some arrays can have items with internal structure
            memberT = self._discoverAddressSpace(
                converter.getPort(transTmpl), offset)
            if memberT is not None:
                raise NotImplementedError("Nested address space")
        return t

    def walkToConverter(self, mainSig, offset):
        """
        walk mainSig down to endpoints and search for any bus converter
        instances

        :return: generator of typles (offset, converter instance)
        """
        if mainSig in self.seen:
            return

        self.seen.add(mainSig)

        parent = getParentUnit(mainSig)

        if parent not in self.seen:
            self.seen.add(parent)
            if isinstance(parent, BusEndpoint):
                yield offset, parent
                return
            elif isinstance(parent, BusBridge):
                i = parent.m
                yield from self.walkToConverter(self._getMainSigFn(i), offset)
                return
            elif isinstance(parent, BusInterconnect):
                if len(parent._masters) != 1:
                    raise NotImplementedError()
                for intf, addrRec in zip(parent.m, parent._slaves):
                    _offset = addrRec[0]
                    yield from self.walkToConverter(self._getMainSigFn(intf),
                                                    offset + _offset)
                return

        for e in mainSig.endpoints:
            if isinstance(e, Operator) and not isEventDependentOp(e):
                ep = getEpSignal(mainSig, e)
                yield from self.walkToConverter(ep, offset)
            elif isinstance(e, (Assignment, PortItem)):
                yield from self.walkToConverter(e.dst, offset)
            else:
                for outp in e._outputs:
                    yield from self.walkToConverter(outp, offset)

    def _getMainSigFn(self, intf):
        _mainSig = self.getMainSigFn(intf)
        try:
            return _mainSig._sig
        except AttributeError:
            return _mainSig._sigInside

    def _discoverAddressSpace(self, topIntf, offset):
        mainSig = self._getMainSigFn(topIntf)
        t = None
        for _offset, converter in self.walkToConverter(mainSig, offset):
            # addrMap = self._extractAddressMap(converter, offset)
            if t is not None:
                raise NotImplementedError("Hierarchical endpoints")
            t = self._extractStruct(converter, _offset)

        return t
