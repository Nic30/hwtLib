#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import hBit, vec, vecT
from hwt.interfaces.std import Signal, Clk
from hwt.serializer.constants import SERI_MODE
from hwt.code import Concat, If
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


def mkLutRamCls(DATA_WIDTH):
	"""
	Lut ram generator
	hdl code will be excluded from serialization because we expect vendor library to contains it
	"""
	
	class RAMnX1S(Unit):
		_serializerMode = SERI_MODE.EXCLUDE
		
		def _config(self):
			self.INIT = Param(vec(0, DATA_WIDTH))
			self.IS_WCLK_INVERTED = Param(hBit(0))
	
		def _declr(self):
			self.a0 = Signal()
			self.a1 = Signal()
			self.a2 = Signal()
			self.a3 = Signal()
			self.a4 = Signal()
			self.a5 = Signal()
			self.d	 = Signal()  # in

			self.wclk = Clk()
			self.o = Signal()  # out
			self.we = Signal()
			
			
		def _impl(self):
			s = self._sig
			wclk_in = s("wclk_in")
			mem = self._cntx.sig("mem", vecT(DATA_WIDTH + 1),
								    defVal=hBit(None)._concat(self.INIT))
			a_in = s("a_in", vecT(6))
			d_in = s("d_in")
			we_in = s("we_in")
			
			wclk_in ** (self.wclk ^ self.IS_WCLK_INVERTED)
			we_in ** self.we
			a_in ** Concat(self.a5, self.a4, self.a3, self.a2, self.a1, self.a0)
			d_in ** self.d   
			
			# ReadBehavior
			self.o ** mem[a_in]
				
			# WriteBehavior
			If(wclk_in._onRisingEdge() & we_in,
			   mem[a_in] ** d_in
			) 

	RAMnX1S.__name__ = "RAM%dX1S" % DATA_WIDTH
	return RAMnX1S

RAM64X1S = mkLutRamCls(64)


if __name__ == "__main__":
	from hwt.synthesizer.shortcuts import toRtl
	print(toRtl(RAM64X1S))
