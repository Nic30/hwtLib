from itertools import product
# from pprint import pprint
from typing import List, Tuple

from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from math import inf


class ByteSrcInfo():
    """
    Container for informations about byte in stream data

    :ivar stream_i: index of stream
    :ivar word_i: index of word in frame
    :ivar byte_i: index of byte in word
    :ivar is_from_last_input_word: true if this byte comes from
        last word in input frame
    """

    def __init__(self, stream_i: int, word_i: int, byte_i: int,
                 is_from_last_input_word: bool):
        self.stream_i = stream_i
        self.word_i = word_i
        self.byte_i = byte_i
        self.is_from_last_input_word = is_from_last_input_word

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
            and self.as_tuple() == other.as_tuple()

    def __lt__(self, other):
        if other is None:
            return False
        return self.as_tuple() < other.as_tuple()

    def __hash__(self):
        return hash(self.as_tuple())

    def as_tuple(self):
        return (self.stream_i, self.word_i, self.byte_i, self.is_from_last_input_word)

    def __repr__(self):
        return "<%s %d, w:%d, B:%d, l:%d>" % (
            self.__class__.__name__, self.stream_i, self.word_i,
            self.byte_i, self.is_from_last_input_word)


def append_data_from_frame(res, word_bytes, data_in, curr_word):
    had_any_data = False
    for d_bytes in data_in:
        for d in d_bytes:
            if len(curr_word) == word_bytes:
                # current data word full
                curr_word = []
                res.append(curr_word)

            if d is not None:
                curr_word.append(d)

        had_any_data = True

    return curr_word, had_any_data


def join_streams(word_bytes, stream_data: List[List[Tuple[List[object], bool]]],
                 offset=0):
    """
    :param word_bytes: number of bytes in output word
    :param stream_data: list of data for each stream input
        (stream data is list of data words, data word is tuple: list of data bytes, last word flag)
    :param offset: offset of output stream
    """
    assert offset >= 0 and offset < word_bytes, (offset, word_bytes)
    res = []
    _data = [iter(data) for data in stream_data]
    has_any_data = True
    while has_any_data:
        has_any_data = False
        # start of new frame
        curr_word = [None for _ in range(offset)]
        res.append(curr_word)

        # take data from input frame
        for data in _data:
            curr_word, has_any_data = append_data_from_frame(
                res, word_bytes, data, curr_word)
        if has_any_data:
            # fill end of the frame
            if len(curr_word) == 0:
                res.pop()
                curr_word = res[-1]

            for _ in range(word_bytes - len(curr_word)):
                curr_word.append(None)
        else:
            res.pop()

    return freeze_frame(res)


def freeze_frame(f):
    return tuple(tuple(w) for w in f)


def create_frame(word_bytes, stream_i, byte_cnt, offset_out, offset_in):
    """
    :param offset_out: how many empty bytes should be put before data in frame
    :param offset_in: how many bytes skip from imput stream
    """
    assert byte_cnt > 0, byte_cnt
    assert offset_out >= 0, offset_out
    assert offset_in >= 0, offset_in

    frame = []
    if offset_out:
        frame.append([None for _ in range(offset_out)])
        last_in_word_i = 0
    else:
        last_in_word_i = -1

    last_word_i = ((offset_in + byte_cnt - 1) // word_bytes)
    for i in range(byte_cnt):
        in_B_i = i + offset_in
        in_byte_i = in_B_i % word_bytes
        in_word_i = in_B_i // word_bytes
        is_from_last_input_word = int(in_word_i == last_word_i)
        B_info = ByteSrcInfo(stream_i, in_word_i, in_byte_i, is_from_last_input_word)

        if in_word_i == last_in_word_i:
            frame[-1].append(B_info)
        else:
            assert last_in_word_i == in_word_i - 1
            last_in_word_i = in_word_i
            frame.append([B_info, ])

    last_data_word = frame[-1]
    for _ in range(word_bytes - len(last_data_word)):
        last_data_word.append(None)

    return freeze_frame(frame)


def get_bytes_in_frame_info(offset_out, offset_in, word_bytes,
                            chunk_size, chunk_cnt, already_has_body_words):
    assert chunk_cnt > 0, chunk_cnt
    assert chunk_size > 0, chunk_size

    offset = max(offset_in, offset_out)
    first_word_bytes = min(word_bytes - offset, chunk_cnt * chunk_size)
    last_word_bytes = (offset + chunk_size * chunk_cnt) % word_bytes
    has_body_words = (offset + chunk_size * chunk_cnt) >= (2 * word_bytes)
    # if first_word_bytes + last_word_bytes == word_bytes and word_bytes % chunk_size == 0:
    #    # the output offset will be same after adding data from this frame
    #    has_body_words = False

    first_word_is_last_word = (offset + chunk_cnt * chunk_size) <= word_bytes

    min_representative_frame_size = first_word_bytes
    if has_body_words and (offset != 0 or not already_has_body_words):
        min_representative_frame_size += word_bytes
    if not first_word_is_last_word\
            and not (
                has_body_words
                and last_word_bytes == word_bytes
            ):
        min_representative_frame_size += last_word_bytes
    if first_word_bytes == word_bytes and min_representative_frame_size > word_bytes:
        has_body_words = True
    return first_word_bytes, has_body_words, last_word_bytes, min_representative_frame_size


def get_important_byte_cnts(offset_out, offset_in, word_bytes, chunk_size,
                            chunk_cnt_min, chunk_cnt_max):
    """
    Filter chunk cnt range, let only those values
    which affect the number of valid bytes
    in first/last word of frame and presence of words in body frame
    """
    assert chunk_cnt_min <= chunk_cnt_max, (chunk_cnt_min, chunk_cnt_max)
    if isinstance(chunk_cnt_min, int) and isinstance(chunk_cnt_max, int)\
            and chunk_cnt_min == chunk_cnt_max:
        _, _, _, min_representative_frame_size = get_bytes_in_frame_info(
            offset_out, offset_in, word_bytes, chunk_size, chunk_cnt_min, False)
        return [min_representative_frame_size, ]

    _chunk_cnt_min = chunk_cnt_min % (2 * word_bytes)
    chunk_cnt_max = _chunk_cnt_min + \
        min((2 * word_bytes), chunk_cnt_max - chunk_cnt_min)
    chunk_cnt_min = _chunk_cnt_min
    sizes = set()
    already_has_body_words = False
    for chunk_cnt in range(chunk_cnt_min, chunk_cnt_max + 1):
        (_,
         has_body_words,
         _,
         min_representative_frame_size) = get_bytes_in_frame_info(
            offset_out, offset_in, word_bytes, chunk_size, chunk_cnt,
            already_has_body_words)
        sizes.add(min_representative_frame_size)
        already_has_body_words |= has_body_words

    return sorted(sizes)


def stream_to_all_possible_frame_formats(t: HStream, stream_i: int,
                                         word_bytes: int, offset_out: int):
    frames = []
    chunk_size = t.element_t.bit_length() // 8
    for offset_in in t.start_offsets:
        for byte_cnt in get_important_byte_cnts(
                offset_out, offset_in, word_bytes,
                chunk_size, t.len_min, t.len_max):
            frame = create_frame(word_bytes, stream_i,
                                 byte_cnt, offset_out, offset_in)
            frames.append(frame)
    return frames


def count_not_none(items):
    for i, b in enumerate(items):
        if b is not None:
            return i
    return 0


def streams_to_all_possible_frame_formats(t: HStruct, word_bytes: int, offset: int):
    assert isinstance(t, HStruct)
    frames_per_stream = []
    prev_end_offsets = [offset, ]
    for i, f in enumerate(t.fields):
        t = f.dtype
        f_frames = set()
        for offset_out in prev_end_offsets:
            f_frames_tmp = stream_to_all_possible_frame_formats(
                t, i, word_bytes, offset_out)
            f_frames.update(f_frames_tmp)

        f_frames = list(f_frames)
        # pprint(f_frames)
        frames_per_stream.append(f_frames)
        _prev_end_offsets = prev_end_offsets
        prev_end_offsets = set()
        # for each frame resolve end alignment of the frames
        for frame in f_frames:
            last_word = frame[-1]
            o = count_not_none(last_word)
            prev_end_offsets.add(o)

        prev_end_offsets = sorted(prev_end_offsets)

    res = set()
    for frame_combination in product(*frames_per_stream):
        res_frame = join_streams(word_bytes, frame_combination, offset)
        res.add(res_frame)

    res = list(res)
    return res


def resolve_input_bytes_destinations(frames, input_cnt, word_bytes):
    """
    :param frames: list of all possible frame formats generated
        from streams_to_all_possible_frame_formats
    :param input_cnt: number of input streams
    :param word_bytes: number of bytes in output and input words
    """
    def init_word():
        return [set() for _ in range(word_bytes)]

    input_B_dst = [init_word() for _ in range(input_cnt)]

    def add_dst(state_name, input_i, input_B_i, input_time_offset, output_B_i,
                is_last_word_from_this_input):
        input_B_dst[input_i][input_B_i].add((
            state_name,
            input_time_offset,
            output_B_i,
            is_last_word_from_this_input))

    for f_i, f in enumerate(frames):
        # print("frame %d" % f_i)
        for output_word_i, w in enumerate(f):
            # print("%d: %r" % (output_word_i, w))
            state_label = (f_i, output_word_i)

            min_word_i_per_input_in_this_out_word = [inf for _ in range(input_cnt)]
            for output_B_i, byte_info in enumerate(w):
                if byte_info is None:
                    continue
                i = byte_info.stream_i
                min_word_i_per_input_in_this_out_word[i] =\
                    min(min_word_i_per_input_in_this_out_word[i], byte_info.word_i)
            for output_B_i, byte_info in enumerate(w):
                if byte_info is None:
                    continue
                input_i = byte_info.stream_i
                input_B_i = byte_info.byte_i
                time_offset = byte_info.word_i - min_word_i_per_input_in_this_out_word[input_i]
                assert time_offset >= 0, time_offset
                add_dst(state_label, input_i, input_B_i, time_offset,
                        output_B_i, byte_info.is_from_last_input_word)

    return input_B_dst
