
from hdl_toolkit.serializer.formater import formatVhdl
from hdl_toolkit.synthetisator.rtlLevel.netlist import RtlNetlist
from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.synthetisator.codeOps import connect, If, Switch

w = connect


def complexConds():
    n = RtlNetlist("ComplexConds")
    stT = Enum('t_state', ["idle", "tsWait", "ts0Wait", "ts1Wait", "lenExtr"])
    clk = n.sig('clk')
    rst = n.sig("rst")
    
    st = n.sig('st', stT, clk=clk, syncRst=rst, defVal=stT.idle)
    s_idle = n.sig('s_idle')
    sd0 = n.sig('sd0')
    sd1 = n.sig('sd1')
    cntrlFifoVld = n.sig('ctrlFifoVld')
    cntrlFifoLast = n.sig('ctrlFifoLast')

    def tsWaitLogic(ifNoTsRd):
        return  If(sd0 & sd1,
                    w(stT.lenExtr, st)
                ).Elif(sd0,
                    w(stT.ts1Wait, st)
                ).Elif(sd1,
                    w(stT.ts0Wait, st)
                ).Else(
                    ifNoTsRd
                )
    Switch(st)\
    .Case(stT.idle,
            tsWaitLogic(
                If(cntrlFifoVld,
                   w(stT.tsWait, st)
                   ,
                   w(st, st)
                )
            )
    ).Case(stT.tsWait,
            tsWaitLogic(w(st, st))
    ).Case(stT.ts0Wait,
        If(sd0,
           w(stT.lenExtr, st)
        ).Else(
           w(st, st)
        )
    ).Case(stT.ts1Wait,
        If(sd1,
           w(stT.lenExtr, st)
        ).Else(
           w(st, st)
        )
    ).Case(stT.lenExtr,
        If(cntrlFifoVld & cntrlFifoLast,
           w(stT.idle, st)
        ).Else(
           w(st, st)
        )
    )
    w(st._eq(stT.idle), s_idle)
    
    return n, [sd0, sd1, cntrlFifoVld, cntrlFifoLast, s_idle]
    
if __name__ == "__main__":
    n, interf = complexConds()
    
    for o in n.synthetize(interf):
        print(formatVhdl(str(o)))
