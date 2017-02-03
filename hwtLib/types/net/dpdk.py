from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t, uint32_t
from hwt.hdlObjects.typeShortcuts import vecT

phys_addr_t = uint64_t
ptr = uint64_t
#    struct rte_mbuf {
rte_mbuf= [
#     MARKER      cacheline0;            #/*     0     0 */
     (ptr,        "buf_addr"),           #/*     0     8 */
     (phys_addr_t,"buf_physaddr"),       #/*     8     8 */
     (uint16_t,   "buf_len"),            #/*    16     2 */
     
     #MARKER8     rearm_data;            #/*    18     0 */
     (uint16_t,   "data_off"),           #/*    18     2 */
     (uint16_t,   "refcnt"),             #/*    20     2 */
     (uint8_t ,   "nb_segs"),            #/*    22     1 */
     (uint8_t ,   "port"),               #/*    23     1 */
     (uint64_t,   "ol_flags"),           #/*    24     8 */
     
     #MARKER      rx_descriptor_fields1; #/*    32     0 */
     (uint32_t,   "packet_type"),        #/*    32     4 */
     (uint32_t,   "pkt_len"),            #/*    36     4 */
     (uint16_t,   "data_len"),           #/*    40     2 */
     (uint16_t,   "vlan_tci"),           #/*    42     2 */
     (uint64_t,   "hash"),               #/*    44     8 */
     (uint32_t,   "seqn"),               #/*    52     4 */
     (uint16_t,   "vlan_tci_outer"),     #/*    56     2 */
     (vecT(6*8), None),
     #/* XXX 6 bytes hole, try to pack */
     #/* --- cacheline 1 boundary (64 bytes) --- */
     #MARKER                     cacheline1;           /*    64     0 */
     (uint64_t,   "userdata"),           #/*    64     8 */ struct rte_mempool * 
     (ptr,        "pool"),               #/*    72     8 */ struct rte_mbuf * 
     (ptr,        "next"),               #/*    80     8 */
     (uint64_t,   "tx_offload"),         #/*    88     8 */
     (uint16_t,   "priv_size"),          #/*    96     2 */
     (uint16_t,   "timesync"),           #/*    98     2 */

    ]
#     /* size: 128, cachelines: 2, members: 25 */
#     /* sum members: 94, holes: 1, sum holes: 6 */
#     /* padding: 28 */
#};

    