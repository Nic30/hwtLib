# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![codecov](https://codecov.io/gh/Nic30/hwtLib/branch/master/graph/badge.svg)](https://codecov.io/gh/Nic30/hwtLib)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/pypi/pyversions/hwtLib.svg)](https://img.shields.io/pypi/pyversions/hwtLib.svg)
[![Join the chat at https://gitter.im/hwt-community/community](https://badges.gitter.im/hwt-community/community.svg)](https://gitter.im/hwt-community/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


hwtLib is the library of hardware components for [hwt framework](https://github.com/Nic30/hwt)
Any component can be exported as IP-exact IPcore using [IpPackager](https://github.com/Nic30/hwtLib/blob/master/hwtLib/examples/simple_ip.py#L26) or as Verilog/VHDL/SystemC code by [to_rtl()](https://github.com/Nic30/hwtLib/blob/master/hwtLib/examples/showcase0.py#L256) (Verilog, VHDL, ...). Target language is specified by keyword parameter serializer. Note that for most of components there is a schematic in the documentation.


## Content

Majority of components in this library is actually configurable component generator.
For example there is no address decoder which takes a list of addresses and produces a mapped register file for Axi4Lite interface.
Instead there is a component AxiLiteEndpoint, which takes hdl type description of address space
and generates a address decoders and convertors to other intefaces if requested.
Another example is AxiS_frameParser, which takes a hdl type description of output data and can be also used to change alignment of a frame or split/cut frame
as the type description can also contains unions, struct, streams, padding and other hdl data types.

Same applies to simulation. Instead of hardcoding address values in to testbench you should use a AddressSpaceProbe to discover
a addresses of mapped memory cells and use this object to communicate through the bus interface, because you want to write a verification
which does not depends on interface used nor manually compute addresses for each component variant.


* [abstract](https://github.com/Nic30/hwtLib/tree/master/hwtLib/abstract) - abstract classes for component classes like bus endpoint, etc
* [amba](https://github.com/Nic30/hwtLib/tree/master/hwtLib/amba) - AXI interfaces and components for them (AXI3/4 DMAs, interconnects, Axi-stream components, Axi4Lite address decoders etc...)
* [avalon](https://github.com/Nic30/hwtLib/tree/master/hwtLib/avalon) - same thing as amba just for Avalon interfaces (AvalonST, AvalonMM, ... and components for them)
* [cesnet](https://github.com/Nic30/hwtLib/tree/master/hwtLib/cesnet) - components and interfaces specific to Cesnet designs
* [clocking](https://github.com/Nic30/hwtLib/tree/master/hwtLib/clocking) - various generic PLLs, timer generators etc.
* [examples](https://github.com/Nic30/hwtLib/tree/master/hwtLib/examples) - demonstrative examples of [hwt](https://github.com/Nic30/hwt/) functionality
* [handshaked](https://github.com/Nic30/hwtLib/tree/master/hwtLib/handshaked) - components for handshaked interfaces (FIFO, AsyncFifo, Resizer, interconnects, Register, ...)
* [img](https://github.com/Nic30/hwtLib/tree/master/hwtLib/img) - image preprocessing utils (parse PNG font to bits for OLED, ...)
* [interfaces](https://github.com/Nic30/hwtLib/tree/master/hwtLib/interfaces) - various interfaces which does not have it's package yet
* [logic](https://github.com/Nic30/hwtLib/tree/master/hwtLib/logic) - various components like CRC generator, gray counter, decoders-encoders ...
* [mem](https://github.com/Nic30/hwtLib/tree/master/hwtLib/mem) - various memories (BRAM, ROM, FIFO, Async FIFO, CAM, LUT, ...)
* [peripheral](https://github.com/Nic30/hwtLib/tree/master/hwtLib/peripheral) - various peripheral interfaces and components for them (I2C, MDIO, SPI, UART, USB, Ethernet, ...)
* [sim](https://github.com/Nic30/hwtLib/tree/master/hwtLib/sim) - simulation utils
* [structManipulators](https://github.com/Nic30/hwtLib/tree/master/hwtLib/structManipulators) - DMAs for specific data structures
* [tests](https://github.com/Nic30/hwtLib/tree/master/hwtLib/tests) - tests which are not related to another components
* [types](https://github.com/Nic30/hwtLib/tree/master/hwtLib/types) - deffinitions of common types (uint32_t, ipv6_t, udp_t, ...)
* [xilinx](https://github.com/Nic30/hwtLib/tree/master/hwtLib/xilinx) - components and interfaces specific to Xilinx based designs (IPIF, LocalLink, ...)


## Installation
``` bash
sudo pip3 install hwtLib
```


## Repositories with opensource HW:

* [analogdevicesinc/hdl/](https://github.com/analogdevicesinc/hdl/)
* [connectal](https://github.com/cambridgehackers/connectal) - framework for software-driven hardware development
* [corundum](https://github.com/ucsdsysnet/corundum) - Packet DMA
* [enjoy-digital repositories](https://github.com/enjoy-digital?tab=repositories) - Migen, SoC level modules
* [FPGAwars FPGA-peripherals](https://github.com/FPGAwars/FPGA-peripherals) - Verilog, simple peripherals
* [leon/grlib](https://www.gaisler.com/index.php/downloads/leongrlib) - Library of SoC components
* [myhdl-resources](https://github.com/xesscorp/myhdl-resources) - MyHDL list of projects
* [NyuziProcessor](https://github.com/jbush001/NyuziProcessor) - GPGPU
* [opencores](https://opencores.org/)
* [openrisc](https://github.com/openrisc) - OpenRISC, FuseSoC, peripherals and cpu parts
* [picorv32](https://github.com/cliffordwolf/picorv32) - Verilog, A Size-Optimized RISC-V SoC
* [PoC](https://github.com/VLSI-EDA/PoC) - VHDL, utils
* [pulp-platform](https://github.com/pulp-platform)
* [rhea](https://github.com/cfelton/rhea) - MyHDL, SoC level modules
* [surf](https://github.com/slaclab/surf) - VHDL, SoC/DSP/IO/Ethernet focused components
* [tinyfpgax](https://github.com/tinyfpga)
* [ultraembedded/cores](https://github.com/ultraembedded/cores) - mostly Verilog, mostly peripherals
* [ZipCPU repositories](https://github.com/ZipCPU?tab=repositories) - Verilog, mostly peripherals, DSP
* [hls-fpga-machine-learning](https://github.com/hls-fpga-machine-learning) - Python -> HSL C++, mostyl ML and video processing
* [fpgasystems](https://github.com/fpgasystems) - HLS C++, SystemVerilog, FPGA @ Systems Group, ETH Zurich, mostly networking 

