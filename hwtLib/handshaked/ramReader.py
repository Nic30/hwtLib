#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import BramPort_withoutClk, Handshaked, \
    HandshakeSync
from hwt.interfaces.utils import addClkRstn
from hwt.code import Switch, If, FsmBuilder
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param


class HsRamPortReader(Unit):
    """
    Read data from BramPort and send them over handsaked interface
    """
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(32)
        
        self.ADDR_LOW = Param(0)
        self.SIZE = Param(255)
    
    def _declr(self):
        addClkRstn(self)
        # start reading data over dataOut
        self.en = HandshakeSync()
        
        # delete active memoryset
        self.clean = HandshakeSync()
        
        with self._paramsShared():
            self.dataIn = BramPort_withoutClk()
            self.dataOut = Handshaked() 
    
    def fsm(self, data_flag, data_inReg, addr):
        st_t = Enum("st_t", ["idle", "sendingData", "inCleaning"])
        Out = self.dataOut
        
        ADDR_HIGH = self.ADDR_LOW + self.SIZE - 1
        lastAddr = addr._eq(ADDR_HIGH)

        return FsmBuilder(self, st_t)\
        .Trans(st_t.idle,
            (self.en.vld, st_t.sendingData),
            (self.clean.vld, st_t.inCleaning)
        ).Trans(st_t.sendingData,
            # if some data is loaded and it can not be send out
            # stage is same
            # if is possible to send data in this clk
            (~(data_inReg | (data_flag & ~Out.rd)) & lastAddr, st_t.idle)
        ).Trans(st_t.inCleaning,
            (lastAddr, st_t.idle)
        ).stateReg
                
    def _impl(self):
        In = self.dataIn
        Out = self.dataOut

        addr = self.addr = self._reg("addr_reg", In.addr._dtype)
        data_reg = self.data_reg = self._reg("data_reg", In.dout._dtype)
        data_flag = self.data_flag = self._reg("data_flag_reg", defVal=0)
        data_inReg = self.data_inReg = self._reg("data_inReg_flag_reg", defVal=0)
        
        
        self.st = st = self.fsm(data_flag, data_inReg, addr)
        st_t = st._dtype
        
        self.en.rd ** st._eq(st_t.idle)
        self.clean.rd ** st._eq(st_t.idle) 
        
        Out.vld ** (data_inReg | data_flag)
        
        In.din ** 0
        In.en ** 1
        In.we ** st._eq(st_t.inCleaning)
        In.addr ** addr

        
        If(data_flag,
           data_reg ** In.dout
        )
        
        If(data_inReg,
           Out.data ** data_reg
        ).Else(
           Out.data ** In.dout
        )
        
        # addr incrementig logic
        Switch(st)\
        .Case(st_t.idle,
            addr ** self.ADDR_LOW
        ).Case(st_t.sendingData,
            If(~(data_inReg | (data_flag & ~Out.rd)),
                # if is possible to send data in this clk
                addr ** (addr + 1)
            )
        ).Case(st_t.inCleaning,
            addr ** (addr + 1)
        )
        
        # dataRegs logic
        If(st._eq(st_t.sendingData),
            data_flag ** 1,
            If(data_inReg | (data_flag & ~Out.rd),
                # if some data is loaded and it can not be send out
                If(data_inReg,
                   data_inReg ** ~Out.rd
                )
            ).Else(
                # if is possible to send data in this clk
                data_inReg ** ~self.dataOut.rd
            )
        ).Else(
            data_flag ** 0,
            data_inReg ** 0 
        )
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = HsRamPortReader()
    print(toRtl(u))        
