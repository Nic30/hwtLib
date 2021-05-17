# hwtLib
[![CircleCI](https://circleci.com/gh/Nic30/hwtLib.svg?style=svg)](https://circleci.com/gh/Nic30/hwtLib)
[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)
[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)
[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/pypi/pyversions/hwtLib.svg)](https://img.shields.io/pypi/pyversions/hwtLib.svg)
[![Join the chat at https://gitter.im/hwt-community/community](https://badges.gitter.im/hwt-community/community.svg)](https://gitter.im/hwt-community/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


hwtLib is the library of hardware components writen using [hwt library](https://github.com/Nic30/hwt).
Any component can be exported as Xilinx Vivado (IP-exact) or Quartus IPcore using [IpPackager](https://github.com/Nic30/hwtLib/blob/master/hwtLib/examples/simple_ip.py#L26) or as raw Verilog/VHDL/SystemC code and constraints by [to_rtl() function](https://github.com/Nic30/hwtLib/blob/master/hwtLib/examples/showcase0.py#L256). Target language is specified by keyword parameter `serializer`.


## Content

For example there is a component [AxiLiteEndpoint](https://github.com/Nic30/hwtLib/blob/master/hwtLib/amba/axiLite_comp/endpoint.py#L185), wich is configured using c-like data type description and it generates a address decoders and convertors to other intefaces if requested.
Another example is [AxiS_frameParser](https://github.com/Nic30/hwtLib/blob/master/hwtLib/amba/axis_comp/frame_parser/_parser.py#L438), which is configured in same way and performs an extraction of the data fields from an input stream. Hwt type system does contains all c-like and SystemVerilog-like types but in addition it allows for better specification of padding and allignment and has an explicit data type for streams. This allows AxiS_frameParser to be easily configured to change alignemnt of the stream, cut/split/replace part of the steam with an easy to read HLS-like description.

Verifications are write in UVM like style and as [hwt](https://github.com/Nic30/hwt) based design are actually a graph we can easily analyse them.
This is every usefull as it allows us to generate most of the test environment automatically in a user controlled and predictable way and write mostly only a test scenario. For example there is no need to build bus transactions manually as [AddressSpaceProbe](https://github.com/Nic30/hwtLib/blob/master/hwtLib/abstract/discoverAddressSpace.py#L47) can discover the mapped address space (for any interface) and we can set register values using a proxy as if it was a normal value.
This means that you can write a verification which will have a component with arbitrary bus/address space and it will work as long as you keep the names of the registers the same.

Clock frequencies and target chips usually does not matter but if componet [generates constraints](https://github.com/Nic30/hwtLib/blob/master/hwtLib/handshaked/cdc.py#L154) it surely needs a correct clock period to generate them correctly.

Also note that the code of the components should be shared if `@serializeParamsUniq` is used, the design for largest FPGAs takes 5s to generate. The verification should be also fast (take look at travis build) if this is not your case you are probably doing something wrong.

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
* [peripheral](https://github.com/Nic30/hwtLib/tree/master/hwtLib/peripheral) - various peripheral interfaces and components (I2C, MDIO, SPI, UART, USB, Ethernet, ...)
* [sim](https://github.com/Nic30/hwtLib/tree/master/hwtLib/sim) - simulation utils
* [structManipulators](https://github.com/Nic30/hwtLib/tree/master/hwtLib/structManipulators) - DMAs for specific data structures
* [tests](https://github.com/Nic30/hwtLib/tree/master/hwtLib/tests) - tests which are not related to another components
* [types](https://github.com/Nic30/hwtLib/tree/master/hwtLib/types) - deffinitions of common types (uint32_t, ipv6_t, udp_t, ...)
* [xilinx](https://github.com/Nic30/hwtLib/tree/master/hwtLib/xilinx) - components, primitives and interfaces specific to Xilinx based designs (IPIF, LocalLink, ...)

If you see any problem/do not underestand something/do miss something open the github issue as others may step uppon same problem sooner or later.


## Installation
``` bash
# from PYPI (latest release)
sudo pip3 install hwtLib

# or from git (latest)
sudo pip3 install -r https://raw.githubusercontent.com/Nic30/hwtLib/master/doc/requirements.txt git+git://github.com/Nic30/hwtLib#egg=hwtLib --upgrade --no-cache
```


## Repositories with opensource HW:

* [analogdevicesinc/hdl/](https://github.com/analogdevicesinc/hdl/)
* [connectal](https://github.com/cambridgehackers/connectal) - framework for software-driven hardware development
* [corundum](https://github.com/ucsdsysnet/corundum) - Packet DMA
* [Elphel repositories](https://git.elphel.com/Elphel?page=1) - Verilog, firmware for Zynq based camera with DDR3, HiSPi, JPEG
* [enjoy-digital repositories](https://github.com/enjoy-digital?tab=repositories) - Migen, SoC level modules
* [FPGAwars FPGA-peripherals](https://github.com/FPGAwars/FPGA-peripherals) - Verilog, simple peripherals
* [hdl4fpga](https://github.com/hdl4fpga/hdl4fpga) - Verilog/VHDL various peripherals
* [hdl-util](https://github.com/hdl-util) - SV, various IO
* [analogdevicesinc/hdl](https://github.com/analogdevicesinc/hdl) - Verilog, Library of common components for AnalogDevices chip interfacing
* [leon/grlib](https://www.gaisler.com/index.php/downloads/leongrlib) - Library of SoC components
* [myhdl-resources](https://github.com/xesscorp/myhdl-resources) - MyHDL list of projects
* [NyuziProcessor](https://github.com/jbush001/NyuziProcessor) - GPGPU
* [opencores](https://opencores.org/) - everything
* [openrisc](https://github.com/openrisc) - OpenRISC, FuseSoC, peripherals and cpu parts
* [picorv32](https://github.com/cliffordwolf/picorv32) - Verilog, A Size-Optimized RISC-V SoC
* [PoC](https://github.com/VLSI-EDA/PoC) - VHDL, utils
* [pulp-platform](https://github.com/pulp-platform)
* [rhea](https://github.com/cfelton/rhea) - MyHDL, SoC level modules
* [SpinalCrypto](https://github.com/SpinalHDL/SpinalCrypto) - SpinalHDL, various crypto/hash functions
* [surf](https://github.com/slaclab/surf) - VHDL, SoC/DSP/IO/Ethernet focused components
* [tinyfpgax](https://github.com/tinyfpga)
* [ultraembedded/cores](https://github.com/ultraembedded/cores) - mostly Verilog, mostly peripherals
* [ZipCPU repositories](https://github.com/ZipCPU?tab=repositories) - Verilog, mostly peripherals, DSP
* [hls-fpga-machine-learning](https://github.com/hls-fpga-machine-learning) - Python -> HSL C++, mostyl ML and video processing
* [fpgasystems](https://github.com/fpgasystems) - HLS C++, SystemVerilog, FPGA @ Systems Group, ETH Zurich, mostly networking
* [Limago](https://github.com/hpcn-uam/Limago) - SV/VHDL - 100G TCP/IP stack


