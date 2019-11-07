# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/pypi/pyversions/hwtLib.svg)](https://img.shields.io/pypi/pyversions/hwtLib.svg)


hwtLib is the library of hardware components for [hwt framework](https://github.com/Nic30/hwt) (= IPcore repository).



## Content

Majority of components in this library is actually configurable component generator.
Any component can be exported as IPCore using hwt.Packager or as HDL code by [toRtl()](https://github.com/Nic30/hwt/blob/master/hwt/synthesizer/utils.py#L17) (Verilog, VHDL, ...). Target language is specified by keyword parameter serializer. Note that for most of components there is a schematic in the documentation.

* [abstract](https://github.com/Nic30/hwtLib/tree/master/hwtLib/abstract) - abstract classes for component classes like bus endpoint, etc
* [amba](https://github.com/Nic30/hwtLib/tree/master/hwtLib/amba) - AXI interfaces and components for them (AXI3/4 DMAs, interconnects, ..., Axi-stream components, ..., Axi4Lite address decoders etc...)
* [avalon](https://github.com/Nic30/hwtLib/tree/master/hwtLib/avalon) - same thing as amba just for Avalon interfaces (AvalonST, AvalonMM, ... and components for them)
* [clocking](https://github.com/Nic30/hwtLib/tree/master/hwtLib/clocking) - various PLLs, timer generators etc.
* [examples](https://github.com/Nic30/hwtLib/tree/master/hwtLib/examples) - demonstrative examples of [hwt](https://github.com/Nic30/hwt/) functionality
* [handshaked](https://github.com/Nic30/hwtLib/tree/master/hwtLib/handshaked) - components for handshaked interfaces (FIFO, AsyncFifo, Resizer, interconnects, Register, ...)
* [img](https://github.com/Nic30/hwtLib/tree/master/hwtLib/img) - image preprocessing utils (parse PNG fornt to bits for OLED)
* [interfaces](https://github.com/Nic30/hwtLib/tree/master/hwtLib/interfaces) - various interfaces which does not have it's package yet
* [IPIF](https://github.com/Nic30/hwtLib/tree/master/hwtLib/ipif) - IPIF interface and components for it (Interconnect, Register, address decoder, ...)
* [logic](https://github.com/Nic30/hwtLib/tree/master/hwtLib/logic) - various components like CRC generator, gray counter, decoders-encoders ...
* [mem](https://github.com/Nic30/hwtLib/tree/master/hwtLib/mem) - various memories (BRAM, ROM, FIFO, Async FIFO, CAM, LUT, ...)
* [peripheral](https://github.com/Nic30/hwtLib/tree/master/hwtLib/peripheral) - various peripheral interfaces and components for them (I2C, SPI, UART)
* [sim](https://github.com/Nic30/hwtLib/tree/master/hwtLib/sim) - simulation utils
* [structManipulators](https://github.com/Nic30/hwtLib/tree/master/hwtLib/structManipulators) - DMAs for specific data structures
* [tests](https://github.com/Nic30/hwtLib/tree/master/hwtLib/tests) - tests which are not related to another components
* [types](https://github.com/Nic30/hwtLib/tree/master/hwtLib/types) - deffinitions of common types (uint32_t, ipv6_t, udp_t, ...)

## Installation
``` bash
sudo pip3 install hwtLib
```



## Repositories with opensource HW:

* [analogdevicesinc/hdl/](https://github.com/analogdevicesinc/hdl/)
* [corundum](https://github.com/ucsdsysnet/corundum) - Packet DMA
* [enjoy-digital repositories](https://github.com/enjoy-digital?tab=repositories) - Migen, SoC level modules
* [FPGAwars FPGA-peripherals](https://github.com/FPGAwars/FPGA-peripherals) - Verilog, simple peripherals
* [leon/grlib](https://www.gaisler.com/index.php/downloads/leongrlib) - Library of SoC components
* [NyuziProcessor](https://github.com/jbush001/NyuziProcessor) - GPGPU
* [openrisc](https://github.com/openrisc) - OpenRISC, FuseSoC, peripherals and cpu parts
* [picorv32](https://github.com/cliffordwolf/picorv32) - Verilog, A Size-Optimized RISC-V SoC
* [PoC](https://github.com/VLSI-EDA/PoC) - VHDL, utils
* [pulp-platform](https://github.com/pulp-platform)
* [rhea](https://github.com/cfelton/rhea) - MyHDL, SoC level modules
* [tinyfpgax](https://github.com/tinyfpga)
* [ZipCPU repositories](https://github.com/ZipCPU?tab=repositories) - Verilog, mostly preipherals, DSP
