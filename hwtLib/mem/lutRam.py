from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.hdlObjects.typeShortcuts import hBit, vec, vecT
from hdl_toolkit.interfaces.std import Ap_none
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect, Concat
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If

c = connect

def mkLutRamCls(DATA_WIDTH):
	class RAMnX1S(Unit):
		def _config(self):
			self.INIT = Param(vec(0, DATA_WIDTH))
			self.IS_WCLK_INVERTED = Param(hBit(0))
	
		def _declr(self):
			self.o = Ap_none()
	
			self.a0 = Ap_none()
			self.a1 = Ap_none()
			self.a2 = Ap_none()
			self.a3 = Ap_none()
			self.a4 = Ap_none()
			self.a5 = Ap_none()
			self.d	 = Ap_none()
			self.wclk = Ap_none()
			self.we = Ap_none()
			
			self._mkIntfExtern()
			
		def _impl(self):
			s = self._sig
			wclk_in = s("wclk_in")
			mem = self._cntx.sig("mem", vecT(DATA_WIDTH+1),clk=wclk_in, defVal=hBit(None)._concat(self.INIT))
			a_in = s("a_in", vecT(6))
			d_in = s("d_in")
			we_in = s("we_in")
			
			c(self.wclk ^ self.IS_WCLK_INVERTED, wclk_in)
			c(self.we, 	we_in)
			c(Concat(self.a5, self.a4, self.a3, self.a2, self.a1, self.a0), a_in)
			c(self.d, d_in) 
			
			# ReadBehavior
			c(mem[a_in], self.o)
				
			# WriteBehavior 
			If(we_in,
			  c(d_in, mem[a_in])
			) 

	RAMnX1S.__name__  = "RAM%dX1S_gen" % DATA_WIDTH
	return RAMnX1S

RAM64X1S = mkLutRamCls(64)


if __name__ == "__main__":
	from hdl_toolkit.synthetisator.shortcuts import toRtl
	print(toRtl(RAM64X1S))
