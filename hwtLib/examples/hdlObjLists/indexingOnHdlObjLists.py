from typing import Union

from hwt.code import Switch
from hwt.interfaces.std import VectSignal, Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit


def _create_intermediate_signals(parent_u: Unit, res_t: Union[RtlSignal, Interface, HObjList]):
    if isinstance(res_t, HObjList):
        res = HObjList(_create_intermediate_signals(parent_u, res_t[0]) for _ in range(len(res_t)))
        parent_u._registerArray("indexing_", res)
    elif isinstance(res_t, Interface):
        res = res_t.__copy__()
        parent_u._registerIntfInImpl("indexing_", res)
    else:
        res = parent_u._ctx.parent._sig("indexing_", res_t._dtype)

    return res


def HdlObjList_index_read(hlist: HObjList, index: Union[RtlSignal, Interface]):
    if isinstance(index, RtlSignal):
        parent_u = index.ctx.parent
    else:
        parent_u = index._parent
        while not isinstance(u, Unit):
            parent_u = parent_u._parent

    res = _create_intermediate_signals(parent_u, hlist[0])
    Switch(index)\
        .add_cases(
            (i, res(hlist[i])) for i in range(2 ** index._dtype.bit_length())
        )
    return res


class UseSignalToIndexOnHdlObjList0(Unit):

    def _declr(self):
        addClkRstn(self)
        self.i = VectSignal(2)
        self.d = HObjList(VectSignal(8) for _ in range(4))
        self.d_out = VectSignal(8)._m()

    def _impl(self):
        self.d_out(HdlObjList_index_read(self.d, self.i))


class UseSignalToIndexOnHdlObjList1(UseSignalToIndexOnHdlObjList0):

    def _impl(self):
        self.d_out(HdlObjList_index_read(self.d, self.i) + 1)


class UseSignalToIndexOnHdlObjList2(UseSignalToIndexOnHdlObjList0):

    def _impl(self):
        tmp = self._sig("tmp")
        tmp(HdlObjList_index_read(self.d, self.i))
        self.d_out(tmp)


class UseSignalToIndexOnHdlObjList3(UseSignalToIndexOnHdlObjList0):

    def _declr(self):
        addClkRstn(self)
        self.i = VectSignal(2)
        self.d = HObjList(Handshaked() for _ in range(4))
        self.d_out = Handshaked()._m()

    def _impl(self):
        self.d_out(HdlObjList_index_read(self.d, self.i))


class UseSignalToIndexOnHdlObjList4(UseSignalToIndexOnHdlObjList0):

    def _declr(self):
        addClkRstn(self)
        self.i0 = VectSignal(2)
        self.i1 = VectSignal(2)
        self.d = HObjList(HObjList(Handshaked() for _ in range(4)) for _ in range(4))
        self.d_out = Handshaked()._m()

    def _impl(self):
        self.d_out(HdlObjList_index_read(HdlObjList_index_read(self.d, self.i0), self.i1))


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = UseSignalToIndexOnHdlObjList4()
    print(to_rtl_str(u))
