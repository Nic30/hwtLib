#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Union, Set, Tuple

from hwt.bitmask import selectBitRange
from hwt.code import log2ceil, isPow2, connect, SwitchLogic
from hwt.hdl.constants import READ, WRITE
from hwt.hdl.typeShortcuts import hBit
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.unit import Unit
from hwtLib.ipif.intf import Ipif


class IpifInterconnectMatrix(Unit):
    """
    Simple matrix interconnect for IPIF interface
    """
    
    AUTO_ADDR = "AUTO_ADDR"
    FEATURE_READ_ONLY = {READ}
    FEATURE_WRITE_ONLY = {WRITE}
    FEATURE_READ_AND_WRITE = {READ, WRITE}

    def __init__(self, masters: List[Tuple[int, Set]], slaves: List[Tuple[Union[int, "AUTO_ADDR"], int, Set]]):
        """
        :param masters: list of tuples (offset, features) for each master
        :param slaves: list of tuples (offset, size, features) for each slave
        :note: features can be found on definition of this class
        """
        self._masters = masters

        _slaves = []
        maxAddr = 0
        for offset, size, features in slaves:
            if not isPow2(size):
                raise AssertionError(
                    "Size which is not power of 2 is suboptimal for interconnects")
            if offset == self.AUTO_ADDR:
                offset = maxAddr
                isAligned = (offset % size) == 0
                if not isAligned:
                    offset = ((offset // size) + 1) * size
            else:
                isAligned = (offset % size) == 0
                if not isAligned:
                    raise AssertionError("Offset which is not aligned to size is suboptimal")

            maxAddr = max(maxAddr, offset + size)
            _slaves.append((offset, size, features))

        self._slaves = sorted(_slaves, key=lambda x: x[0])

        # check for address space colisions
        lastAddr = -1
        for offset, size, features in self._slaves:
            if lastAddr >= offset:
                raise ValueError(
                    "Address space on address 0x%X colliding with previous" % offset)
            lastAddr = offset + size - 1

        super(IpifInterconnectMatrix, self).__init__()

    def getOptimalAddrSize(self):
        assert self._slaves
        last =  self._slaves[-1]
        maxAddr = last[0] + last[1]
        maxAddr -= int(self.DATA_WIDTH) // 8
        assert maxAddr >= 0
        return log2ceil(maxAddr)

    def _config(self)->None:
        Ipif._config(self)

    def _declr(self)->None:
        addClkRstn(self)

        slavePorts = HObjList()
        for _, features in self._masters:
            if features is not self.FEATURE_READ_AND_WRITE:
                raise NotImplementedError(features)
            m = Ipif()
            m._updateParamsFrom(self)
            slavePorts.append(m)

        self.s = slavePorts

        masterPorts = HObjList()
        for _, size, features in self._slaves:
            if features is not self.FEATURE_READ_AND_WRITE:
                raise NotImplementedError(features)
            s = Ipif()._m()
            s.ADDR_WIDTH.set(log2ceil(size - 1))
            s._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
            masterPorts.append(s)

        self.m = masterPorts

    def _impl(self)->None:
        if len(self._masters) > 1:
            raise NotImplementedError()

        m_offset, _ = self._masters[0]
        if m_offset != 0:
            raise NotImplementedError()

        m = self.s[0]

        err = hBit(0)
        rdack = hBit(0)
        wrack = hBit(0)
        AW = int(self.ADDR_WIDTH)
        wdata = []
        for i, (s, (s_offset, s_size, _)) in enumerate(zip(self.m, self._slaves)):
            
            connect(m.bus2ip_addr, s.bus2ip_addr, fit=True)
            s.bus2ip_be(m.bus2ip_be)
            s.bus2ip_rnw(m.bus2ip_rnw)
            s.bus2ip_data(m.bus2ip_data)
            
            bitsOfSubAddr = int(log2ceil(s_size - 1))
            prefix = selectBitRange(
                s_offset, bitsOfSubAddr, AW - bitsOfSubAddr)
            cs = self._sig("m_cs_%d" % i)
            cs(m.bus2ip_addr[AW:bitsOfSubAddr]._eq(prefix))
            s.bus2ip_cs(m.bus2ip_cs & cs)
            
            err = err | (cs & s.ip2bus_error)
            rdack = rdack | (cs & s.ip2bus_rdack)
            wrack = wrack | (cs & s.ip2bus_wrack)
            wdata.append((cs, s.ip2bus_data))

        m.ip2bus_error(err)
        m.ip2bus_rdack(rdack)
        m.ip2bus_wrack(wrack)

        SwitchLogic(
            [(sel, m.ip2bus_data(data)) for sel, data in wdata],
            default=m.ip2bus_data(None)
        )


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    RW = IpifInterconnectMatrix.FEATURE_READ_AND_WRITE
    AUTO = IpifInterconnectMatrix.AUTO_ADDR
    u = IpifInterconnectMatrix(
        masters=[(0x0, RW)],
        slaves=[
            (0x0000,  0x100, RW),
            (0x0100,  0x100, RW),
            (AUTO,    0x100, RW),
            (0x1000, 0x1000, RW),
        ]
    )

    print(toRtl(u))
