from copy import copy
import pprint

from hwt.bitmask import mask
from hwt.hdlObjects.assignment import Assignment
from hwt.hdlObjects.operator import Operator
from hwt.hdlObjects.operatorDefs import AllOps
from hwt.hdlObjects.portItem import PortItem
from hwt.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busConverter import BusConverter
from hwt.hdlObjects.types.array import Array


def getEpSignal(sig, op):
    """
    :param sig: main signal
    :param op: operator on this signal

    :return: signal modified by this operator or none if this operator is creating new datapath
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


class AddrSpaceItem(object):
    """
    Container of informations about space in memory
    :ivar port: port for this item on converter
    :ivar children: nested addr space items (dict addr:addrspaceitem)
    """
    def __init__(self, addr, name, size=1, origin=None, alignOffsetBits=None):
        """
        :param addr: base addr for this addr item
        :param name: name of this addr item, (port with same name will be created for this item)
        :param size: used for memories, number of items in memory
        :param alignOffsetBits: used for memories, number of bits which should be trimmed (from LSB side)
            from bus interface to make aligned address for this item
        :param origin: object from which this was generated usually HStructField
        """
        self.port = None
        self.children = {}

        self.name = name
        self.addr = addr
        self.size = size
        self.alignOffsetBits = alignOffsetBits
        self.origin = origin

    def assertNoOverlap(self, nextItem):
        left0 = self.addr + self.size
        right1 = nextItem.addr
        assert left0 <= right1, (self, nextItem)

    @staticmethod
    def checkOverlapping(addrSpace):
        """
        :param addrSpace: sorted list of AddrSpaceItems
        """
        last = None
        for item in addrSpace:
            if last is None:
                pass
            else:
                last.assertNoOverlap(item)

            last = item

    def getMyAddrPrefix(self):
        """
        :return: None if base addr is not aligned to size and prefix can not be used
                 tuple (prefix, subAddrBits) if can be mapped by prefix
        """
        if self.size == 1:
            return self.addr, 0
        else:
            subAddrBits = (self.size - 1).bit_length()

        if self.addr & mask(subAddrBits):
            # is addr is not aligned to size
            return None
        return self.addr >> subAddrBits, subAddrBits

    def __repr__(self):
        if self.children:
            children = ",\n" + pprint.pformat(self.children, 2) + "\n "
        else:
            children = ""

        if self.size is None:
            size = 1
        else:
            size = self.size

        return "<AddrSpaceItem %s, %d, size=%d%s>" % (self.name, self.addr, size, children)


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

    def discover(self):
        return self._discoverAddressSpace(self.topIntf, self.offset, ignoreMyParent=False)

    @staticmethod
    def pprint(addrSpaceDict, indent=0, doPrint=True):
        "pretty print for addrSpaceDict (result of discover())"
        buff = []

        for addr in sorted(addrSpaceDict.keys()):
            item = addrSpaceDict[addr]
            if item.size is not None and item.size > 1:
                size = "(size=%d)" % item.size
            else:
                size = ""
            _indent = "".join(["    " for _ in range(indent)])
            tmp = "%s0x%x:%s%s" % (_indent, addr, item.name, size)
            if doPrint:
                print(tmp)
            else:
                buff.append(tmp)

            subTmp = AddressSpaceProbe.pprint(item.children, indent + 1)
            if not doPrint and subTmp:
                buff.append(subTmp)

        return "\n".join(buff)

    def _extractAddressMap(self, converter, offset, addrModifier, sizeModifier):
        """
        coppy address space map from converter
        """
        m = {}
        ADDR_STEP = converter._getAddrStep()
        for _item in converter.ADRESS_MAP:
            addr = _item.bitAddr // ADDR_STEP
            if isinstance(_item.dtype, Array):
                size = _item.itemCnt
                _prefix = _item.getMyAddrPrefix(ADDR_STEP)
                try:
                    (_, bitForAligin) = _prefix
                except TypeError:
                    bitForAligin = 0
            else:
                size = None
                bitForAligin = 0

            item = AddrSpaceItem(addr, _item.origin.name, size, _item.origin, bitForAligin)
            item.addr = offset + addrModifier(addr)

            m[addr] = item

            if size is not None and size > 1:
                port = converter.decoded._fieldsToInterfaces[_item.origin]
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

    def _discoverAddressSpace(self, topIntf, offset,
                              addrModifier=lambda x: x,
                              sizeModifier=lambda x: x,
                              ignoreMyParent=True):
        _mainSig = self.getMainSigFn(topIntf)
        try:
            mainSig = _mainSig._sig
        except AttributeError:
            mainSig = _mainSig._sigInside

        addrMap = {}
        for converter in self.walkToConverter(mainSig, ignoreMyParent=ignoreMyParent):
            addrMap = self._extractAddressMap(converter, offset, addrModifier, sizeModifier)

        return addrMap


def regSpace_formatAsCDefines(bus, getMainSigFn, offset=0, prefix=""):
    addrSpace = AddressSpaceProbe(bus, getMainSigFn, offset=offset).discover()
    buff = []
    for addr, asi in sorted(addrSpace.items(), key=lambda x: x[0]):
        buff.append("#define %s 0x%x" % (prefix + asi.name.upper(), addr))

    return "\n".join(buff)
