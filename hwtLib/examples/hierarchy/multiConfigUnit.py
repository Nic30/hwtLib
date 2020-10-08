from typing import List

from hdlConvertorAst.hdlAst._defs import HdlIdDef
from hdlConvertorAst.hdlAst._expr import HdlValueId
from hdlConvertorAst.hdlAst._statements import HdlStmIf, HdlStmBlock
from hdlConvertorAst.hdlAst._structural import HdlModuleDef, HdlCompInst
from hwt.hdl.types.defs import BIT
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from ipCorePackager.constants import INTF_DIRECTION


class MultiConfigUnitWrapper(Unit):
    """
    Class which creates wrapper around multiple unit instances,
    the implementation is choosen based on generic/parameter values in HDL

    :attention: This is meant to be used for top component only, because it is useless
        for hwt design and it is usefull only for integration of statically build
        component in to VHDL/Verilog
    """

    def __init__(self, possible_variants: List[Unit]):
        assert possible_variants
        self._possible_variants = possible_variants
        super(MultiConfigUnitWrapper, self).__init__()

    def _copyParamsAndInterfaces(self):
        # note that the parameters are not added to HdlModuleDef (VHDL entity, Verilog module header)
        # as it was already build
        for p in self._possible_variants[0]._params:
            myP = Param(p.get_value())
            self._registerParameter(p._name, myP)
            myP.set_value(p.get_value())
            
        ns = self._store_manager.name_scope 
        for p in sorted(self._params, key=lambda x: x._name):
            hdl_val = p.get_hdl_value()
            v = HdlIdDef()
            v.origin = p
            v.name = p.hdl_name = ns.checked_name(p._name, p)
            v.type = hdl_val._dtype
            v.value = hdl_val
            self._ctx.ent.params.append(v)


        for intf in self.possible_variants[0]._interfaces:
            # clone interface
            myIntf = intf.__copy__()
            # sub-interfaces are not instantiated yet
            # myIntf._direction = intf._direction
            myIntf._direction = INTF_DIRECTION.opposite(intf._direction)

            self._registerInterface(intf._name, myIntf)
            object.__setattr__(self, intf._name, myIntf)


        ei = self._ctx.interfaces
        for i in self._interfaces:
            self._loadInterface(i, True)
            assert i._isExtern
            i._signalsForInterface(self._ctx, ei,
                                   self._store_manager.name_scope,
                                   reverse_dir=True)


    def _getDefaultName(self):
        return self._possible_variants[0]._getDefaultName()

    def _get_hdl_doc(self):
        return self._possible_variants[0]._get_hdl_doc()

    def _checkCompInstances(self):
        pass

    def create_HdlModuleDef(self,
                            target_platform: DummyPlatform,
                            store_manager: "StoreManager"):
        ctx = self._ctx
        mdef = HdlModuleDef()
        mdef.dec = ctx.ent
        mdef.module_name = HdlValueId(ctx.ent.name, obj=ctx.ent)
        mdef.name = "rtl"
        # mdef.objs.extend(processes)
        
        # constant signals which represents the param/generic values
        param_signals = [ctx.sig(p.hdl_name, p.get_hdl_type(), def_val=p.get_hdl_value()) for p in sorted(self._params, key=lambda x: x.hdl_name)]
        
        # instantiate subUnits in architecture
        ns = store_manager.name_scope
        as_hdl_ast = self._store_manager.as_hdl_ast
        if_generate_cases = []
        for u in self._units:
            ci = HdlCompInst()
            ci.origin = u
            ci.module_name = HdlValueId(u._ctx.ent.name, obj=u._ctx.ent)
            ci.name = HdlValueId(ns.checked_name(u._name + "_inst", ci), obj=u)
            e = u._ctx.ent

            ci.param_map.extend(e.params)
            assert len(e.ports) == len(ctx.ent.ports)
            for p, parent_port in zip(e.ports, ctx.ent.ports):
                i = p.getInternSig()
                parent_port_sig = parent_port.getInternSig()
                assert i.name == parent_port_sig.name
                o = p.getOuterSig()

                # can not connect directly to parent port because type is different
                # but need to connect to something with the same nme
                if o is p.src:
                    p.src = p.dst
                else:
                    assert o is p.dst, (o, p.dst)
                    p.dst = p.src

                ci.port_map.append(p)

            param_cmp_expr = BIT.from_py(1)
            assert len(u._params) == len(param_signals)
            for p, p_sig in zip(sorted(u._params, key=lambda x: x.hdl_name), param_signals):
                assert p.hdl_name == p_sig.name, (p.hdl_name, p_sig.name)
                param_cmp_expr = param_cmp_expr & p_sig._eq(p.get_hdl_value())
            _param_cmp_expr = as_hdl_ast.as_hdl(param_cmp_expr)
            ci = as_hdl_ast.as_hdl_HdlCompInst(ci)
            b = HdlStmBlock()
            b.body.append(ci)
            b.in_preproc = True
            if_generate_cases.append((_param_cmp_expr, b))

        if_generate = HdlStmIf()
        if_generate.in_preproc = True
        for c, ci in if_generate_cases:
            if if_generate.cond is None:
                if_generate.cond = c
                if_generate.if_true = ci
            else:
                if_generate.elifs.append((c, ci))
        if_generate.labels.append(ns.checked_name("implementation_select", if_generate))
        mdef.objs.append(if_generate)
        ctx.arch = mdef

        return mdef

    def _impl(self):
        assert self._parent is None, "should be used only for top instances"
        self._ctx.create_HdlModuleDef = self.create_HdlModuleDef
        self.possible_variants = HObjList(self._possible_variants)
        self._copyParamsAndInterfaces()


if __name__ == "__main__":
    from hwtLib.examples.simpleWithParam import SimpleUnitWithParam
    from hwt.synthesizer.utils import to_rtl_str
    u0 = SimpleUnitWithParam()
    u0.DATA_WIDTH = 2
    u1 = SimpleUnitWithParam()
    u1.DATA_WIDTH = 3
    
    u = MultiConfigUnitWrapper([u0, u1])
    print(to_rtl_str(u))

