from hdl_toolkit.intfLvl import UnitFromHdl 

class EntityWithPartialyInvalidIntf(UnitFromHdl):
    _hdlSources = "vhdl/entityWithPartialyInvalidIntf.vhd"
    

if __name__ == "__main__":
    u = EntityWithPartialyInvalidIntf()
    u._loadDeclarations()
    print(u._entity)
    assert u.descrBM_w_wr_addr_V_123._parent == u
    assert u.descrBM_w_wr_din_V._parent == u
    assert u.descrBM_w_wr_dout_V._parent == u
    assert u.descrBM_w_wr_en._parent == u
    assert u.descrBM_w_wr_we._parent == u
    assert len(u._interfaces) == len(u._entity.ports)
    print(u.descrBM_w_wr_din_V._dtype)