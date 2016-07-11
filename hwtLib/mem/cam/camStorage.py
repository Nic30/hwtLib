from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.std import Ap_clk,Ap_rd, s
from hdl_toolkit.synthetisator.interfaceLevel.interface import Interface
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, vec
from hwtLib.mem.lutRam import RAM64X1S
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If

class CamStorageInIntf(Interface):
    def _config(self):
        self.COLUMNS = Param(1)
        self.ROWS = Param(1)
        
    def _declr(self):
        COLUMNS = self.COLUMNS
        self.data = s(dtype=vecT(COLUMNS*6))
        self.di   = s(dtype=vecT(COLUMNS))
        self.we   = s(dtype=vecT(self.ROWS))
       

con = connect
        
class CamStorage(Unit):
    """
    Cam storage mapped in lutRAMs
    """
    def _config(self):
        CamStorageInIntf._config(self)
    
    def _declr(self):
        self.clk = Ap_clk()
        self.dIn = CamStorageInIntf()
        self.match = Ap_rd()
        
        self.match._replaceParam("DATA_WIDTH", self.ROWS)
        self._mkIntfExtern()
        
        self.rams = []
        for c in range(evalParam(self.COLUMNS).val):
            # 7Series LUTM
            ram = RAM64X1S()
            ram.INIT.set(vec(0,64))
            self.rams.append(ram)
            setattr(self, "RAM64X1S_inst%d" % c, ram)
            

    def _impl(self):
        rows_t = vecT(self.ROWS)
        carry_t = vecT(self.COLUMNS+1)
        dIn = self.dIn
        #cam_storage_gen :
        for r in range(evalParam(self.ROWS).val):
            match_carry = self._sig("match_carry%d" % r, carry_t)
            #cam_storage_row_gen :
            for c in range(evalParam(self.COLUMNS).val):
                match_base = self._sig("match_base%d" % c, rows_t)
                ram = self.rams[c]
                base = c*6

                con(self.clk, ram.wclk)
                
                con(dIn.data[base+0], ram.a0)
                con(dIn.data[base+1], ram.a1)
                con(dIn.data[base+2], ram.a2)
                con(dIn.data[base+3], ram.a3)
                con(dIn.data[base+4], ram.a4)
                con(dIn.data[base+5], ram.a5)
                
                con(ram.o,     match_base[r])
                con(dIn.di[c],         ram.d)
                con(dIn.we[r],        ram.we)
                
                # Carry MUX
                nextCarry = match_carry[c+1]
                If(match_base[r],
                   con(match_carry[c], nextCarry)
                   ,
                   con(0, nextCarry)
                )
                
            con(self.match.rd,       match_carry[0])
            con(match_carry[self.COLUMNS], self.match.data[r])

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(CamStorage))
