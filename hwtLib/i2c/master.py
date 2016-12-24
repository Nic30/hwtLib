#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.code import If, Concat
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.i2c.masterBitCntrl import I2cMasterBitCtrl
from hwtLib.interfaces.peripheral import I2c


class I2cMaster(Unit):
    """
    [TODO] not finished
    """
    def _config(self):
        self.CLK_FREQ = Param(int(100e6))
        self.I2C_FREQ = Param(int(400e3))
        
    def _declr(self):
        addClkRstn(self)
        
        self.start = Signal() # send start on i2c bus, can be used with read or write
        self.stop = Signal() # send stop to i2c bus
        self.read = Signal() 
        self.write = Signal()
        
        self.ack_in = Signal()  # i2c ack bit
        self.din = Signal(dtype=vecT(8))
        
        self.ack_out = Signal()  # i2c ack bit
        self.dout = Signal(dtype=vecT(8))
        
        
        self.i2c = I2c()
        
        self.bitCntrl = I2cMasterBitCtrl()
        
    def _impl(self):
        propagateClkRstn(self)
        
        cntrl = self.bitCntrl
        self.i2c ** cntrl.i2c
        
        shiftReg_index = self._reg("shiftReg_index", vecT(3, False), defVal=0)
        shiftReg = self._reg("shiftReg", vecT(8), defVal=0)
        
        If(ld,
           shiftReg ** self.din,
           shiftReg_index ** 7
        ).Elif(doShift,
           shiftReg ** Concat(shiftReg[7:], cntrl.dout),
           shiftReg_index ** (shiftReg_index - 1)
        )
        
        shiftDone = shiftReg_index._eq(0)

        stT = Enum("st_t", ["idle", "start", "read", "write", "ack"])


