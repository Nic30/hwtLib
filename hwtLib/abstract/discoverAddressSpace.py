from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.operator import Operator
from hwt.hdl.operatorDefs import AllOps, isEventDependentOp
from hwt.hdl.portItem import HdlPortItem
from hwt.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.abstract.busEndpoint import BusEndpoint
from hwtLib.abstract.busInterconnect import BusInterconnect
from hwtLib.abstract.busStaticRemap import BusStaticRemap


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
        return  # if there is no interface it cant be a signal in IO of :class:`hwt.synthesizer.unit.Unit` instance

    while not isinstance(intf._parent, UnitBase):
        intf = intf._parent
    return intf._parent


class AddressSpaceProbe(object):
    """
    An object which can be used to discover an address space of an interface.
    Discovery is made by walking on address signal.
    """

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

        for ( _, _), transTmpl in converter._bramPortMapped:
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
            # check if the parent :class:`hwt.synthesizer.unit.Unit` instance is some specific component
            # which handles bus protocol
            self.seen.add(parent)
            if isinstance(parent, BusEndpoint):
                yield offset, parent
                return
            elif isinstance(parent, BusBridge):
                i = parent.m
                yield from self.walkToConverter(self._getMainSigFn(i), offset)
                return
            elif isinstance(parent, BusStaticRemap):
                i = parent.m
                for _offset, _parent in self.walkToConverter(self._getMainSigFn(i), 0):
                    yield parent.translate_addr_val(parent.MEM_MAP, _offset) + offset, _parent
            elif isinstance(parent, BusInterconnect):
                if len(parent._masters) != 1:
                    raise NotImplementedError()
                for intf, addrRec in zip(parent.m, parent._slaves):
                    _offset = addrRec[0]
                    yield from self.walkToConverter(self._getMainSigFn(intf),
                                                    offset + _offset)
                return

        # walk endpoints where this signal is connected
        for e in mainSig.endpoints:
            if isinstance(e, Operator) and not isEventDependentOp(e):
                ep = getEpSignal(mainSig, e)
                yield from self.walkToConverter(ep, offset)
            elif isinstance(e, (HdlAssignmentContainer, HdlPortItem)):
                yield from self.walkToConverter(e.dst, offset)
            else:
                for outp in e._outputs:
                    yield from self.walkToConverter(outp, offset)

    def _getMainSigFn(self, intf):
        _mainSig = self.getMainSigFn(intf)
        s = _mainSig._sig
        if s is None:
            return _mainSig._sigInside
        else:
            return s

    def _discoverAddressSpace(self, topIntf, offset):
        mainSig = self._getMainSigFn(topIntf)
        t = None
        for _offset, converter in self.walkToConverter(mainSig, offset):
            # addrMap = self._extractAddressMap(converter, offset)
            if t is not None:
                raise NotImplementedError("Hierarchical endpoints")
            t = self._extractStruct(converter, _offset)

        return t
