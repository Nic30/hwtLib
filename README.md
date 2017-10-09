# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
 
Library can be installed by command: 
``` bash
sudo pip3 install hwtLib
```


Any component can be exported as IPCore using Packager class from hwt or as pure code by toRtl().
Target language is specified by keyword serializer.
```python
    from hwt.serializer.ip_packager.packager import Packager
    
    u = AnyUnitClass()

    # example configuration
    u.DATA_WIDTH.set(64) #  DATA_WIDTH is instance of Param which is used to mark config

    # export unit as IPCore
    p = Packager(u)
    p.createPackage(".")
```


Repositories with opensource HW:

https://github.com/enjoy-digital?tab=repositories

https://github.com/cfelton/rhea

https://github.com/FPGAwars/FPGA-peripherals
