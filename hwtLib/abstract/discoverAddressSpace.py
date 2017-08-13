from hwt.hdlObjects.assignment import Assignment
from hwt.hdlObjects.operator import Operator
from hwt.hdlObjects.operatorDefs import AllOps
from hwt.hdlObjects.portItem import PortItem
from hwt.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busEndpoint import BusEndpoint


def getEpSignal(sig, op):
    """
    :param sig: main signal
    :param op: operator on this signal

    :return: signal modified by this operator or none if this operator is creating new datapath
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
        self.seen = set()
        self.discovered = self._discoverAddressSpace(self.topIntf,
                                                     self.offset)

    def _extractStruct(self, converter, offset):
        t = converter.STRUCT_TEMPLATE

        for transTmpl in converter._bramPortMapped:
            # some arrays can have items with internal structure
            memberT = self._discoverAddressSpace(converter.getPort(transTmpl), offset)
            if memberT is not None:
                raise NotImplementedError("Nested address space")
        return t

    def walkToConverter(self, mainSig):
        """
        we walk mainSig down to endpoints and we are searching for any bus converter instance
        """
        if mainSig is None:
            return

        parent = getParentUnit(mainSig)
        if isinstance(parent, BusEndpoint) and parent not in self.seen:
            self.seen.add(parent)
            yield parent

        for e in mainSig.endpoints:
            if isinstance(e, Operator):
                ep = getEpSignal(mainSig, e)
                if ep is not None:
                    yield from self.walkToConverter(ep)
            elif isinstance(e, (Assignment, PortItem)):
                if e.src is mainSig:
                    yield from self.walkToConverter(e.dst)
            else:
                raise NotImplementedError(e.__class__)

    def _discoverAddressSpace(self, topIntf, offset):
        _mainSig = self.getMainSigFn(topIntf)
        try:
            mainSig = _mainSig._sig
        except AttributeError:
            mainSig = _mainSig._sigInside

        t = None
        for converter in self.walkToConverter(mainSig):
            # addrMap = self._extractAddressMap(converter, offset)
            if t is not None:
                raise NotImplementedError("Hierarchical endpoints")
            t = self._extractStruct(converter, offset)

        return t


def regSpace_formatAsCDefines(bus, getMainSigFn, offset=0, prefix=""):
    addrSpace = AddressSpaceProbe(bus, getMainSigFn, offset=offset).discover()
    buff = []
    for addr, asi in sorted(addrSpace.items(), key=lambda x: x[0]):
        buff.append("#define %s 0x%x" % (prefix + asi.name.upper(), addr))

    return "\n".join(buff)
