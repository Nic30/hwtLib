from hdl_toolkit.synthesizer.codeOps import And
from python_toolkit.arrayQuery import where

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
    

def streamNodeSync(masters=[], slaves=[], extraConds={}):
    """
    @param masters: interfaces which are inputs into this node
    @param slaves: interfaces which are outputs of this node 
    @param extraConds: dict interface : [extraConditions]
              where extra conditions will be added to expression for channell enable
    generate valid/ready synchronization for interfaces
    """
    # also note that only slaves or only masters mean you are alwasy generating/receiving 
    # data from/to node 
    assert masters or slaves
    
    # this expression container is there to allow usage of this function
    # in usual hdl containers like If, Switch etc...
    expression = []
    
    for m in masters:
        otherMasters = where(masters, lambda x: x is not m)
        try:
            extra = extraConds[m]
        except KeyError:
            extra = []
        
        expression.extend(    
            _getRd(m) ** And(*map(_getVld, otherMasters), 
                             *map(_getRd, slaves),
                             *extra)
        )
    for s in slaves:
        otherSlaves = where(slaves, lambda x: x is not s)
        try:
            extra = extraConds[s]
        except KeyError:
            extra = []
        
        expression.extend(    
            _getVld(s) ** And(*map(_getVld, masters), 
                              *map(_getRd, otherSlaves),
                              *extra)
        )
    
    return expression