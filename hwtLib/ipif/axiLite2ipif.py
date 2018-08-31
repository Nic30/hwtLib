from hwt.synthesizer.unit import Unit
from hwtLib.ipif.intf import Ipif
from hwtLib.amba.axi4Lite import Axi4Lite
from hwt.code import Switch, If, FsmBuilder, In
from hwtLib.amba.constants import RESP_SLVERR, RESP_OKAY
from hwt.interfaces.utils import addClkRstn
from hwt.hdl.types.enum import HEnum


class AxiLite2Ipif(Unit):

    def _config(self) -> None:
        Ipif._config(self)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = Axi4Lite()
            self.m = Ipif()._m()

    def handleResp(self):
        ipif = self.m
        axi = self.s
        resp = self._sig("resp", axi.r.resp._dtype)
        If(ipif.ip2bus_error,
           resp(RESP_SLVERR)
        ).Else(
           resp(RESP_OKAY)
        )
        axi.r.resp(resp)
        axi.b.resp(resp)

    def handleAddr(self, st):
        st_t = st._dtype
        ipif = self.m
        axi = self.s

        addr = self._reg("addr", axi.aw.addr._dtype)
        If(st._eq(st_t.idle),
            If(axi.ar.valid,
                addr(axi.ar.addr)
            ).Elif(axi.aw.valid,
                addr(axi.aw.addr)
            )
        )
        ipif.bus2ip_addr(addr)

    def _impl(self) -> None:
        ipif = self.m
        axi = self.s
        st_t = HEnum("st_t", ["idle",
                              "write", "write_wait_data", "write_ack",
                              "read", "read_ack"
                              ])

        st = FsmBuilder(self, st_t
        ).Trans(st_t.idle,
                # ready for new request
                (axi.ar.valid, st_t.read),
                (axi.aw.valid, st_t.write_wait_data),
        ).Trans(st_t.write_wait_data,
                # has address but needs data from axi
                (axi.w.valid, st_t.write),
        ).Trans(st_t.write,
                # has address and data from axi and writing to ipif
                (ipif.ip2bus_wrack & axi.b.ready, st_t.idle),
                (ipif.ip2bus_wrack, st_t.write_ack),
        ).Trans(st_t.write_ack,
                # data was writen waiting for write response to axi,
                (axi.b.ready, st_t.idle)
        ).Trans(st_t.read,
                # has address, reading from ipif
                (ipif.ip2bus_rdack & axi.r.ready, st_t.idle),
                (ipif.ip2bus_rdack, st_t.read_ack),
        ).Trans(st_t.read_ack,
                # read from ipif complete, waiting for axi to accept data
                (axi.r.ready, st_t.idle)
        ).stateReg

        self.handleResp()
        self.handleAddr(st)

        idle = st._eq(st_t.idle)
        axi.aw.ready(idle)
        axi.ar.ready(idle)
        axi.w.ready(st._eq(st_t.write_wait_data))

        dataReg = self._reg("data", axi.w.data._dtype)
        strbReg = self._reg("strb", axi.w.strb._dtype)

        If(((st._eq(st_t.idle) & axi.aw.valid) | st._eq(st_t.write_wait_data)) & axi.w.valid,
            dataReg(axi.w.data),
            strbReg(axi.w.strb)
        ).Elif(ipif.ip2bus_rdack,
            dataReg(ipif.ip2bus_data),
        )
        If(idle,
           ipif.bus2ip_be(axi.w.strb)
        ).Else(
           ipif.bus2ip_be(strbReg)
        )

        Switch(st)\
        .Case(st_t.read,
              axi.r.data(ipif.ip2bus_data),
              axi.r.valid(ipif.ip2bus_rdack))\
        .Case(st_t.read_ack,
              axi.r.data(dataReg),
              axi.r.valid(1),
        ).Default(
            axi.r.data(None),
            axi.r.valid(0)
        )

        Switch(st)\
        .Case(st_t.write,
            axi.b.valid(ipif.ip2bus_wrack)
        ).Case(st_t.write_ack,
            axi.b.valid(1)
        ).Default(
            axi.b.valid(0)
        )

        ipif.bus2ip_data(dataReg)
        ipif.bus2ip_cs(st._eq(st_t.write) | st._eq(st_t.read))
        ipif.bus2ip_rnw(st._eq(st_t.read))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiLite2Ipif()
    print(toRtl(u))
   