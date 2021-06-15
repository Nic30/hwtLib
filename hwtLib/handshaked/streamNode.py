from typing import List, Optional, Tuple, Union

from hwt.code import And, Or
from hwt.hdl.statements.assignmentContainer import HdlAssignmentContainer
from hwt.hdl.types.defs import BIT
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


def _get_ready_signal(intf: Union[Interface, Tuple[RtlSignal, RtlSignal]]) -> RtlSignal:
    try:
        return intf.rd
    except AttributeError:
        pass

    if isinstance(intf, Tuple):
        _, rd = intf
        return rd

    return intf.ready


def _get_valid_signal(intf: Union[Interface, Tuple[RtlSignal, RtlSignal]]) -> RtlSignal:
    try:
        return intf.vld
    except AttributeError:
        pass

    if isinstance(intf, Tuple):
        vld, _ = intf
        return vld

    return intf.valid


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
        return Or(*map(_exStreamMemberAck, self))


class StreamNode():
    """
    Group of stream master and slave interfaces to synchronize them to each other

    :ivar ~.masters: interfaces which are inputs into this node
    :ivar ~.slaves: interfaces which are outputs of this node
    :ivar ~.extraConds: {dict interface : extraConditionSignal}
        where extra conditions will be added to expression for channel enable.
        For master it means it will obtain ready=1 only if extraConditionSignal
        is 1.
        For slave it means it will obtain valid=1 only
        if extraConditionSignal is 1.
        All interfaces have to wait on each other so if an extraCond!=1 it causes
        blocking on all interfaces if not overridden by skipWhen.
    :note: instead of interface it is possilble to use tuple (valid, ready) signal
    :ivar ~.skipWhen: dict interface : skipSignal
        where if skipSignal is high interface is disconnected from stream
        sync node and others does not have to wait on it
        (master does not need to have valid and slave ready)
    :attention: skipWhen has higher priority
    """

    def __init__(self, masters=None, slaves=None,
                 extraConds=None, skipWhen=None):
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

    def sync(self, enSig=None) -> List[HdlAssignmentContainer]:
        """
        Create synchronization logic between streams
        (generate valid/ready synchronization logic for interfaces)

        :param enSig: optional signal to enable this node
        :return: list of assignements which are responsible for synchronization of streams
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
                a = [_get_ready_signal(m)(r), ]

            expression.extend(a)

        for s in slaves:
            v = self.ackForSlave(s)

            if enSig is not None:
                v = v & enSig

            if isinstance(s, ExclusiveStreamGroups):
                a = s.sync(v)
            else:
                a = [_get_valid_signal(s)(v), ]

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

            if extra:
                a = And(a, *extra)

            if skip is not None:
                a = Or(a, skip)

            acks.append(a)

        if not acks:
            return True

        return And(*acks)

    def getExtraAndSkip(self, intf) -> Tuple[Optional[RtlSignal], Optional[RtlSignal]]:
        """
        :return: optional extraCond and skip flags for interface
        """
        try:
            extra = [self.extraConds[intf], ]
        except KeyError:
            extra = []

        try:
            skip = self.skipWhen[intf]
        except KeyError:
            skip = None

        return extra, skip

    def vld(self, intf: Union[Interface, Tuple[RtlSignal, RtlSignal]]) -> RtlSignal:
        """
        :return: valid signal of master interface for synchronization of othres
        """
        try:
            s = self.skipWhen[intf]
            assert s is not None
        except KeyError:
            s = None

        if isinstance(intf, ExclusiveStreamGroups):
            v = intf.ack()
        else:
            v = _get_valid_signal(intf)

        if s is None:
            return v
        else:
            return v | s

    def rd(self, intf: Union[Interface, Tuple[RtlSignal, RtlSignal]]) -> RtlSignal:
        """
        :return: ready signal of slave interface for synchronization of othres
        """
        try:
            s = self.skipWhen[intf]
            assert s is not None
        except KeyError:
            s = None

        if isinstance(intf, ExclusiveStreamGroups):
            r = intf.ack()
        else:
            r = _get_ready_signal(intf)

        if s is None:
            return r
        else:
            return r | s

    def ackForMaster(self, master: Interface) -> RtlSignal:
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

    def ackForSlave(self, slave: Interface) -> RtlSignal:
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
