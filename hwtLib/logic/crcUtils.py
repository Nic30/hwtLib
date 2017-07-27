import re
from copy import copy


def parsePolyStr_parse_n(string):
    "Parse the number part of a polynomial string term"
    if not string:
        return 1
    elif string == '-':
        return -1
    elif string == '+':
        return 1
    else:
        if re.match("\s*\+\s*1\s*", string):
            return 1
        return int(string)


def parsePolyStr_parse_p(string):
    "Parse the power part of a polynomial string term"
    pat = re.compile('x\^?(\d+)?')
    if not string:
        return 0
    res = pat.findall(string)[0]
    if not res:
        return 1
    return int(res)


def parsePolyStr(polyStr, width):
    coefs = [0 for _ in range(width)]
    """\
    Do very, very primitive polynom parsing of a string into a list of coefficients.
    'x' is the only term considered for the polynomial, and this
    routine can only handle terms of the form:
    7x^2 + 6x - 5
    and will choke on seemingly simple forms such as
    x^2*7 - 1
    or
    x**2 - 1

    :return: list of coefficients
    """
    termpat = re.compile('([-+]?\s*\d*\.?\d*)(x?\^?(\d+)?)')
    res_dict = {}
    for n, powStr, _ in termpat.findall(polyStr):
        n, p = n.strip(), powStr.strip()
        if not n and not p:
            continue
        n, p = parsePolyStr_parse_n(n), parsePolyStr_parse_p(p)

        if p in res_dict:
            res_dict[p] += n
        else:
            res_dict[p] = n

    for key, value in res_dict.items():
        coefs[key] = value

    return coefs


def crc_serial_shift(num_bits_to_shift,
                     polySize,
                     coefs,
                     lfsr_cur,
                     dataWidth,
                     data_cur):
    """
    :param polySize: bit size of polynomial
    :param coefs: array of 1,0 which representing the polynomial
    :param lfsr_cur: array with single 1 flag which specifies
        for which bit we are currently counting the crc
    :pram dataWidth: bit widtho of input signal to this crc round
    :pram data_cur: ray with single 1 flag which specifies
        for which bit we are currently counting the crc
    """

    assert num_bits_to_shift <= dataWidth

    lfsr_next = copy(lfsr_cur)
    lfsr_poly_size = len(coefs)

    for j in range(num_bits_to_shift):
        # shift the entire LFSR
        lfsr_upper_bit = lfsr_next[lfsr_poly_size - 1]

        for i in range(lfsr_poly_size - 1, 0, -1):
            if coefs[i]:
                lfsr_next[i] = lfsr_next[i - 1] ^ lfsr_upper_bit ^ data_cur[j]
            else:
                lfsr_next[i] = lfsr_next[i - 1]

        lfsr_next[0] = lfsr_upper_bit ^ data_cur[j]

    return lfsr_next


def buildCrcMatrix_dataMatrix(coefs, polyWidth, dataWidth):
    """
    generate LSFR reg,  matrix[MxN]

    :param coefs: Polynomial coefficients
    :param polyWidth: number of bits of Polynomial
    :param dataWidth: number of bits of data signal
    """
    reg_cur = [0 for _ in range(polyWidth)]
    data_cur = [0 for _ in range(dataWidth)]
    data_matrix = [[0 for _ in range(dataWidth)]
                   for _ in range(polyWidth)]

    for m1 in range(dataWidth):
        # set flag for crc_serial_shift
        data_cur[m1] = 1
        if m1:
            # clean last flag
            data_cur[m1 - 1] = 0

        _data_matrix = crc_serial_shift(dataWidth,
                                        polyWidth,
                                        coefs,
                                        reg_cur,
                                        dataWidth,
                                        data_cur)

        for n2, b in enumerate(_data_matrix):
            if b:
                # dataWidth - m1 - 1
                data_matrix[n2][m1] = 1

    return data_matrix


def buildCrcMatrix_reg0Matrix(coefs, polyWidth, dataWidth):
    reg_cur = [0 for _ in range(polyWidth)]
    data_cur = [0 for _ in range(dataWidth)]
    reg_matrix = [[0 for _ in range(polyWidth)]
                  for _ in range(polyWidth)]

    # lfsr reg to lfsr reg connections
    for n1 in range(polyWidth):
        reg_cur[n1] = 1
        if n1:
            reg_cur[n1 - 1] = 0

        reg_next = crc_serial_shift(dataWidth,
                                    polyWidth,
                                    coefs,
                                    reg_cur,
                                    dataWidth,
                                    data_cur)

        for n2, b in enumerate(reg_next):
            if b:
                reg_matrix[n2][n1] = 1

    return reg_matrix


def buildCrcMatrix(coefs, polyWidth, dataWidth):
    regMatrix = buildCrcMatrix_reg0Matrix(coefs, polyWidth, dataWidth)
    dataMatrix = buildCrcMatrix_dataMatrix(coefs, polyWidth, dataWidth)

    return regMatrix, dataMatrix
