#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

# File: bitMapping.py
# Author: Brent Nelson
# Created: 24 June 2020
# Description:
#    Will compute bit mappings from init.mem bit locations to FASM INIT/INITP lines/bits and to frame/bitoffset values

import os
import sys
import glob
import parseutil.misc as misc
import parseutil.parse_mdd as parse_mdd
import argparse
import json
import pathlib
import struct
import DbgParser
import re


# Holds a single mapping record from init.mem bit to FASM and bitstream
class Mapping:
    def __init__(
        self, word, bit, tile, bits, fasmY, fasmINITP, fasmLine, fasmBit, xyz
        #frameAddr, frameBitOffset
    ):
        self.word = word
        self.bit = bit
        self.tile = tile
        self.bits = bits
        self.fasmY = fasmY
        self.fasmINITP = fasmINITP
        self.fasmLine = fasmLine
        self.fasmBit = fasmBit
        self.xyz = xyz
        #self.frameAddr = frameAddr
        #self.frameBitOffset = frameBitOffset

    def toString(self):
        return "word={}, bit={}, tile = {}, bits = {}, fasmY={}, fasmINITP={}, fasmLine={}, fasmBit={} xyz={}".format(
            self.word, self.bit, self.tile, self.bits, self.fasmY,
            self.fasmINITP, self.fasmLine, self.fasmBit, self.xyz
            #3, self.frameAddr,
            #self.frameBitOffset
        )

    def toStringShort(self):
        return "word={}, bit={}, tile = {}".format(
            self.word, self.bit, self.tile
        )


# Add mappings for a particular BRAM primitive into the mappingsn array and return it
def createBitMapping(
    words, bits, cell, mappings, verbose, printMappings
):

    # 1. Flag of whether this is RAMB36E cell or not
    ramb36 = (cell.type == "RAMB36E1") or (cell.type == "RAMB36E2") 

    # 2. Get the info on this BRAM tile from tilegrid.json
    #tilegridname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
    #    "XRAY_DATABASE"] + "/" + os.environ["XRAY_PART"] + "/tilegrid.json"
    #with open(tilegridname) as f:
    #    tilegrid = json.load(f)
    #tilegridinfo = tilegrid[cell.tile]
    #cell.baseaddr = int(tilegridinfo["bits"]["BLOCK_RAM"]["baseaddr"], 16)
    #cell.wordoffset = int(tilegridinfo["bits"]["BLOCK_RAM"]["offset"])

    # Step 2: Now build the mappings
    for w in range(words):
        for b in range(bits):
            # Just do the locations covered by this RAMB primitive
            if w < cell.addr_beg or w > cell.addr_end or b < cell.slice_beg or b > cell.slice_end:
                continue

            # 2a: Compute characteristics of this particular RAMB primitive
            RAMBinitwidth = cell.slice_end - cell.slice_beg + 1
            RAMBdepth = cell.addr_end - cell.addr_beg + 1
            RAMBreadinitwidth = cell.width
            RAMBparityinitwidth = cell.pbits
            RAMBdatainitwidth = cell.dbits
            assert RAMBinitwidth == RAMBdatainitwidth + RAMBparityinitwidth, "RAMBinitwidth ERROR: {} {} {} {}".format(
                RAMBinitwidth, RAMBreadinitwidth, RAMBparityinitwidth,
                RAMBdatainitwidth
            )

            # 2b: Determine how many bits are in parity and how many are in the "normal" bits
            if not ramb36:
                assert not RAMBreadinitwidth == 72
            initSliceinitwidth = 64 if RAMBreadinitwidth == 72 else 32 if RAMBreadinitwidth == 36 else 16 if RAMBreadinitwidth == 18 else 8 if RAMBreadinitwidth == 9 else RAMBreadinitwidth
            initpSliceinitwidth = 8 if RAMBreadinitwidth == 72 else 4 if RAMBreadinitwidth == 36 else 2 if RAMBreadinitwidth == 18 else 1 if RAMBreadinitwidth == 9 else 0

            if verbose:
                print("\nDoing: {} {}".format(w, b))
                print(
                    "{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT"
                    .format(
                        RAMBinitwidth, RAMBparityinitwidth,
                        initpSliceinitwidth, RAMBdatainitwidth,
                        initSliceinitwidth
                    ),
                    end=''
                )
                print(
                    "   {} {} {} ({}) {}:{} {}.{}".format(
                        cell.tile,
                        cell.type,
                        cell.write_style,
                        cell.width,
                        cell.addr_end,
                        cell.addr_beg,
                        cell.slice_end,
                        cell.slice_beg,
                    )
                )
                print(
                    "    This is the correct BRAM block iff: {} >= r >= {} and {} >= b >= {}"
                    .format(
                        cell.addr_end,
                        cell.addr_beg,
                        cell.slice_end,
                        cell.slice_beg,
                    )
                )
            # Some sanity checks
            # Number of bits in INIT and INITP should be 32K and 4K respectively (RAMB36E1) or 16K and 2K respectively (RAMB18E1)
            #assert initSliceinitwidth * RAMBdepth == (
            #    32768 if ramb36 else 16384
            #), "initSliceinitwidth={}, RAMBdepth={}".format(initSliceinitwidth, RAMBdepth)
            #assert initpSliceinitwidth == 0 or initpSliceinitwidth * RAMBdepth == (
            #    4096 if ramb36 else 2048
            #)

            # 2c: Is the bit of interest in the INIT portion or the INITP portion?
            if b - cell.slice_beg < initSliceinitwidth:
                # In the INIT portion
                sliceinitwidth = initSliceinitwidth
                parity = False
            else:
                # In the INITP portion
                sliceinitwidth = initpSliceinitwidth
                parity = True

            # 2.d: Compute how many "words" fit into each INIT string.
            # This may be the initwidth of the memory or it may not since
            # Vivado often pads.  Example: for a 128b1 the "read initwidth" is 18.
            # That means the memory has a 16-bit word in the INIT and a 2-bit word in the INITP.
            # In the INIT there are 15 0's as padding + the 1 bit of data.  The INITP is all 0's in this case.
            initStringLen = 512 if ramb36 else 256

            # 2.e: How many words are in each INIT and INITP string?
            numWordsPerInit = (initStringLen / sliceinitwidth)
            # Make sure it divides evenly or there must be a problem
            assert int(numWordsPerInit) == numWordsPerInit
            numWordsPerInit = int(numWordsPerInit)

            # 2.f: Compute where to find the bit in the INIT strings
            # Find which INIT or INITP entry it is in (00-3F for INIT, 00-07 for INITP)
            initRow = int((w - cell.addr_beg) / numWordsPerInit)
            assert initRow <= 0x3F, "{} {} {} {} {}".format(
                initRow, w, numWordsPerInit, initStringLen, sliceinitwidth
            )

            # 2.g: Now, compute the actual bit offset into that INIT or INITP string
            wordOffset = int(w % numWordsPerInit)
            bitOffset = wordOffset * sliceinitwidth + (
                b - cell.slice_beg - (initSliceinitwidth if parity else 0)
            )
            #if verbose:
            #    print(
            #        "FASM initRow = {} bitOffset = {}".format(
            #            initRow, bitOffset
            #        )
            #    )

            # 2.h: Get the segment info from the prjxray segments file
            lr = 0 if cell.tile[6] == "L" else 1
            y01 = 0 if ramb36 is False or bitOffset % 2 == 0 else 1
            #segoffset = findSegOffset(
            #    segs,
            #    lr,
            #    y01,
            #    1 if parity else 0,
            #    initRow,
            #    int(bitOffset / 2) if ramb36 else bitOffset,
            #)

            # 2.i: Compute the bitstream location of the bit from the above information
            ## Frame number is tilegrid.json's baseaddr + segbits frame offset number
            #frameNum = cell.baseaddr + segoffset[0]
            ## Bit offset is given in segbits file
            #frameBitOffset = int(segoffset[1]) + cell.wordoffset * 32

            # 2.j: Print out the mapping if requested
            bbb = int(bitOffset / 2) if ramb36 else bitOffset
            if printMappings or verbose:
                if parity:
                    print(
                        "init.mem[{}][{}] -> {}.{}_Y{}.INITP_{:02x}[{:03}]"
                        .format(
                            w, b, cell.tile,
                            cell.type[:-2], y01, initRow, bbb
                            #cell.tile,
                            #hex(cell.baseaddr), segoffset[0], segoffset[1],
                            #cell.wordoffset
                        )
                    )

                else:
                    print(
                        "init.mem[{}][{}] -> {}.{}_Y{}.INIT_{:02x}[{:03}]"
                        .format(
                            w, b, cell.tile,
                            cell.type[:-2], y01, initRow, bbb
                            #cell.tile,
                            #hex(cell.baseaddr), segoffset[0], segoffset[1],
                            #cell.wordoffset
                        )
                    )

            # 2.j1: Compute xyz (7 series)
            xyz = initRow * 512 + 2*bbb + y01
            xyz = xyz + 32768 if parity else xyz

            # 2.k: Finally, build a Mapping object and add it to the mappings list (to be returned below)
            mappings.append(
                Mapping(
                    w, b, cell.tile, bits, y01, parity, initRow, bbb, xyz
                    #, frameNum,
                    #frameBitOffset
                )
            )
    # All done...
    return mappings


# Given a word/bit index, find the mapping
def findMapping(w, b, bits, mappings):
    #for m in mappings:
    #    if m.word == w and m.bit == b:
    #        return m
    #assert False, "Could not find mapping: {} {}".format(w, b)
    row = (w * bits) + b
    return mappings[row]


# If this is done once and re-used, much time can be saved
def loadSegs():
    # Read the segbits database information for later use.
    # Create multidimensional array to hold it.
    # Indices from left to right are: lr, y01, initinitp, initnum, initbit, frame, framebit
    segs = [
        [
            [
                [[None
                  for j in range(256)]
                 for k in range(64)]
                for l in range(2)
            ]
            for m in range(2)
        ]
        for n in range(2)
    ]

    # Read the segbits database info
    segname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/segbits_bram_l.block_ram.db"
    with open(segname) as f:
        lines = f.readlines()
        segs = processSegLines(lines, segs)
    segname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/segbits_bram_r.block_ram.db"
    with open(segname) as f:
        lines = f.readlines()
        segs = processSegLines(lines, segs)

    return segs


# Process the segment lines read from the database and fill an array with them
def processSegLines(seglines, segs):
    # seglines is a multi-dimensional array, indexed by integers
    # Level1: [bram_l, bram_r]
    # Level 2: [y0, y1]
    # Level 3: [INIT, INITP]
    # Level 4: [0, 1, ..., 3F] (which INIT line?  could make INITP ones shorter but, hey...)
    # Level 5: [0, 1, ..., 255]  (bits from a given init line)
    # Level 6: [frame, bit]     (the location in the bitstream for this bit)
    for line in seglines:
        m = re.search(
            '^BRAM_(.)\.RAMB18_Y(.)\.([^_]*)_(..)\[(...)\] ([^_]*)_(.*)$',
            line.rstrip()
        )
        assert m is not None, "{}".format(line)
        lr = 0 if m.group(1) == 'L' else 1
        y01 = int(m.group(2))
        initinitp = 0 if m.group(3) == "INIT" else 1
        initnum = int(m.group(4), 16)
        initbit = int(m.group(5))
        frame = int(m.group(6))
        framebit = int(m.group(7))
        #print(lr)
        #print(y01)
        #print(initinitp)
        #print(initnum)
        #print(initbit)
        #print(frame)
        #print(framebit)
        #print("  {}".format(len(segs[0][0])))
        #print("  {}".format(len(segs[0][0][0])))
        #print()
        segs[lr][y01][initinitp][initnum][initbit] = [frame, framebit]
    return segs


def findSegOffset(segs, lr, y01, initinitp, initnum, initbit):
    #print("{} {} {} {} {}".format(lr, y01, initinitp, initnum, initbit))
    return segs[lr][y01][initinitp][initnum][initbit]


##############################################################################################
# Create the bitmappings for a design
##############################################################################################
def createBitMappings(
    memName,
    mddName,
    verbose,
    printMappings
):

    # 1. Load the MDD file.
    mdd_data = parse_mdd.readAndFilterMDDData(mddName, memName)
    words, bits = misc.getMDDMemorySize(mdd_data)
    #print("Words = {}, bits = {}".format(words, bits))

    # 2. Load the segment data from the prjxray database.
    #    This uses the environment variables set by prjxray
    #    Passing it into createBitMappings() each time will save a lot of time since it can be reused for all
    #       the BRAMs in a design.
    #segs = loadSegs()

    # 3. Define the data structure to hold the mappings that are returned.
    #    Format is: [word, bit, tileName, bits (width of each init.mem word), fasmY, fasmINITP, fasmLine, fasmBit, frameAddr, frameBitOffset]
    mappings = []

    # 4. Create the bitmappings for each BRAM Primitive
    for cell in mdd_data:
        mappings = createBitMapping(
            #segs,  # The segs info
            words,  # Depth of memory
            bits,  # Width of memory
            cell,  # The BRAM primitive to process
            mappings,  # The returned mappings data structure
            verbose,
            printMappings
        )

    # Inner function for use in sort below
    def mapSort(m):
        # Need a key that is ascending for the order we want
        return m.word * m.bits + m.bit

    # 5. Sort the mappings to enable fast lookups
    mappings.sort(key=mapSort)

    return mappings


# The routine createBitMappings() above is intended to be called from other programs which require the mappings.
# This main routine below is designed to test it
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir", help='Directory where design is located.')
    parser.add_argument("memname", help='Name of memory.')
    parser.add_argument("mddname", help='Base name of mdd file')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()

    mappings = createBitMappings(
        args.memname, baseDir / args.mddname, args.verbose,
        args.printmappings
    )

    # Since this is a test program, print out what was returned
    print("\nMappings:")
    for m in mappings:
        print(" {}".format(m.toString()))

    print("")

#############################################################################################################################
# bitMapping.py will compute the bit mappings for a particular memory and return them in a data structure
# The routine above called createBitMappings() is intended to be called from other programs.
# But, to test it, you can call it from the command line like this:
#      python bitMapping.py testing/tests/master/1kb1 mem/ram 1kb1.mdd
#
# This program will print out the resulting data structure to the terminal if you call it from the command line like above.  Here is an example:
#  word=127, bit=0, tile = BRAM_L_X6Y5, bits = 1, fasmY=0, fasmINITP=False, fasmLine=7, fasmBit=240, frameAddr=c0000f, frameBitOffset=327
# As you can see from the code, it prints out the values in each mapping record it creates.  In the line above,
#  init[127][0] can be found in BRAM_L_X6Y5, fasm Y0, INIT line 7, bit=240
#  The same bit can also be found in frame c0000f, bit offset 327.
# So, what is the "bits = 1" doing?  It is there just to tell you how many bits are in each word of the INIT file.
#     For most purposes it is not needed but if you ever go to re-create an init.mem file you will need it to know how wide to make each word.
#
# You can experiment with this program from the command line but the real use of it comes when calling createBitMappings() to get the data structure returned.
# See fasm2init.py for an example program.
