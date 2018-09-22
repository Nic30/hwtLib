# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
[![Python version](https://img.shields.io/pypi/pyversions/hwtLib.svg)](https://img.shields.io/pypi/pyversions/hwtLib.svg)


hwtLib is the library of hardware components for [hwt framework](https://github.com/Nic30/hwt). Relation of hwt and hwtLib is similar as C and stdlib relation. 


Any component can be exported as IPCore using Packager class from hwt or as HDL code by toRtl(). Target language is specified by keyword parameter serializer.


## Installation 
``` bash
sudo pip3 install hwtLib
```



## Repositories with opensource HW:

* [enjoy-digital repositories](https://github.com/enjoy-digital?tab=repositories) - Migen, SoC level modules
* [ZipCPU repositories](https://github.com/ZipCPU?tab=repositories) - Verilog, mostly preipherals, DSP
* [rhea](https://github.com/cfelton/rhea) - MyHDL, SoC level modules
* [FPGAwars FPGA-peripherals](https://github.com/FPGAwars/FPGA-peripherals) - Verilog, simple peripherals
* [PoC](https://github.com/VLSI-EDA/PoC) - VHDL, utils
* [picorv32](https://github.com/cliffordwolf/picorv32) - Verilog, A Size-Optimized RISC-V SoC
