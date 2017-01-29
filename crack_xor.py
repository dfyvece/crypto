#!/usr/bin/env python

import sys
import argparse
import base64


def xor(data, key):
    data = data.decode("hex")
    key = key.decode("hex")
    res = ""
    for i in range(len(data)):
        x = ord(data[i])
        y = ord(key[i % len(key)])
        res += chr(x ^ y)
    return res.encode("hex")


def weighted_score(frequency_table, data):
    score = 0
    for c in data:
        if c in frequency_table.keys():
            score -= frequency_table[c]
        else:
            score += 50
    return score


def hamming_score(frequency_table, data):
    data_map = {}
    count = 0
    for i in frequency_table.keys():
        data_map[i] = 0

    score = 0
    for c in data:
        if c in frequency_table.keys():
            data_map[c] += 1
            count += 1
        else:
            score += 50

    if count > 0:
        for k in data_map.keys():
            score += abs(frequency_table[k] - (data_map[k] / float(count)))
    return score


def english_score(data, hamming=False):
    english_frequency_table = {
        'e': 12.01,
        't': 9.10,
        'a': 8.12,
        'o': 7.68,
        'i': 7.31,
        'n': 6.95,
        's': 6.28,
        'r': 6.02,
        'h': 5.92,
        'd': 4.32,
        'l': 3.98,
        'u': 2.88,
        'c': 2.71,
        'm': 2.61,
        'f': 2.30,
        'y': 2.11,
        'w': 2.09,
        'g': 2.03,
        'p': 1.82,
        'b': 1.49,
        'v': 1.11,
        'k': 0.69,
        'x': 0.17,
        'q': 0.11,
        'j': 0.10,
        'z': 0.07
    }
    if hamming:
        return hamming_score(english_frequency_table, data)
    return weighted_score(english_frequency_table, data)


def single_byte_xor(data, hamming=False):
    best_score = sys.maxint
    best_res = ("", 0)
    for i in range(255):
        s = chr(i).encode("hex")
        d = xor(data, s).decode("hex")
        score = english_score(d, hamming)
        if score < best_score:
            best_score = score
            best_res = d, s
    return best_res


def hamming(a, b):
    dist = 0
    for i in range(len(a)):
        x = ord(a[i])
        y = ord(b[i])
        dist += bin(x ^ y).count("1")
    return dist


def get_first(item):
    return item[0]


def guess_key_size(data):
    key_size = len(data) / 16
    best = []

    for sz in range(1, key_size):
        a = data[:sz]
        b = data[sz:2*sz]
        c = data[2*sz:3*sz]
        d = data[3*sz:4*sz]
        e = data[4*sz:5*sz]
        f = data[5*sz:6*sz]
        g = data[6*sz:7*sz]
        h = data[7*sz:8*sz]
        i = data[8*sz:9*sz]
        j = data[9*sz:10*sz]
        k = data[10*sz:11*sz]
        l = data[11*sz:12*sz]
        m = data[12*sz:13*sz]
        n = data[13*sz:14*sz]
        o = data[14*sz:15*sz]
        p = data[15*sz:16*sz]
        dist = 0
        dist += hamming(a, b) / float(sz)
        dist += hamming(b, c) / float(sz)
        dist += hamming(c, d) / float(sz)
        dist += hamming(d, e) / float(sz)
        dist += hamming(e, f) / float(sz)
        dist += hamming(f, g) / float(sz)
        dist += hamming(g, h) / float(sz)
        dist += hamming(h, i) / float(sz)
        dist += hamming(i, j) / float(sz)
        dist += hamming(j, k) / float(sz)
        dist += hamming(k, l) / float(sz)
        dist += hamming(l, m) / float(sz)
        dist += hamming(m, n) / float(sz)
        dist += hamming(n, o) / float(sz)
        dist += hamming(o, p) / float(sz)
        best.append((dist, sz))
    best.sort(key=get_first)
    return best


def repeating_key_xor(data, guess=1, hamming=False):
    data = data.decode("hex")
    guesses = guess_key_size(data)
    key_size = guesses[guess-1][1]
    key = ""
    for i in range(key_size):
        block = ""
        j = i
        while j < len(data):
            block += data[j]
            j += key_size
        _, k = single_byte_xor(block.encode("hex"), hamming)
        key += k
    return xor(data.encode("hex"), key), key


def base64_to_hex(data):
    data = base64.b64decode(data)
    return data.encode("hex")


def pretty_print(data,
                 decode=False,
                 raw=False,
                 b64=False,
                 showkey=False,
                 guess=1,
                 ham=False):
    if b64:
        data = base64_to_hex(data)
    elif raw:
        data = data.encode("hex")
    else:
        data = data.strip()
    decrypted, key = repeating_key_xor(data, guess, ham)
    if showkey:
        print "\nKey (Hex)  : '%s'" % (key)
        print "Key (ASCII): '%s'" % (key.decode("hex"))
    print "\nPlaintext:"
    if decode:
        decrypted = decrypted.decode("hex")
    print decrypted


def main():
    parser = argparse.ArgumentParser(
        description="Decode XOR encrypted hex data",
        epilog="Default behavior is to read from stdin until EOF"
    )
    parser.add_argument("-f", "--file",
        metavar="FILE_NAME",
        help='read content from specified file(s) instead of stdin',
        type=str,
        action='append'
    )
    parser.add_argument("-n", "--num",
        metavar="NUM",
        type=int,
        default=1,
        help="use this to specify which guess to use "
             "(useful if first guess didn't work)",
    )
    parser.add_argument("-r", "--raw",
        help='data is a raw string',
        action='store_true'
    )
    parser.add_argument("-d", "--decode",
        help='return raw (hex decoded) data',
        action='store_true'
    )
    parser.add_argument("-b", "--base64",
        help='data is base64 encoded',
        action='store_true'
    )
    parser.add_argument("-k", "--key",
        help='print key',
        action='store_true'
    )
    parser.add_argument("--hamming",
        help='use hamming metric for scoring (less reliable)',
        action='store_true'
    )

    args = vars(parser.parse_args())

    for key in args.keys():
        if args[key] is None:
            del args[key]

    if "file" in args:
        for fname in args["file"]:
            print "="*60
            print "File: %s" % (fname)
            print "="*60
            f = open(fname, 'r')
            data = f.read()
            pretty_print(data,
                         args["decode"],
                         args["raw"],
                         args["base64"],
                         args["key"],
                         args["num"],
                         args["hamming"])
        sys.exit(0)

    # Read from stdin until EOF
    data = sys.stdin.read()
    pretty_print(data,
                 args["decode"],
                 args["raw"],
                 args["base64"],
                 args["key"],
                 args["num"],
                 args["hamming"])

if __name__ == '__main__':
    main()
