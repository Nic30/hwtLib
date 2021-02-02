from operator import ne
from typing import List, Dict

from hwt.code import Concat, And, Or
from hwt.code_utils import _mkOp
from hwt.math import isPow2, log2ceil
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


def parity(bit_vector):
    return _mkOp(ne)(*bit_vector)


# https://chipress.co/2019/07/09/how-to-implement-pseudo-lru/
class PseudoLru():
    """
    Tree-PLRU, Pseudo Last Recently Used (LRU) algorithm
    * Often used to select least used value in caches etc.



    Example for four-way set associative cache (three bits)

    each bit represents one branch point in a binary decision tree; let 1
    represent that the left side has been referenced more recently than the
    right side, and 0 vice-versa

    .. code-block::

                   are all 4 lines valid?
                        /       \
                      yes        no, use an invalid line
                       |
                       |
                       |
                  bit_0 == 0?            state | replace      ref to | next state
                   /       \             ------+--------      -------+-----------
                  y         n             00x  |  line_0      line_0 |    11_
                 /           \            01x  |  line_1      line_1 |    10_
          bit_1 == 0?    bit_2 == 0?      1x0  |  line_2      line_2 |    0_1
            /    \          /    \        1x1  |  line_3      line_3 |    0_0
           y      n        y      n
          /        \      /        \        ('x' means       ('_' means unchanged)
        line_0  line_1  line_2  line_3      don't care)


    :note: that there is a 6-bit encoding for true LRU for four-way set associative
      bit 0: bank[1] more recently used than bank[0]
      bit 1: bank[2] more recently used than bank[0]
      bit 2: bank[2] more recently used than bank[1]
      bit 3: bank[3] more recently used than bank[0]
      bit 4: bank[3] more recently used than bank[1]
      bit 5: bank[3] more recently used than bank[2]

    :note: this is not a component in order to make this alg independent on lru reg storage type
    :ivar lru_reg: register with bits which represents binary tree
        used in pseudo LRU. It uses a common binary tree in array node representation
        index of left is 2x parent index; index of right is 2x parent index + 1
    """

    @staticmethod
    def lru_reg_width(items):
        return 2 ** log2ceil(items) - 1

    @staticmethod
    def lru_reg_items(width):
        return 2 ** log2ceil(width + 1)

    def __init__(self, lru_reg: RtlSignal):
        assert isPow2(lru_reg._dtype.bit_length() - 1) or lru_reg._dtype.bit_length() == 1, lru_reg._dtype.bit_length()
        self.lru_regs = lru_reg

    def node_selected_mask(self, lru_tree, node_i):
        """
        :ivar lru_tree: array with lru binary tree, nodes are lru registers,
            leafs are select flags
        :ivar node_i: index of node which we are checking
        """
        is_leaf = 2 * node_i + 1 >= self.lru_regs._dtype.bit_length()
        if is_leaf:
            yield lru_tree[node_i]
        else:
            # right
            yield from self.node_selected_mask(lru_tree, 2 * node_i + 1)
            # left
            yield from self.node_selected_mask(lru_tree, 2 * node_i + 2)

    def mark_use_many(self, used_item_mask):
        """
        Mark values as used just now
        """
        lru_tree = [*self.lru_regs, *used_item_mask]
        invert_mask = []
        for i in range(self.lru_regs._dtype.bit_length()):
            # flip lru node if it is accessed odd-number times
            do_invert = parity(self.node_selected_mask(lru_tree, i))
            invert_mask.append(do_invert)

        return self.lru_regs ^ Concat(*reversed(invert_mask))

    def _build_node_paths(self, node_paths: Dict[int, List[RtlSignal]],
                          i: int,
                          prefix: List[RtlSignal]):
        """
        Collect in tree paths for items.
        """
        is_last_level = 2 * i + 1 >= self.lru_regs._dtype.bit_length()
        this_node_bit = self.lru_regs[i]
        if is_last_level:
            this_node_bit = ~this_node_bit
            node_paths[i] = [*prefix, this_node_bit]
        else:
            node_paths[i] = [*prefix, this_node_bit]
            # left
            self._build_node_paths(node_paths, 2 * i + 1, [*prefix, ~this_node_bit])
            # right
            self._build_node_paths(node_paths, 2 * i + 2, [*prefix, this_node_bit])

    def get_lru(self):
        """
        To find LRU, we can perform a depth-first-search starting from root,
        and traverse nodes in lower levels. If the node is 0, then we traverse the left sub-tree;
        otherwise, we traverse the right sub-tree. In the diagram above, the LRU is set 3.
        """
        # node_index: bits  rlu register
        node_paths = {}
        self._build_node_paths(node_paths, 0, tuple())
        # also number of levels of rlu tree
        bin_index_w = log2ceil(self.lru_reg_items(self.lru_regs._dtype.bit_length()))

        lru_index_bin = []
        # msb first in lru binary index
        for output_bit_i in range(bin_index_w):
            items_on_current_level = int(2 ** output_bit_i)
            current_level_offset = 2 ** output_bit_i - 1
            possible_paths = []
            for node_i in range(
                    current_level_offset,
                    current_level_offset + items_on_current_level):
                p = node_paths[node_i]
                possible_paths.append(And(*p))
            lru_index_bin.append(Or(*possible_paths))

        # MSB was first so the result is in little endian MSB..LSB
        return Concat(*lru_index_bin)
