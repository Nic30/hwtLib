#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.enum import Enum
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.code import If, Concat, FsmBuilder, In
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.interfaces.peripheral import I2c


NOP, START, STOP, READ, WRITE = range(5)

def hasRisen(last, actual):
    return ~last & actual

def hasFallen(last, actual):
    return last & ~actual

class I2cMasterBitCtrl(Unit):
    """
    -----------------------------------
     Bit controller section
    ----------------------------------
    
     Translate simple commands into SCL/SDA transitions
     Each command has 5 states, 0/1/2/3/idle
    
     start:    SCL  ~~~~~~~~~~~~~~\____
               SDA  XX/~~~~~~~\______
                    x | 0 | 1 | 2 | 3 | i
    
     repstart  SCL  ______/~~~~~~~\___
               SDA  __/~~~~~~~\______
                    x | 0 | 1 | 2 | 3 | i
    
     stop      SCL  _______/~~~~~~~~~~~
               SDA  ==\___________/~~~~~
                    x | 0 | 1 | 2 | 3 | i
    
     - write    SCL  ______/~~~~~~~\____
               SDA  XXX===============XX
                    x | 0 | 1 | 2 | 3 | i
    
     - read     SCL  ______/~~~~~~~\____
               SDA  XXXXXXX=XXXXXXXXXXX
                    x | 0 | 1 | 2 | 3 | i
    
    
     Timing:      Normal mode     Fast mode
    ---------------------------------------------------------------
     Fscl         100KHz          400KHz
     Th_scl       4.0us           0.6us   High period of SCL
     Tl_scl       4.7us           1.3us   Low period of SCL
     Tsu:sta      4.7us           0.6us   setup time for a repeated start condition
     Tsu:sto      4.0us           0.6us   setup time for a stop condition
     Tbuf         4.7us           1.3us   Bus free time between a stop and start condition
    """
    def _config(self):
        self.CLK_CNTR_WIDTH = Param(16)
        
    def _declr(self):
        addClkRstn(self)
        self.clk_cnt_initVal = Signal(dtype=vecT(16))
        self.i2c = I2c()
        
        self.cmd = Signal(dtype=vecT(4))
        self.cmd_ack = Signal()  # command completed
        self.busy = Signal()  # i2c bus busy
        self.arbitrationLost = Signal()  # arbitration lost
        
        self.din = Signal()
        self.dout = Signal()
    
    def stateClkGen(self, scl_sync, scl_t, scl):
        # whenever the slave is not ready it can delay the cycle by pulling SCL low
        # delay scl_oen
        delayedScl_t = self._reg("delayedScl_t", defVal=1) 
        delayedScl_t ** scl_t
        
        # slave_wait is asserted when master wants to drive SCL high, but the slave pulls it low
        # slave_wait remains asserted until the slave releases SCL
        slave_wait = self._reg("slave_wait", defVal=0)
        slave_wait ** ((~scl_t & delayedScl_t & ~scl) | (slave_wait and ~scl))
        
        clkCntr = self._reg("clkCntr",
                            vecT(self.CLK_CNTR_WIDTH, False),
                            defVal=self.clk_cnt_initVal)
        stateClkEn = self._reg("stateClkEn", defVal=1)
        
        If(clkCntr._eq(0) | scl_sync,
           clkCntr ** self.clk_cnt_initVal,
           stateClkEn ** 1
        ).Elif(slave_wait,
           stateClkEn ** 0
        ).Else(
           clkCntr ** (clkCntr - 1),
           stateClkEn ** 0
        )
        
        return stateClkEn
    
    def filter(self, name, sig):
        """attempt to remove glitches"""
        filter0 = self._reg(name + "_filter0", dtype=vecT(2), defVal=0)
        filter0 ** (filter0[0]._concat(sig))
        
        # let filter_cnt to be shared between filters
        try:
            filter_clk_cntr = self.filter_clk_cntr
        except AttributeError:
            filter_clk_cntr = self.filter_clk_cntr = self._reg("filter_clk_cntr",
                                                     vecT(self.CLK_CNTR_WIDTH),
                                                     defVal=self.clk_cnt_initVal)
            If(filter_clk_cntr._eq(0),
               filter_clk_cntr ** self.clk_cnt_initVal
            ).Else(
               filter_clk_cntr ** (filter_clk_cntr - 1)    
            )

        
        filter1 = self._reg(name + "_filter1", dtype=vecT(3), defVal=0b111)
        If(filter_clk_cntr._eq(0),
           filter1 ** Concat(filter1[2:], filter0[1])
        )
        
        filtered = ((filter1[2] & filter1[1]) | 
                    (filter1[2] & filter1[0]) | 
                    (filter1[1] & filter1[0]))
        return filtered
    
    def detectStartAndStop(self, scl, sda, scl_t):
        """
        @attention: also dout driver
        """
        lastScl = self._reg("lastScl", defVal=0)
        lastSda = self._reg("lastSda", defVal=0)
               
        startCond = hasFallen(lastSda, sda) & scl     
        stopCond = hasRisen(lastSda, sda) & scl   
                        
        lastScl ** scl
        lastSda ** sda
    
        dout = self._reg("dout", defVal=0)
        dout ** hasRisen(lastScl, scl)
        self.dout ** dout
        
        # master drives SCL high, but another master pulls it low
        # master start counting down its low cycle now (clock synchronization)
        scl_sync = lastScl & ~scl & ~scl_t
    
        return startCond, stopCond, scl_sync
    
    def busyDriver(self, startCond, stopCond):
        busy = self._reg("busy_reg", defVal=0)
        busy ** ((startCond | busy) & ~stopCond)
        self.busy ** busy
    
    def arbitrationLostDriver(self, st, sda, sda_chk, sda_t, stopCond, stateClkEn):
        """
        aribitration lost when:
        1) master drives SDA high, but the i2c bus is low
        2) stop detected while not requested (detect during 'idle' state)
        """
        
        al = self._reg("al", defVal=0)
        cmd_stop = self._reg("cmd_stop", defVal=0)
        If(stateClkEn,
           cmd_stop ** self.cmd._eq(STOP)
        )
        
        
        _al = (sda_chk & ~sda & ~sda_t)
        If(st._eq(st._dtype.idle),
           al ** (_al | (stopCond & ~cmd_stop))
        ).Else(
           al ** _al
        )
        self.arbitrationLost ** al
    
        return al
    
    def _impl(self):
        cmd = self.cmd
        cmd_ack = self.cmd_ack
        stT = Enum("stT", ["idle",
                    "start_0", "start_1", "start_2", "start_3", "start_4",
                    "stop_0", "stop_1", "stop_2", "stop_3",
                    "rd_0", "rd_1", "rd_2", "rd_3",
                    "wr_0", "wr_1", "wr_2", "wr_3"])
        
        fsm = FsmBuilder(self, stT)
        st = fsm.stateReg
        
        # check SDA status (multi-master arbitration)
        sda_chk = self._reg("sda_chk", defVal=0)
        scl_t = self._reg("scl_t", defVal=0)
        sda_t = self._reg("sda_t", defVal=0)
        
        scl = self.filter("scl", self.i2c.scl.i)
        sda = self.filter("sda", self.i2c.sda.i)
        
        startCond, stopCond, scl_sync = self.detectStartAndStop(scl, sda, scl_t)
        stateClkEn = self.stateClkGen(scl_sync, scl_t, scl)
        self.busyDriver(startCond, stopCond)
        al = self.arbitrationLostDriver(st, sda, sda_chk, sda_t, stopCond, stateClkEn)

        def stateSequence(sequneceName, stateCnt):
            for i in range(stateCnt):
                stateFrom = getattr(stT, sequneceName + "_%d" % i)
                if i == stateCnt - 1:
                    stateTo = stT.idle
                else:
                    stateTo = getattr(stT, sequneceName + "_%d" % (i + 1))
                
                fsm.Trans(stateFrom,
                        (al, stT.idle),
                         stateTo
                )
        fsm.Trans(stT.idle,
                  (al, stT.idle),
                  (cmd._eq(START), stT.start_0),
                  (cmd._eq(STOP), stT.stop_0),
                  (cmd._eq(WRITE), stT.wr_0),
                  (cmd._eq(READ), stT.rd_0),
        
        )
        stateSequence("start", 5)
        stateSequence("stop", 4)
        stateSequence("rd", 4)
        stateSequence("wr", 4)
        
        If(al,
           cmd_ack ** 0,
           sda_t ** 0,
           scl_t ** 0,
           sda_chk ** 0,
        ).Else(
            If(In(st, [stT.start_1, stT.start_2, stT.start_3,
                       stT.stop_1, stT.stop_2, stT.stop_3,
                       stT.rd_1, stT.rd_2,
                       stT.wr_1, stT.wr_2]),
               scl_t ** 0
            ).Elif(In(st, [stT.start_4, stT.stop_0,
                           stT.rd_0, stT.rd_3,
                           stT.wr_0, stT.wr_3]),
               scl_t ** 1
            ),
               
            If(In(st, [stT.start_0, stT.start_1,
                       stT.stop_3,
                       stT.rd_0, stT.rd_1, stT.rd_2, stT.rd_3]),
               sda_t ** 0
            ).Elif(In(st, [stT.start_2, stT.start_3, stT.start_4,
                        stT.stop_0, stT.stop_1, stT.stop_2]),
               sda_t ** 1
            ).Elif(In(st, [stT.wr_0, stT.wr_1, stT.wr_2, stT.wr_3]),
               sda_t ** self.din 
            ),
            # cmd ack at the end of state sequence   
            If(In(st, [stT.start_4, stT.stop_3, stT.rd_3, stT.wr_3]),
                cmd_ack ** 1
            ).Else(
                cmd_ack ** 0
            )
        )

        self.i2c.scl.o ** 0
        self.i2c.sda.o ** 0
        self.i2c.scl.t ** scl_t
        self.i2c.sda.t ** sda_t

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = I2cMasterBitCtrl()
    print(toRtl(u))
    
