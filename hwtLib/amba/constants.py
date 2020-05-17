"""
Constant used for a signals in AXI, AXI-lite interfaces.
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

PROT_DEFAULT = 0
"""
:note: "prot" is an access permissions signals that can be used to protect
    against illegal transactions.

+--------+-------+---------------------+
| PROT   | Value | Function            |
+========+=======+=====================+
| [0]    | 0     | Unprivileged access |
|        | 1     | Privileged access   |
| [1]    | 0     | Secure access       |
|        | 1     | Non-secure access   |
| [2]    | 0     | Data access         |
|        | 1     | Instruction access  |
+--------+----------+------------------+
"""

QOS_DEFAULT = 0

LOCK_DEFAULT = 0

"""
+-------+----------+-----------------------+
| RESP  | Response | Desciption            |
+=======+==========+=======================+
| 0b00  | OKAY     | Normal access success |
| 0b10  | SLVERR   | Slave error           |
| 0b11  | DECERR   | Decode error          |
+-------+----------+-----------------------+
"""
RESP_OKAY = 0
RESP_EXOKAY = 1
RESP_SLVERR = 2
RESP_DECERR = 3
