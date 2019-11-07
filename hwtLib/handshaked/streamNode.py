from hwt.code import And, Or
from hwt.hdl.typeShortcuts import hBit
from hwt.pyUtils.arrayQuery import where


def _get_ready_signal(intf):
    try:
        return intf.rd
    except AttributeError:
        pass
    return intf.ready


def _get_valid_signal(intf):
    try:
        return intf.vld
    except AttributeError:
        pass
    return intf.valid


def _exStreamMemberAck(m):
    c, n = m
    return c & n.ack()


class ExclusiveStreamGroups(list):
    """
    list of tuples (cond, StreamNode instance)
    Only one stream from this group can be activated at the time
    """

    def __hash__(self):
        return id(self)

    def sync(self, enSig=None):
        """
        Create synchronization logic between streams
        (generate valid/ready synchronization logic for interfaces)

        :param enSig: optional signal to enable this group of nodes
        :return: list of assignements which are responsible for synchronization
            of streams
        """
        expression = []
        for cond, node in self:
            if enSig is not None:
                cond = cond & enSig
            expression.extend(node.sync(cond))
        return expression

    def ack(self):
        """
        :return: expression which's value is high when transaction can be made
            over at least on child streaming node
        """
        return Or(*map(_exStreamMemberAck, self))


class StreamNode():
    """
    Group of stream master and slave interfaces to synchronize them to each other

    :ivar masters: interfaces which are inputs into this node
    :ivar slaves: interfaces which are outputs of this node
    :ivar extraConds: dict interface : extraConditionSignal
        where extra conditions will be added to expression for channel enable
        for master it means it will get ready only when extraConditionSignal
        is 1 for slave it means it will not get valid only
        when extraConditionSignal is 1 but all interfaces have to wait
        on each other
    :ivar skipWhen: dict interface : skipSignal
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

    def sync(self, enSig=None):
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

    def ack(self):
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

    def getExtraAndSkip(self, intf):
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

    def vld(self, intf):
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

    def rd(self, intf):
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

    def ackForMaster(self, master):
        """
        :return: driver of ready signal for master
        """
        otherMasters = where(self.masters, lambda x: x is not master)
        extra, skip = self.getExtraAndSkip(master)

        conds = [*map(self.vld, otherMasters),
                 *map(self.rd, self.slaves),
                 *extra]
        if conds:
            r = And(*conds)
        else:
            r = hBit(1)

        if skip is not None:
            r = r & ~skip

        return r

    def ackForSlave(self, slave):
        """
        :return: driver of valid signal for slave
        """
        otherSlaves = where(self.slaves, lambda x: x is not slave)
        extra, skip = self.getExtraAndSkip(slave)

        conds = [*map(self.vld, self.masters),
                 *map(self.rd, otherSlaves),
                 *extra]
        if conds:
            v = And(*conds)
        else:
            v = hBit(1)

        if skip is not None:
            v = v & ~skip

        return v
