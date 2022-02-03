#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

# File: checkTheBits.py
# Author: Brent Nelson
# Created: 24 June 2020
# Description:
#    Will verify that the bits in an init.mem file are where it says they should be in the FASM file and bitstream.
#    If a bit mismatch is found between a given init.mem file and locations in the FASM or bitstream file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown that means all checked out.

import os
import sys
import glob
import parseutil
import parseutil.misc as misc
import argparse
import json
import pathlib
import struct
import DbgParser
import bitMapping
import patch_mem
import re
import parseutil.misc as misc


# Check the bits for a complete memory
def checkTheBits(
    baseDir,  # pathlib.Path
    memName,  # str
    mdd,  # pathlib.Path
    initFile,  # pathlib.Path
    fasmFile,  # pathlib.Path
    verbose,  # bool
    printmappings  # bool
):

    designName = baseDir.name

    # 0. Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(mdd, memName)
    initwordcnt, initbitwidth = misc.getMDDMemorySize(mdd_data)

    # 1. Read the init.mem file for this design
    # Put the contents into an array of strings
    initMemContents = parseutil.parse_init_test.read_initfile(
        initFile, initbitwidth
    )
    words = len(initMemContents)
    assert initwordcnt == words, "Discrepancy between length of .init file and design as reported by Vivado: {} vs. {} \n  (Vivado sometimes lies about length of small memories).".format(
        words, initwordcnt
    )

    # 2. Get the mapping infols /
    print("Loading mappings for {}...".format(designName))
    mappings = bitMapping.createBitMappings(
        baseDir,  # The directory where the design lives
        memName,
        mdd,
        False,
        printmappings
    )
    print("  Done loading mappings")

    # 3. Load up the bit file
    #    It MUST be a debug bitstream which is generated in Vivado using the following command in the .tcl file before called write_bitstream:
    #          set_property BITSTREAM.GENERAL.PERFRAMECRC YES [current_design]
    frames = DbgParser.loadFrames(
        baseDir / "vivado" / "{}.bit".format(designName)
    )

    # 4. Read the fasm file for this cell and collect the INIT/INITP lines
    init0lines, init0plines, init1lines, init1plines = misc.readInitStringsFromFASMFile(
        fasmFile
    )

    # 5. Check each cell
    for cell in mdd_data:
        # inits will be indexed as inits[y01][initinitp]
        inits = [[None for j in range(2)] for k in range(2)]

        # Convert the FASM lines into the proper format strings
        # Store them in a multi-dimensional array indexed by y01 and INITP/INIT (True/False)
        inits[0][False] = misc.processInitLines("0s", init0lines, cell, False)
        inits[0][True] = misc.processInitLines("0ps", init0plines, cell, True)
        inits[1][False] = misc.processInitLines("1s", init1lines, cell, False)
        inits[1][True] = misc.processInitLines("1ps", init1plines, cell, True)

        for w in range(words):
            for b in range(initbitwidth):
                if w < cell.addr_beg or w > cell.addr_end:
                    continue
                if b < cell.slice_beg or b > cell.slice_end:
                    continue

                # Get the bit from the memory
                initbit = initMemContents[w][b]

                # Get the bit from the FASM line
                mapping = bitMapping.findMapping(w, b, initbitwidth, mappings)
                assert mapping is not None, "{} {} {}".format(
                    w, b, initbitwidth
                )
                # Now get the actual bit
                fasmbit = inits[mapping.fasmY][mapping.fasmINITP][
                    mapping.fasmLine][mapping.fasmBit]

                # Get the bit from the bitstream
                frame = mapping.frameAddr
                bitOffset = mapping.frameBitOffset
                frwd = frames[frame][int(bitOffset / 32)]
                # Mask off just the bit we want out of the 32
                # 1. Doing a mod 32 will tell which bit num it is
                # 2. Then, shift over and mask
                frbit = (frwd >> bitOffset % 32) & 0x1

                # Check the bits
                if verbose:
                    print("Mapping: " + mapping.toString())
                    print(
                        "Frame = {:x} bitOffset = {} frwd = {} frbit = {}".
                        format(frame, bitOffset, frwd, frbit)
                    )
                assert fasmbit == initbit, "initbit: {} != fasmbit: {} ({}:{} {} {} \n   {})".format(
                    initbit, fasmbit, w, b, initMemContents[w], initbitwidth,
                    mapping.toString()
                )
                assert str(
                    frbit
                ) == initbit, "initbit: {} != bitstream bit: {}".format(
                    initbit, frbit
                )

                if printmappings:
                    print("bit[{}][{}] = {}".format(w, b, initbit))

        # If we got here, it worked.
        # So say so if you were asked to...
        print(
            "    Cell: {} {} {} all checked out and correct!".format(
                designName, cell.tile, cell.type
            ),
            flush=True
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument(
        "memname", help='Name of memory to check (as in "mem/ram")'
    )

    parser.add_argument("--verbose", action='store_true')

    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )

    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    designName = baseDir.name

    checkTheBits(
        baseDir, args.memname, baseDir / "{}.mdd".format(designName),
        baseDir / "init/init.mem", baseDir / "real.fasm", args.verbose,
        args.printmappings
    )

    print("")

########################################################################
# checkTheBits.py will check that the bits in the init.mem file match those
# in the real.fasm file and also in the bitstream.
# To run it:
#       python checkTheBits.py testing/tests/master/128b1 mem/ram
# You will see if there are any errors thrown.  If not, everything checked out.
# The code shows how to pull bits from a bitstream as well.  Important: the code above
#     tells how to ensure you have a debug bitstream for this to work with.
########################################################################
