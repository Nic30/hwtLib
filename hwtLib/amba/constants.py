"""
Constant used for a signals in AXI, AXI-lite interfaces.

https://static.docs.arm.com/ihi0022/d/IHI0022D_amba_axi_protocol_spec.pdf
"""
BURST_FIXED = 0b00
BURST_INCR = 0b01
BURST_WRAP = 0b10


def BYTES_IN_TRANS(n):
    n = int(n)
    return n.bit_length() - 1


# http://www.gstitt.ece.ufl.edu/courses/fall15/eel4720_5721/labs/refs/AXI4_specification.pdf  p.65
# Normal Non-cacheable Bufferable
CACHE_DEFAULT = 3
"""
+--------------+--------------+-----------------------------------------+
| ARCACHE[3:0] | AWCACHE[3:0] |  Memory type                            |
+==============+==============+=========================================+
| 0000         | 0000         |  Device Non-bufferable                  |
+--------------+--------------+-----------------------------------------+
| 0001         | 0001         |  Device Bufferable                      |
+--------------+--------------+-----------------------------------------+
| 0010         | 0010         |  Normal Non-cacheable Non-bufferable    |
+--------------+--------------+-----------------------------------------+
| 0011         | 0011         |  Normal Non-cacheable Bufferable        |
+--------------+--------------+-----------------------------------------+
+--------------+--------------+-----------------------------------------+
| 1010         | 0110         |  Write-through No-allocate              |
+--------------+--------------+-----------------------------------------+
| 1110 (0110)  | 0110         |  Write-through Read-allocate            |
+--------------+--------------+-----------------------------------------+
| 1010         | 1110 (1010)  |  Write-through Write-allocate           |
+--------------+--------------+-----------------------------------------+
| 1110         | 1110         |  Write-through Read and Write-allocate  |
+--------------+--------------+-----------------------------------------+
+--------------+--------------+-----------------------------------------+
| 1011         | 0111         |  Write-back No-allocate                 |
+--------------+--------------+-----------------------------------------+
| 1111 (0111)  | 0111         |  Write-back Read-allocate               |
+--------------+--------------+-----------------------------------------+
| 1011         | 1111 (1011)  |  Write-back Write-allocate              |
+--------------+--------------+-----------------------------------------+
| 1111         | 1111         |  Write-back Read and Write-allocate     |
+--------------+--------------+-----------------------------------------+
"""

PROT_DEFAULT = 0
"""
:note: "prot" is an access permissions signals that can be used to protect
    against illegal transactions.

+--------+-------+---------------------+
| PROT   | Value | Function            |
+========+=======+=====================+
| [0]    | 0     | Unprivileged access |
+--------+-------+---------------------+
|        | 1     | Privileged access   |
+--------+-------+---------------------+
| [1]    | 0     | Secure access       |
+--------+-------+---------------------+
|        | 1     | Non-secure access   |
+--------+-------+---------------------+
| [2]    | 0     | Data access         |
+--------+-------+---------------------+
|        | 1     | Instruction access  |
+--------+-------+---------------------+
"""

QOS_DEFAULT = 0

LOCK_DEFAULT = 0

"""
+-------+----------+--------------------------+
| RESP  | Response | Description              |
+=======+==========+==========================+
| 0b00  | OKAY     | Normal access success    |
+-------+----------+--------------------------+
| 0b01  | EXOKAY   | Exclusive access success |
+-------+----------+--------------------------+
| 0b10  | SLVERR   | Slave error              |
+-------+----------+--------------------------+
| 0b11  | DECERR   | Decode error             |
+-------+----------+--------------------------+
"""
RESP_OKAY = 0
RESP_EXOKAY = 1
RESP_SLVERR = 2
RESP_DECERR = 3
