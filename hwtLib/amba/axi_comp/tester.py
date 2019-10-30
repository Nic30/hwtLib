from hwt.code import FsmBuilder, If, connect, Concat
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi3Lite import Axi3Lite
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint


SEND_AW, SEND_W, RECV_B, SEND_AR, RECV_R = range(1, 6)


class AxiTester(Unit):
    """
    Tester for AXI3/4 interfaces

    Can precisely control order and timing
    of read address/write address/read/write/write response transactions
    Allows to read and specify values of controls signals like cache/lock/burst
    etc...

    .. hwt-schematic::
    """

    def __init__(self, axiCls=Axi4, cntrlCls=Axi4Lite):
        self._axiCls = axiCls
        self._cntrlCls = cntrlCls
        super(AxiTester, self).__init__()

    def _config(self):
        self._axiCls._config(self)
        self.CNTRL_DATA_WIDTH = Param(32)
        self.CNTRL_ADDR_WIDTH = Param(32)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.m_axi = self._axiCls()._m()
        with self._paramsShared(prefix="CNTRL_"):
            self.cntrl = self._cntrlCls()
            self._add_ep()

        # r = self.ram = Ram_dp()
        # r.ADDR_WIDTH = log2ceil(4096)
        # r.DATA_WIDTH = self.DATA_WIDTH

    def _add_ep(self):
        strb_w = self.DATA_WIDTH // 8
        # [TODO] hotfix, should be self.DATA_WIDTH
        DATA_FIELD_W = self.CNTRL_DATA_WIDTH
        LEN_WIDTH = self.m_axi.LEN_WIDTH
        LOCK_WIDTH = self.m_axi.LOCK_WIDTH

        mem_space = HStruct(
            (Bits(32), "id_reg"), # 0x00
            (Bits(32), "cmd_and_status"),
            (Bits(self.ADDR_WIDTH), "addr"),
            # a or w id
            (Bits(self.ID_WIDTH), "ar_aw_w_id"),
            (Bits(32 - int(self.ID_WIDTH)), None), 

            (Bits(2), "burst"), # 0x10
            (Bits(32 - 2), None),
            (Bits(4), "cache"),
            (Bits(32 - 4), None),
            (Bits(LEN_WIDTH), "len"),
            (Bits(32 - LEN_WIDTH), None),
            (Bits(LOCK_WIDTH), "lock"),
            (Bits(32 - LOCK_WIDTH), None),
            (Bits(3), "prot"), # 0x20
            (Bits(32 - 3), None),
            (Bits(3), "size"),
            (Bits(32 - 3), None),
            (Bits(4), "qos"),
            (Bits(32 - 4), None),

            (Bits(self.ID_WIDTH), "r_id"),
            (Bits(32 - int(self.ID_WIDTH)), None),
            (Bits(DATA_FIELD_W), "r_data"), # 0x30
            (Bits(2), "r_resp"),
            (Bits(32 - 2), None),
            (BIT, "r_last"),
            (Bits(32 - 1), None),

            (Bits(self.ID_WIDTH), "b_id"),
            (Bits(32 - int(self.ID_WIDTH)), None),
            (Bits(2), "b_resp"), # 0x40
            (Bits(32 - 2), None),

            (Bits(DATA_FIELD_W), "w_data"),
            (BIT, "w_last"),
            (Bits(32 - 1), None),
            (Bits(strb_w), "w_strb"),
            (Bits(32 - int(strb_w)), None),
            # 0x50
            (Bits(5*2), "hs"),
            (Bits(5*2 - 1), None),
        )

        ep = self.axi_ep = AxiLiteEndpoint(mem_space, intfCls=self._cntrlCls)
        ep.DATA_WIDTH = self.CNTRL_DATA_WIDTH
        ep.ADDR_WIDTH = self.CNTRL_ADDR_WIDTH

    def _impl(self):
        propagateClkRstn(self)
        self.axi_ep.bus(self.cntrl)

        ep = self.axi_ep.decoded
        id_reg_val = int.from_bytes("test".encode(), byteorder="little")
        ep.id_reg.din(id_reg_val)

        def connected_reg(name, input_=None, inputEn=None, fit=False):
            if input_ is not None:
                assert inputEn is not None

            port = getattr(ep, name)
            reg = self._reg(name, port.din._dtype)
            e = If(port.dout.vld,
                   connect(port.dout.data, reg, fit=fit)
                )
            if input_ is not None:
                e.Elif(inputEn,
                    connect(input_, reg, fit=fit)
                )
            port.din(reg)
            return reg

        cmdIn = ep.cmd_and_status.dout
        cmd = self._reg("reg_cmd", cmdIn.data._dtype, def_val=0)
        cmdVld = self._reg("reg_cmd_vld", def_val=0)
        If(cmdIn.vld,
           connect(cmdIn.data, cmd, fit=True)
        )
        partDone = self._sig("partDone")
        If(partDone,
           cmdVld(0)
        ).Elif(cmdIn.vld,
           cmdVld(1)
        )

        def cmd_en(cmd_code):
            return cmdVld & cmd._eq(cmd_code)

        state_t = HEnum("state_t",
                        ["ready", "wait_ar", "wait_aw",
                         "wait_w", "wait_b", "wait_r"])

        axi = self.m_axi
        st = FsmBuilder(self, state_t)\
            .Trans(state_t.ready,
                   (cmd_en(SEND_AW), state_t.wait_aw),
                   (cmd_en(SEND_AR), state_t.wait_ar),
                   (cmd_en(SEND_W), state_t.wait_w),
                   (cmd_en(RECV_R), state_t.wait_r),
                   (cmd_en(RECV_B), state_t.wait_b),
            ).Trans(state_t.wait_aw,
                (axi.aw.ready, state_t.ready)
            ).Trans(state_t.wait_ar,
                (axi.ar.ready, state_t.ready)
            ).Trans(state_t.wait_w,
                (axi.w.ready, state_t.ready)
            ).Trans(state_t.wait_r,
                (axi.r.valid, state_t.ready)
            ).Trans(state_t.wait_b,
                (axi.b.valid, state_t.ready)
            ).stateReg

        partDone((st._eq(state_t.wait_aw) & axi.aw.ready) |
                 (st._eq(state_t.wait_ar) & axi.ar.ready) |
                 (st._eq(state_t.wait_w) & axi.w.ready) |
                 (st._eq(state_t.wait_r) & axi.r.valid) |
                 (st._eq(state_t.wait_b) & axi.b.valid))

        ready = st._eq(state_t.ready)
        tmp = self._sig("tmp")
        tmp(ready & ~ep.cmd_and_status.dout.vld)
        connect(tmp, ep.cmd_and_status.din, fit=True)

        a_w_id = connected_reg("ar_aw_w_id")
        addr = connected_reg("addr")
        burst = connected_reg("burst")
        cache = connected_reg("cache")
        len_ = connected_reg("len")
        lock = connected_reg("lock")
        prot = connected_reg("prot")
        size = connected_reg("size")
        qos = connected_reg("qos")

        # aw/ar
        for p in [axi.aw, axi.ar]:
            p.id(a_w_id)
            p.addr(addr)
            p.burst(burst)
            p.cache(cache)
            p.len(len_)
            p.lock(lock)
            p.prot(prot)
            p.size(size)
            if hasattr(p, "qos"):
                p.qos(qos)

        aw_vld = st._eq(state_t.wait_aw)
        axi.aw.valid(aw_vld)
        ar_vld = st._eq(state_t.wait_ar)._reinterpret_cast(BIT)
        axi.ar.valid(ar_vld)

        r = axi.r
        r_rd = st._eq(state_t.wait_r)
        r_en = r.valid & r_rd
        connected_reg("r_id", r.id, r_en)
        connected_reg("r_data", r.data, r_en, fit=True)
        connected_reg("r_resp", r.resp, r_en)
        connected_reg("r_last", r.last, r_en)
        r.ready(r_rd)

        w = axi.w
        w_data = connected_reg("w_data", fit=True)
        w_last = connected_reg("w_last")
        w_strb = connected_reg("w_strb")
        if hasattr(w, "id"):
            w.id(a_w_id)
        connect(w_data, w.data, fit=True)
        w.strb(w_strb)
        w.last(w_last)
        w_vld = st._eq(state_t.wait_w)
        w.valid(w_vld)

        b = axi.b
        b_rd = st._eq(state_t.wait_b)
        connected_reg("b_id", b.id, b.valid & b_rd)
        connected_reg("b_resp")
        b.ready(b_rd)

        ep.hs.din(Concat(ar_vld, axi.ar.ready,
                         aw_vld, axi.aw.ready,
                         r.valid, r_rd,
                         b.valid, b_rd,
                         w_vld, w.ready))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    #from hwt.serializer.ip_packager import IpPackager
    #from os.path import expanduser

    u = AxiTester(Axi3)
    print(toRtl(u))
    #p = IpPackager(u)
    #p.createPackage(expanduser("~"))

