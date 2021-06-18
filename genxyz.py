#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import os
import sys
import glob
import parseutil
import argparse
import json
import pathlib
import struct
import DbgParser
import patch_mem
import re

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("llfile")
    parser.add_argument("mappings")
    args = parser.parse_args()

    with open(args.llfile) as llfile:
        while True:
            lin = llfile.readline()
            if lin.startswith("Bit"):
                frameoffset = int(lin.split(' ')[2], 16)
                break
    print("Frameoffset = {}".format(hex(frameoffset)))

    with open(args.llfile) as llfile:
        llines = llfile.readlines()
    with open(args.mappings) as mappingsfile:
        mlines = mappingsfile.readlines()

    lls = []
    for lin in llines:
        if not lin.startswith("Bit "):
            continue
        # Bit 14189340 0x00800000    860 Block=RAMB36_X0Y12 Ram=B:BIT53
        m = re.search(
            '^Bit \d+ (0x[^ ]+)[ ]*(\d+) Block=[^ ]+ Ram=B:([^\d]+)(\d+)',
            lin.strip()
        )
        if m:
            frame = int(m.group(1), 16) - frameoffset
            bitoffset = int(m.group(2))
            par = "INITP" if (m.group(3) == "PARBIT") else "INIT"
            xyz = int(m.group(4))
            #print("{} {} {} {}".format(hex(frame), bitoffset, par, xyz))
            lls.append([frame, bitoffset, par, xyz])

    mappings = []
    for lin in mlines:
        if not lin.startswith("init.mem"):
            continue
        # init.mem[0][6] -> BRAM_L_X6Y60.RAMB36_Y0.INIT_00[003] -> BRAM_L_X6Y60 0x800000 0_48 wordoffset = 20
        #m = re.search('^init.mem\[(\d+)\]\[(\d+)\] -> BRAM[^.]+[^_]+Y(\d)\.INIT([^_]*)_(..)\[(...)\] -> BRAM[^ ]+ (0x[^ ]+) ([^_]+)_([^ ]+) wordoffset = ([\d]+)',
        m = re.search(
            '^init.mem\[(\d+)\]\[(\d+)\] -> [^.]+[^Y]+Y(.).INIT([^_]*)_(..).(...). -> [^ ]+ ([^ ]+) ([^_]+)_([^ ]+) wordoffset = ([\d]+)',
            lin.strip()
        )

        if m:
            word = int(m.group(1))
            bit = int(m.group(2))
            ynum = int(m.group(3))
            parity = "INITP" if m.group(4) == "P" else "INIT"
            initline = int(m.group(5), 16)
            initbit = int(m.group(6))
            frame = int(m.group(7), 16)
            frameoffset = int(m.group(8))
            bitoffset = int(m.group(9))
            wordoffset = int(m.group(10))
            tmp = [
                word, bit, ynum, parity, initline, initbit, frame, frameoffset,
                bitoffset, wordoffset, wordoffset * 32 + bitoffset
            ]
            #print(tmp)
            mappings.append(tmp)

    # Now do the matching
    def llsort(lin):
        return lin[0] * 3232 + lin[1]

    lls.sort(key=llsort)

    def mpsort(lin):
        return lin[7] * 3232 + lin[10]

    mappings.sort(key=mpsort)

    #for lin in lls:
    #    print(lin)
    #for m in mappings:
    #    print(m)

    res = []
    for i in range(32768 + 4096):
        ll = lls[i]
        m = mappings[i]
        assert ll[0] == m[7]
        assert ll[1] == m[10]
        res.append([m[2], m[3], m[4], m[5], ll[3]])

    def resSort(r):
        return r[4] if r[1] == "INIT" else r[4] + 32768

    res.sort(key=resSort)

    for r in res:
        print(
            "Y{} {}_{:02x}[{}] = bit {}".format(r[0], r[1], r[2], r[3], r[4])
        )
