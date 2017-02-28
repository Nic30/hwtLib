from hwt.hdlObjects.operator import Operator
from hwt.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busConverter import BusConverter
from hwt.hdlObjects.assignment import Assignment
from hwt.hdlObjects.portItem import PortItem
from hwt.hdlObjects.operatorDefs import AllOps
from copy import copy
from hwt.synthesizer.param import evalParam


def getEpSignal(sig, op):
    """
    @param sig: main signal
    @param op: operator on this signal

    @return: signal modified by this operator or none if this operator is creating new datapath
    """
    # we do not follow results of indexing like something[sig]
    if op.operator == AllOps.INDEX:
        if op.ops[0] is not sig:
            return
    if op.operator not in [AllOps.INDEX,
                           AllOps.ADD,
                           AllOps.SUB,
                           AllOps.MUL,
                           AllOps.DIV,
                           AllOps.CONCAT]:
        return

    if sig in op.ops:
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
        @param topIntf: interface on which should discovery start
        @param getMainSigFn: function which gets the main signal
                 form interface which should this code care about
                 usually address
        """
        self.topIntf = topIntf
        self.getMainSigFn = getMainSigFn
        self.offset = offset

    def discover(self):
        return self._discoverAddressSpace(self.topIntf, self.offset)

    @staticmethod
    def pprint(addrSpaceDict, indent=0):
        "pretty print"

        for addr in sorted(addrSpaceDict.keys()):
            item = addrSpaceDict[addr]
            if item.size > 1:
                size = "(size=%d)" % item.size
            else:
                size = ""
            _indent = "".join(["    " for _ in range(indent)])
            print("%s0x%x:%s%s" % (_indent, addr, item.name, size))
            AddressSpaceProbe.pprint(item.children, indent + 1)

    def _extractAddressMap(self, converter, offset, addrModifier, sizeModifier):
        """
        coppy address space map from converter
        """
        m = {}
        for item in converter._addrSpace:
            item = copy(item)

            item.addr = offset + addrModifier(evalParam(item.addr).val)

            m[item.addr] = item
            _size = item.size

            if item.size > 1:
                port = getattr(converter, item.name)
                if item.alignOffsetBits is not None:
                    def _addrModifier(childAddr):
                        return childAddr << item.alignOffsetBits

                    def _sizeModifier(x):
                        return sizeModifier(x) << item.alignOffsetBits
                else:
                    _addrModifier = addrModifier
                    _sizeModifier = sizeModifier

                item.children = self._discoverAddressSpace(port, item.addr, _addrModifier, _sizeModifier)
            item.size = sizeModifier(item.size)
        return m

    def walkToConverter(self, mainSig, ignoreMyParent=False):
        """
        we walk mainSig down to endpoints and we are searching for any bus converter instance
        """
        if mainSig is None:
            return

        parent = getParentUnit(mainSig)
        if isinstance(parent, BusConverter) and not ignoreMyParent:
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

    def _discoverAddressSpace(self, topIntf, offset, addrModifier=lambda x: x, sizeModifier=lambda x: x):
        _mainSig = self.getMainSigFn(topIntf)
        try:
            mainSig = _mainSig._sig
        except AttributeError:
            mainSig = _mainSig._sigInside

        addrMap = {}
        for converter in self.walkToConverter(mainSig, ignoreMyParent=True):
            addrMap = self._extractAddressMap(converter, offset, addrModifier, sizeModifier)

        return addrMap
