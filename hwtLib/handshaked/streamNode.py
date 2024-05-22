from typing import List, Optional, Tuple, Union, Dict

from hwt.code import And, Or
from hwt.constants import NOT_SPECIFIED
from hwt.hdl.const import HConst
from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.types.defs import BIT
from hwt.hwIO import HwIO
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


ValidReadyTuple = Tuple[Union[RtlSignal, int], Union[RtlSignal, int]]
HwIOOrValidReadyTuple = Union[HwIO, ValidReadyTuple]


def _get_ready_signal(hwIO: HwIOOrValidReadyTuple) -> RtlSignal:
    try:
        return hwIO.rd
    except AttributeError:
        pass

    if isinstance(hwIO, Tuple):
        _, rd = hwIO
        return rd

    return hwIO.ready


def _get_valid_signal(hwIO: HwIOOrValidReadyTuple) -> RtlSignal:
    try:
        return hwIO.vld
    except AttributeError:
        pass

    if isinstance(hwIO, Tuple):
        vld, _ = hwIO
        return vld

    return hwIO.valid


def _exStreamMemberAck(m) -> RtlSignal:
    c, n = m
    return c & n.ack()


class ExclusiveStreamGroups(list):
    """
    list of tuples (cond, StreamNode instance)
    Only one stream from this group can be activated at the time
    """

    def __hash__(self):
        return id(self)

    def sync(self, enSig=None) -> List[HdlAssignmentContainer]:
        """
        Create synchronization logic between streams
        (generate valid/ready synchronization logic for interfaces)

        :param enSig: optional signal to enable this group of nodes
        :return: list of assignments which are responsible for synchronization
            of streams
        """
        expression = []
        for cond, node in self:
            if enSig is not None:
                cond = cond & enSig
            expression.extend(node.sync(cond))
        return expression

    def ack(self) -> RtlSignal:
        """
        :return: expression which's value is high when transaction can be made
            over at least on child streaming node
        """
        return Or(*(_exStreamMemberAck(m) for m in self))


class StreamNode():
    """
    Group of stream master and slave interfaces to synchronize them to each other

    :ivar ~.masters: list of unique interfaces which are inputs into this node
    :ivar ~.slaves: list of unique interfaces which are outputs of this node
    :note: instead of interface it is possible to use tuple (valid, ready) signal,
        this tuple can also be (1, 1) but can only in masters or only in slaves
    :ivar ~.extraConds: dict {interface : extraConditionSignal}
        where extra conditions will be added to expression for channel enable.
        For master it means it will obtain ready=1 only if extraConditionSignal
        is 1.
        For slave it means it will obtain valid=1 only
        if extraConditionSignal is 1.
        All interfaces have to wait on each other so if an extraCond!=1 it causes
        blocking on all interfaces if not overridden by skipWhen.
    :ivar ~.skipWhen: dict {interface : skipSignal}
        where if skipSignal is high, the interface is disconnected from stream
        sync node and others does not have to wait for it
        (master does not need to have valid and slave ready)
    :attention: skipWhen has higher priority than extraCond
    """

    def __init__(self,
                 masters: Optional[List[HwIOOrValidReadyTuple]]=None,
                 slaves: Optional[List[HwIOOrValidReadyTuple]]=None,
                 extraConds: Optional[Dict[HwIOOrValidReadyTuple, RtlSignal]]=None,
                 skipWhen: Optional[Dict[HwIOOrValidReadyTuple, RtlSignal]]=None):
        if masters is None:
            masters = []
        if slaves is None:
            slaves = []
        if extraConds is None:
            extraConds = {}
        if skipWhen is None:
            skipWhen = {}

        self.masters = masters
        self.slaves = slaves
        self.extraConds = extraConds
        self.skipWhen = skipWhen

    def sync(self, enSig: Optional[RtlSignal]=None) -> List[HdlAssignmentContainer]:
        """
        Create synchronization logic between streams
        (generate valid/ready synchronization logic for interfaces)

        :param enSig: optional signal to enable this node
        :return: list of assignments which are responsible for synchronization of streams
        """
        masters = self.masters
        slaves = self.slaves

        if not masters and not slaves:
            # node is empty
            assert not self.extraConds
            assert not self.skipWhen
            return []

        # check if there is not not any mess in extraConds/skipWhen
        for i in self.extraConds.keys():
            assert i in masters or i in slaves, i

        for i in self.skipWhen.keys():
            assert i in masters or i in slaves, i

        # this expression container is there to allow usage of this function
        # in usual hdl containers like If, Switch etc...
        expression = []
        for m in masters:
            r = self.ackForMaster(m)
            if enSig is not None:
                r = r & enSig

            if isinstance(m, ExclusiveStreamGroups):
                a = m.sync(r)
            else:
                rd = _get_ready_signal(m)
                if isinstance(rd, int):
                    assert rd == 1
                    continue
                else:
                    a = [rd(r), ]

            expression.extend(a)

        for s in slaves:
            v = self.ackForSlave(s)

            if enSig is not None:
                v = v & enSig

            if isinstance(s, ExclusiveStreamGroups):
                a = s.sync(v)
            else:
                vld = _get_valid_signal(s)
                if isinstance(vld, int):
                    assert vld == 1
                    continue
                else:
                    a = [vld(v), ]

            expression.extend(a)

        return expression

    def ack(self) -> RtlSignal:
        """
        :return: expression which's value is high when transaction can be made over interfaces
        """
        # every interface has to have skip flag or it has to be ready/valid
        # and extraCond has to be True if present
        acks = []
        for m in self.masters:
            extra, skip = self.getExtraAndSkip(m)
            if isinstance(m, ExclusiveStreamGroups):
                a = m.ack()
            else:
                a = _get_valid_signal(m)

            if isinstance(a, (int, HConst)):
                assert int(a) == 1, (m, a)
                continue
            else:
                if extra:
                    a = And(a, *extra)

                if skip is not None:
                    a = Or(a, skip)

            acks.append(a)

        for s in self.slaves:
            extra, skip = self.getExtraAndSkip(s)
            if isinstance(s, ExclusiveStreamGroups):
                a = s.ack()
            else:
                a = _get_ready_signal(s)

            if isinstance(a, (int, HConst)):
                assert int(a) == 1, (s, a)
                continue
            else:
                if extra:
                    a = And(a, *extra)

                if skip is not None:
                    a = Or(a, skip)

            acks.append(a)

        if acks:
            return And(*acks)
        else:
            return True

    def getExtraAndSkip(self, hwIO: HwIOOrValidReadyTuple) -> Tuple[Optional[RtlSignal], Optional[RtlSignal]]:
        """
        :return: optional extraCond and skip flags for interface
        """
        try:
            extra = [self.extraConds[hwIO], ]
        except KeyError:
            extra = []

        try:
            skip = self.skipWhen[hwIO]
        except KeyError:
            skip = None

        return extra, skip

    def vld(self, hwIO: HwIOOrValidReadyTuple) -> RtlSignal:
        """
        :return: valid signal of master interface for synchronization of othres
        """
        try:
            s = self.skipWhen[hwIO]
            assert s is not None
        except KeyError:
            s = None

        if isinstance(hwIO, ExclusiveStreamGroups):
            v = hwIO.ack()
        else:
            v = _get_valid_signal(hwIO)

        if isinstance(v, int):
            assert v == 1, v
            return BIT.from_py(1)

        if s is None:
            return v
        else:
            return v | s

    def rd(self, hwIO: HwIOOrValidReadyTuple) -> RtlSignal:
        """
        :return: ready signal of slave interface for synchronization of othres
        """
        try:
            s = self.skipWhen[hwIO]
            assert s is not None
        except KeyError:
            s = None

        if isinstance(hwIO, ExclusiveStreamGroups):
            r = hwIO.ack()
        else:
            r = _get_ready_signal(hwIO)

        if isinstance(r, int):
            assert r == 1, r
            return BIT.from_py(1)

        if s is None:
            return r
        else:
            return r | s

    def ackForMaster(self, master: HwIOOrValidReadyTuple) -> RtlSignal:
        """
        :return: driver of ready signal for master
        """
        extra, skip = self.getExtraAndSkip(master)

        rd = self.rd
        vld = self.vld
        conds = [*(vld(m) for m in self.masters if m is not master),
                 *(rd(s) for s in self.slaves),
                 *extra]
        if conds:
            r = And(*conds)
        else:
            r = BIT.from_py(1)

        if skip is not None:
            r = r & ~skip

        return r

    def ackForSlave(self, slave: HwIOOrValidReadyTuple) -> RtlSignal:
        """
        :return: driver of valid signal for slave
        """
        extra, skip = self.getExtraAndSkip(slave)

        rd = self.rd
        vld = self.vld
        conds = [*(vld(m) for m in self.masters),
                 *(rd(s) for s in self.slaves if s is not slave),
                 *extra]
        if conds:
            v = And(*conds)
        else:
            v = BIT.from_py(1)

        if skip is not None:
            v = v & ~skip

        return v

    def __repr__format_HwIO_list(self, hwIO_list):
        res = []
        for i in hwIO_list:
            extraCond = self.extraConds.get(i, NOT_SPECIFIED)
            skipWhen = self.skipWhen.get(i, NOT_SPECIFIED)
            if extraCond is not NOT_SPECIFIED and skipWhen is not NOT_SPECIFIED:
                res.append(f"({i},\n            extraCond={extraCond},\n            skipWhen={skipWhen})")
            elif extraCond is not NOT_SPECIFIED:
                res.append(f"({i},\n            extraCond={extraCond})")
            elif skipWhen is not NOT_SPECIFIED:
                res.append(f"({i},\n            skipWhen={skipWhen})")
            else:
                res.append(f"{i}")

        return ',\n        '.join(res)

    def __repr__(self):
        masters = self.__repr__format_HwIO_list(self.masters)
        slaves = self.__repr__format_HwIO_list(self.slaves)
        return f"""<{self.__class__.__name__}
    masters=[
        {masters:s}],
    slaves=[
        {slaves:s}],
>"""

