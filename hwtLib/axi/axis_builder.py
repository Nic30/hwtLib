#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.abstract.streamBuilder import AbstractStreamBuilder
from hwtLib.axi.axis_fifo import AxiSFifo
from hwtLib.axi.axis_reg import AxiSReg
from hwtLib.axi.axis_mux import AxiSMux
from hwtLib.axi.axis_fork import AxiSFork

class AxiSBuilder(AbstractStreamBuilder):
    """
    Helper class which simplifies building of large stream paths 
    """
    FifoCls = AxiSFifo
    ForkCls = AxiSFork
    RegCls  = AxiSReg
    MuxCls  = AxiSMux 