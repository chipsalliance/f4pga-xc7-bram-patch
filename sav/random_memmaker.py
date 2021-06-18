#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import sys
import random as r
import math


def pad(ch, wid, data):
    data = str(data)
    return (ch * (wid - len(data)) + data)

def mylog2(n):
    val = 0
    while round(math.pow(2, val)) < n:
        val += 1
    return val

def main(fname, width, depth, allOnes=False):

    if type(width) is str:
        width = int(width)
    if type(depth) is str:
        depth = int(depth)

    # Go up to next power of 2
    addrwid = mylog2(depth)
    depth =  1<<addrwid

    make_mem(fname=fname, width=width, depth=depth, allOnes=allOnes)


def make_mem(fname, width, depth, allOnes):
    vals = []
    max_data_val = (2**width) - 1
    w = int(width / 4) + 1
    vals = []
    for i in range(depth):
        if allOnes is False:
            v = hex(r.randint(0, max_data_val))[2:]
        else:
            v = hex(max_data_val)[2:]
        vals.append(v)


#    print('Width = {} vals = {}'.format(width, vals))
    perline = 0
    if width == 1:
        perline = 256
    elif width <= 2:
        perline = 128
    elif width <= 4:
        perline = 64
    elif width <= 9:
        perline = 32
    elif width <= 18:
        perline = 16
    elif width <= 36:
        perline = 8
    elif width <= 72:
        perline = 4
    elif width <= 128:
        perline = 2
    else:
        perline = 1
    with open(fname, 'w+') as f:
        vals = [vals[x:x + perline] for x in range(0, depth, perline)]
        for val in vals:
            f.write(' '.join(val))
            f.write('\n')
            # print(' '.join(val))
    print(
        'Randomized memory initialization complete - printed to {}'.
        format(fname)
    )

if __name__ == "__main__":
    if len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2], sys.argv[3], True)
    else:
        print(
            "Usage: python  random_memmaker.py fileToCreate width(in bits) depth(in words) allones(optional)"
        )
        exit(1)
