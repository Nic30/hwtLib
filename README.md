# hwtLib

[![Travis-ci Build Status](https://travis-ci.org/Nic30/hwtLib.png?branch=master)](https://travis-ci.org/Nic30/hwtLib)[![PyPI version](https://badge.fury.io/py/hwtLib.svg)](http://badge.fury.io/py/hwtLib)[![Coverage Status](https://coveralls.io/repos/github/Nic30/hwtLib/badge.svg?branch=master)](https://coveralls.io/github/Nic30/hwtLib?branch=master)[![Documentation Status](https://readthedocs.org/projects/hwtlib/badge/?version=latest)](http://hwtlib.readthedocs.io/en/latest/?badge=latest)
 

Hw_toolkit is library for generating, manipulatin and analysis of HDL (verilog/vhdl...) code.
This library contains:
* hardware components and helpers for Hw_toolkit
* simulations, verifications and test of components for Hw_toolikt
* examples and tests of Hw toolikt itself

```python
    from hwt.serializer.ip_packager.packager import Packager
    from hwtLib.abstract.discoverAddressSpace import AddressSpaceProbe
    
    u = AnyUnitClass()

    # export unit as IPCore
    p = Packager(u)
    p.createPackage(".")

    # print addr space of unit, first argument is main interface, 
    # lamda fn. describes which signal should be tracked (this example for AxiLite)
    addrSpace = AddressSpaceProbe(u.cntrlBus, lambda intf: intf.ar.addr).discover()
    for addr, addrSpaceItem in sorted(addrSpace.items(), key=lambda x: x[0]):
        print("0x%x:   %r" % (addr, addrSpaceItem))
```

Library can be installed by command: 
``` bash
sudo pip3 install hwtLib
```


