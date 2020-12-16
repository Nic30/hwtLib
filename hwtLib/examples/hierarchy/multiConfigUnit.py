from copy import copy
from typing import List, Dict, Tuple, Union

from hdlConvertorAst.hdlAst import HdlIdDef, HdlValueId, HdlStmIf, \
    HdlStmBlock, HdlModuleDef, HdlCompInst
from hwt.code import And
from hwt.hdl.portItem import HdlPortItem
from hwt.hdl.types.defs import BIT, INT
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.value import HValue
from hwt.pyUtils.uniqList import UniqList
from hwt.serializer.mode import paramsToValTuple
from hwt.synthesizer.dummyPlatform import DummyPlatform
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from ipCorePackager.constants import INTF_DIRECTION, DIRECTION


def reduce_ternary(cond_val_pairs: List[Tuple[Union[HValue, RtlSignal], Union[HValue, RtlSignal]]], default: Union[HValue, RtlSignal]):
    """
    .. code-block:: python

        reduce_ternary([(c0, v0), (c1, v1)], v3)
        # to
        v0 if c0 else v1 if c1 else v3
    """
    res = default
    for cond, val in reversed(cond_val_pairs):
        res = cond._ternary(val, res)

    return res


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
            myIntf = copy(intf)
            myIntf._dtype = copy(myIntf._dtype)
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

    def _collectPortTypeVariants(self) -> List[Tuple[HdlPortItem, Dict[Tuple[Param, HValue], List[HdlType]]]]:
        res = []
        param_variants = [paramsToValTuple(u) for u in self._units]
        for parent_port, port_variants in zip(self._ctx.ent.ports, zip(*(u._ctx.ent.ports for u in self._units))):
            param_val_to_t = {}
            for port_variant, params in zip(port_variants, param_variants):
                assert port_variant.name == parent_port.name, (port_variant.name, parent_port.name)
                t = port_variant._dtype
                assert len(params) == len(self._params), (params, self._params)
                params = params._asdict()
                for p in self._params:
                    p_val = params[p.hdl_name]
                    types = param_val_to_t.setdefault((p, p_val), UniqList())
                    types.append(t)

            res.append((parent_port, param_val_to_t))

        return res

    def _injectParametersIntoPortTypes(self,
                                       port_type_variants: List[Tuple[HdlPortItem, Dict[Tuple[Param, HValue], List[HdlType]]]],
                                       param_signals: List[RtlSignal]):
        updated_type_ids = set()
        param_sig_by_name = {p.name: p for p in param_signals}
        param_value_domain = {}
        for parent_port, param_val_to_t in port_type_variants:
            for (param, param_value), port_types in param_val_to_t.items():
                param_value_domain.setdefault(param, set()).add(param_value)

        for parent_port, param_val_to_t in port_type_variants:
            if id(parent_port._dtype) in updated_type_ids:
                continue
            # check which unique parameter values affects the type of the port
            # if the type changes with any parameter value integrate it in to type of the port
            # print(parent_port, param_val_to_t)
            type_to_param_values = {}
            for (param, param_value), port_types in param_val_to_t.items():
                for pt in port_types:
                    cond = type_to_param_values.setdefault(pt, UniqList())
                    cond.append((param, param_value))

            assert type_to_param_values, parent_port
            if len(type_to_param_values) == 1:
                continue  # type does not change

            # Param: values
            params_used = {}
            for t, param_values in type_to_param_values.items():
                for (param, param_val) in param_values:
                    params_used.setdefault(param, set()).add(param_val)

                # filter out parameters which are not part of type specification process
                for p, p_vals in list(params_used.items()):
                    if len(param_value_domain[p]) == len(p_vals):
                        params_used.pop(p)
                # reset sets used to check parameter values
                for p, p_vals in params_used.items():
                    p_vals.clear()

            if not params_used:
                raise AssertionError(parent_port, "Type changes between the variants but it does not depend on parameter", param_val_to_t)

            if len(params_used) == 1 and list(params_used.keys())[0].get_hdl_type() == INT:
                # try to extract param * x + y
                p_val_to_port_w = {}
                for t, param_values in type_to_param_values.items():
                    for (param, param_val) in param_values:
                        if param not in params_used:
                            continue
                        assert param_val not in p_val_to_port_w or p_val_to_port_w[param_val] == t.bit_length(), parent_port
                        p_val_to_port_w[param_val] = t.bit_length()
                # t_width = n*p + c
                _p_val_to_port_w = sorted(p_val_to_port_w.items())
                t_width0, p0 = _p_val_to_port_w[0]
                t_width1, p1 = _p_val_to_port_w[1]
                # 0 == t_width0 - n*p0 + c
                # 0 == t_width1 - n*p1 + c

                # 0 == t_width0 - n*p0 - c + t_width1 - n*p1 - c
                # 0 == t_width0 + t_width1 - n*(p0 + p1) - 2c
                # c == (t_width0 + t_width1 - n*(p0 + p1) ) //2
                # n has to be int, 0 < n <= t_width0/p0
                # n is something like base size of port which is multipled by parameter
                # we searching n for which we can resolve c
                found_nc = None
                for n in range(1, t_width0 // p0 + 1):
                    c = (t_width0 + t_width1 - n * (p0 + p1)) // 2
                    if t_width0 - n * p0 + c == 0 and t_width1 - n * p1 + c == 0:
                        found_nc = (n, c)
                        break

                if found_nc is None:
                    raise NotImplementedError()
                else:
                    p = list(params_used.keys())[0]
                    p = param_sig_by_name[p._name]
                    (n, c) = found_nc
                    t = parent_port._dtype
                    t._bit_length = INT.from_py(n) * p + c
                    t._bit_length._const = True
                    updated_type_ids.add(id(t))
            else:
                condition_and_type_width = []
                default_width = None
                for t, p_vals in sorted(type_to_param_values.items(), key=lambda x: x[0].bit_length()):
                    cond = And(
                        *(param_sig_by_name[p.hdl_name]._eq(p_val)
                        for p, p_val in p_vals if p in params_used)
                    )
                    w = t.bit_length()
                    if default_width is None:
                        default_width = w
                    condition_and_type_width.append((cond, w))

                t = parent_port._dtype
                t._bit_length = reduce_ternary(condition_and_type_width, default_width)
                t._bit_length._const = True
                updated_type_ids.add(id(t))

    def create_HdlModuleDef(self,
                            target_platform: DummyPlatform,
                            store_manager: "StoreManager"):
        ctx = self._ctx
        mdef = HdlModuleDef()
        mdef.dec = ctx.ent
        mdef.module_name = HdlValueId(ctx.ent.name, obj=ctx.ent)
        mdef.name = "rtl"

        # constant signals which represents the param/generic values
        param_signals = [
            ctx.sig(p.hdl_name, p.get_hdl_type(), def_val=p.get_hdl_value())
            for p in sorted(self._params, key=lambda x: x.hdl_name)
        ]
        # rewrite ports to use generic/params of this entity/module
        port_type_variants = self._collectPortTypeVariants()
        self._injectParametersIntoPortTypes(port_type_variants, param_signals)
        for p in param_signals:
            p._const = True
            p.hidden = False
        # instanciate component variants in if generate statement
        ns = store_manager.name_scope
        as_hdl_ast = self._store_manager.as_hdl_ast
        if_generate_cases = []
        for u in self._units:
            # create instance
            ci = HdlCompInst()
            ci.origin = u
            ci.module_name = HdlValueId(u._ctx.ent.name, obj=u._ctx.ent)
            ci.name = HdlValueId(ns.checked_name(u._name + "_inst", ci), obj=u)
            e = u._ctx.ent

            ci.param_map.extend(e.params)
            # connect ports
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

            # create if generate instanciation condition
            param_cmp_expr = BIT.from_py(1)
            assert len(u._params) == len(param_signals)
            for p, p_sig in zip(sorted(u._params, key=lambda x: x.hdl_name), param_signals):
                assert p.hdl_name == p_sig.name, (p.hdl_name, p_sig.name)
                param_cmp_expr = param_cmp_expr & p_sig._eq(p.get_hdl_value())

            # add case if generate statement
            _param_cmp_expr = as_hdl_ast.as_hdl(param_cmp_expr)
            ci = as_hdl_ast.as_hdl_HdlCompInst(ci)
            b = HdlStmBlock()
            b.body.append(ci)
            b.in_preproc = True
            if_generate_cases.append((_param_cmp_expr, b))

        if_generate = HdlStmIf()
        if_generate.in_preproc = True
        if_generate.labels.append(ns.checked_name("implementation_select", if_generate))
        for c, ci in if_generate_cases:
            if if_generate.cond is None:
                if_generate.cond = c
                if_generate.if_true = ci
            else:
                if_generate.elifs.append((c, ci))

        mdef.objs.append(if_generate)
        for p in ctx.ent.ports:
            s = p.getInternSig()
            if p.direction != DIRECTION.IN:
                s.drivers.append(if_generate)
            else:
                s.endpoints.append(if_generate)

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

