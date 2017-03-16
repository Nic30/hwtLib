from hwt.code import And
from hwt.pyUtils.arrayQuery import where


def _getRd(intf):
    try:
        return intf.rd
    except AttributeError:
        pass
    return intf.ready


def _getVld(intf):
    try:
        return intf.vld
    except AttributeError:
        pass
    return intf.valid


def streamAck(masters=[], slaves=[]):
    """
    @param masters: interfaces which are inputs into this node
    @param slaves: interfaces which are outputs of this node

    returns expression which's value is high when transaction is made over interfaces
    """
    return And(*map(_getVld, masters), *map(_getRd, slaves))


def streamSync(masters=[], slaves=[], extraConds={}, skipWhen={}):
    """
    Synchronization of stream node
    generate valid/ready synchronization for interfaces

    @param masters: interfaces which are inputs into this node
    @param slaves: interfaces which are outputs of this node
    @param extraConds: dict interface : extraConditionSignal
              where extra conditions will be added to expression for channel enable
              for master it means it will get ready only when extraConditionSignal is 1
              for slave it means it will not get valid only when extraConditionSignal is 1
              but all interfaces have to wait on each other
    @param skipWhen: dict interface : skipSignal
              where if skipSignal is high interface is disconnected from stream sync node
              and others does not have to wait on it (master does not need to have valid and slave ready)
    @attention: skipWhen has higher priority
    """
    # also note that only slaves or only masters, means you are always generating/receiving
    # data from/to node
    assert masters or slaves
    for i in extraConds.keys():
        assert i in masters or i in slaves, i
    for i in skipWhen.keys():
        assert i in masters or i in slaves, i
    # this expression container is there to allow usage of this function
    # in usual hdl containers like If, Switch etc...
    expression = []

    def vld(intf):
        try: 
            s = skipWhen[intf]
            assert s is not None
        except KeyError:
            s = None
        
        v = _getVld(intf)
        if s is None:
            return v
        else:
            return v | s
        
    def rd(intf):
        try: 
            s = skipWhen[intf]
            assert s is not None
        except KeyError:
            s = None
        
        r = _getRd(intf)
        if s is None:
            return r
        else:
            return r | s      
    
    for m in masters:
        otherMasters = where(masters, lambda x: x is not m)
        try:
            extra = [extraConds[m], ]
        except KeyError:
            extra = []

        try:
            skip = skipWhen[m]
        except KeyError:
            skip = None

        r = And(*map(vld, otherMasters),
                *map(rd, slaves),
                *extra)
        if skip is not None:
            r = r & ~skip
            
        expression.extend(
            _getRd(m) ** r
        )
    for s in slaves:
        otherSlaves = where(slaves, lambda x: x is not s)
        try:
            extra = [extraConds[s], ]
        except KeyError:
            extra = []
            
        try:
            skip = skipWhen[s]
        except KeyError:
            skip = None
        
        v = And(*map(vld, masters),
                *map(rd, otherSlaves),
                *extra)
        
        if skip is not None:
            v = v & ~skip
        expression.extend(
            _getVld(s) ** v
        )

    return expression
