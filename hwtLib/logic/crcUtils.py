import re


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
