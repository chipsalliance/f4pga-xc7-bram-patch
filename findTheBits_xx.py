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

# File: findTheBits_18.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Will verify that the bits in an init.mem file are where it says they should be in the FASM file and bitstream.
#    If a bit mismatch is found between a given init.mem file and locations in the FASM or bitstream file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown that means all checked out.

import os
import sys
import glob
import parseutil
import argparse
import json
import pathlib
import struct
import DbgParser


# Check the bits for a complete memory
def findAllBits(
    dr, mdd_data, cell, initFile, fasmFile, verbose, mappings, check
):

    designName = dr.name

    # Flag of whether this is RAMB36E cell or not
    ramb36 = (cell.type == "RAMB36E1")

    # Step 1: Read the init.mem file for this design
    # Put the contents into an array of strings
    initMemContents = parseutil.parse_init_test.initfile_to_initlist(
        initFile, mdd_data
    )
    # Step 2: Read the fasm file for this design and collect the INIT lines for this cell.
    if ramb36:  # This is for RAMB36E1's
        # Get all the INIT lines
        init0lines, init0plines, init1lines, init1plines = readInitStringsFromFASMFile(
            cell, fasmFile
        )

        # Convert those into the proper format strings
        init0s = processInitLines(init0lines, False)
        init0ps = processInitLines(init0plines, True)
        init1s = processInitLines(init1lines, False)
        init1ps = processInitLines(init1plines, True)

        # Now zip the Y0 and Y1 bits together into big 512 character lines.
        # The even characters come from Y0 and the odd from Y1
        # Once this is done the memory can be handled pretty much
        # like the RAMB18E1 ones in the later code below.
        inits = []
        for i in range(len(init0s)):
            itm = ""
            for j in range(256):
                itm = itm + init0s[i][j] + init1s[i][j]
            inits.append(itm)
        initps = []
        for i in range(len(init0ps)):
            itm = ""
            for j in range(256):
                itm = itm + init0ps[i][j] + init1ps[i][j]
            initps.append(itm)
    else:  # !ramb36 - This is for RAMB18E1's
        # Read all the INIT lines from the FASM file
        init0lines, init0plines, init1lines, init1plines = readInitStringsFromFASMFile(
            cell, fasmFile
        )
        # Only the init0 and init0p should have anything since this is a RAMB18E1 primitive
        assert len(init1lines) == 0, "{}".format(designName)
        assert len(init1plines) == 0, "{}".format(designName)

        # Get all the init lines for this cell, pad them with 0's, and reverse them
        inits = processInitLines(init0lines, False)
        initps = processInitLines(init0plines, True)

    # Step 4: Read the segbits database information for later use.  Also find record in tilegrid.json
    # First, read the segbits database info
    segname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/segbits_bram_l.block_ram.db"
    with open(segname) as f:
        segl_lines = f.readlines()
    segname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/segbits_bram_r.block_ram.db"
    with open(segname) as f:
        segr_lines = f.readlines()
    # Now, get the tileinfo from tilegrid.json
    tilegridname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/" + os.environ["XRAY_PART"] + "/tilegrid.json"
    with open(tilegridname) as f:
        tilegrid = json.load(f)
    tilegridinfo = tilegrid[cell.tile]
    cell.baseaddr = int(tilegridinfo["bits"]["BLOCK_RAM"]["baseaddr"], 16)
    cell.wordoffset = int(tilegridinfo["bits"]["BLOCK_RAM"]["offset"])

    # Step 5: Load up the bit file if checking is requested
    if check:
        frames = DbgParser.loadFrames(
            dr / "vivado" / "{}.bit".format(designName)
        )

    # Step 7: Now check if we can find all the bits in this cell
    # We use the length of the init file to determine the # of words to check since
    # for a small memory (128b1), Vivado will generate a larger one, knowing you will
    # only use the lower part of the memory.
    # NOTE: this doesn't quite what the description of the program says.
    # The description says it will check and output the mapping for every bit in the init file.
    # Technically, this checks and outputs every bit in every RAMB primitive making up your memory.
    # Should be equivalent since all init file bits should be in the RAMB primitives, but there may be cases.
    for w in range(cell.addr_beg, cell.addr_beg + len(initMemContents)):
        for b in range(cell.slice_beg, cell.slice_end + 1):
            bwid = cell.slice_end - cell.slice_beg + 1
            wdep = cell.addr_end - cell.addr_beg + 1
            rwid = cell.width
            pwid = cell.pbits
            dwid = cell.dbits
            if bwid != dwid + pwid:
                print(
                    "     BWID ERROR: {} {} {} {}".format(
                        bwid, rwid, pwid, dwid
                    ),
                    file=sys.stderr
                )
                continue

            # Determine how many bits are in parity and how many are in the "normal" bits
            # Also, only a RAMB36E1 can have an rwid of 72
            if not ramb36:
                assert not rwid == 72
            islice = 64 if rwid == 72 else 32 if rwid == 36 else 16 if rwid == 18 else 8 if rwid == 9 else rwid
            pslice = 8 if rwid == 72 else 4 if rwid == 36 else 2 if rwid == 18 else 1 if rwid == 9 else 0

            if verbose:
                print("Doing: {} {}".format(w, b))
                print(
                    "{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT"
                    .format(bwid, pwid, pslice, dwid, islice),
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
            assert islice * wdep == (32768 if ramb36 else 16384)
            if pslice != 0:
                assert pslice * wdep == (4096 if ramb36 else 2048)

            # Is the bit of interest in the INIT portion or the INITP portion?
            if b - cell.slice_beg < islice:
                bslice = islice
                parity = False
            else:
                bslice = pslice
                parity = True

            # Compute how many "words" fit into each INIT string.
            # This may be the width of the memory or it may not since
            # Vivado often pads.  Example: for a 128b1 the "read width" is 18.
            # That means the memory has a 16-bit word in the INIT and a 2-bit word in the INITP.
            # In the INIT there are 15 0's as padding + the 1 bit of data.
            initLen = 512 if ramb36 else 256

            # How many words are in each INIT and INITP string?
            numPerInit = (initLen / bslice)
            # Make sure it divides evenly or there must be a problem
            assert int(numPerInit) == numPerInit

            if verbose:
                print(
                    "{} {} {} {} {} {}".format(
                        w, b, cell.width, len(initMemContents),
                        len(initMemContents[w]) - 1 - b, initMemContents[w]
                    )
                )
            # Pull the bit from the .mem inititalization file array
            initbit = initMemContents[w][len(initMemContents[w]) - 1 - b]

            # Compute where to find the bit in the INIT strings (after they were combined and reversed above)
            # Find which INIT or INITP it is
            initRow = int(w / numPerInit)
            # Now, compute the actual bit offset into that INIT or INITP string
            wordOffset = int(w % numPerInit)
            bitOffset = wordOffset * bslice + (
                b - cell.slice_beg - (islice if parity else 0)
            )
            if verbose:
                print(
                    "FASM initRow = {} bitOffset = {}".format(
                        initRow, bitOffset
                    )
                )
            # Read the bit from either the INIT or the INITP word
            if parity:
                fasmbit = initps[initRow][bitOffset]
            else:
                fasmbit = inits[initRow][bitOffset]

            if verbose:
                print("Bit[{}][{}] = {} vs. {}".format(w, b, initbit, fasmbit))

            # Check that the bits match each other, proving that the above algorithm is correct
            if check:
                assert initbit == fasmbit

            # Look up the actual frame/bit numbers from the
            # prjxray database (the .../prjxray/database/artix7/segbits_bram_*.block_ram.db file)
            initRow = "{:02x}".format(initRow).upper()
            # Is this Y0 or Y1?
            ynum = '0' if ramb36 is False or bitOffset % 2 == 0 else '1'
            if parity:
                segfeature = "{}.RAMB18_Y{}.INITP_{}[{:03}]".format(
                    cell.tile[0:6], ynum, initRow,
                    int(bitOffset / 2) if ramb36 else bitOffset
                )
            else:
                segfeature = "{}.RAMB18_Y{}.INIT_{}[{:03}]".format(
                    cell.tile[0:6], ynum, initRow,
                    int(bitOffset / 2) if ramb36 else bitOffset
                )
            segoffset = findSegOffset(
                segl_lines if segfeature.split(".")[0] == "BRAM_L" else
                segr_lines, segfeature
            )
            assert segoffset != "UNKNOWN", "{}".format(segfeature)

            # Finally, print out the mapping if requested
            if mappings or verbose:
                if parity:
                    print(
                        "{} init.mem[{}][{}] ({}) -> {}.{}_Y{}.INITP_{}[{:03}] -> {} {} {} wordoffset = {}"
                        .format(
                            designName, w, b, initbit, cell.tile,
                            cell.type[:-2], ynum, initRow,
                            int(bitOffset / 2) if ramb36 else bitOffset,
                            cell.tile, hex(cell.baseaddr), segoffset,
                            cell.wordoffset
                        )
                    )

                else:
                    print(
                        "{} init.mem[{}][{}] ({}) -> {}.{}_Y{}.INIT_{}[{:03}] -> {} {} {} wordoffset = {}"
                        .format(
                            designName, w, b, initbit, cell.tile,
                            cell.type[:-2], ynum, initRow,
                            int(bitOffset / 2) if ramb36 else bitOffset,
                            cell.tile, hex(cell.baseaddr), segoffset,
                            cell.wordoffset
                        )
                    )
            if check:
                # Compute offsets for frame/bit in bitstream
                # Frame number is tilegrid.json's baseaddr + segbits frame offset number
                frame = cell.baseaddr + int(segoffset.split("_")[0])
                # Bit offset is given in segbits file
                frboffset = int(segoffset.split("_")[1])
                # Word bit will be in will be word offset from tilegrid.json file + bit offset from segbits
                frwd = frames[frame][cell.wordoffset + int(frboffset / 32)]
                # Mask off just the bit we want out of the 32
                # 1. Doing a mod 32 will tell which bit num it is
                # 2. Then, shift over and mask
                frbit = (frwd >> frboffset % 32) & 0x1

            # Check bit in frame data if asked
            # This will use the .bit file read in step 4 above and compare to what is in both the init.mem and FASM files
            if check:
                if verbose:
                    print(
                        "Frame = {:x} frboffset = {} frwd = {} frbit = {}".
                        format(frame, frboffset, frwd, frbit)
                    )
                assert frbit == int(
                    initbit
                ), "initbit: {} != frbit: {}".format(initbit, frbit)

    # If we got here, it worked.
    # So say so if you were asked to...
    if check:
        print(
            "    Cell: {} {} {} all checked out and correct...".format(
                designName, cell.tile, cell.type
            ),
            flush=True
        )


# Given a name, find the segOffset for it
def findSegOffset(segs, segfeature):
    for line in segs:
        #print(line.rstrip())
        if line.split(" ")[0] == segfeature:
            return line.split(" ")[1].rstrip()
    return "UNKNOWN"


# Pad a string to a certain length with 'ch'
def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)


# Read the FASM file and filter out Y0 and Y1 INIT and INITP strings
# for the current cell and put into lists to return.
def readInitStringsFromFASMFile(cell, fasmFile):
    init0lines = []
    init0plines = []
    init1lines = []
    init1plines = []
    with open(fasmFile) as f:
        for line in f.readlines():
            if line.split(".")[0] != cell.tile:
                continue
            if "Y0.INITP" in line:
                init0plines.append(line)
            elif "Y0.INIT" in line:
                init0lines.append(line)
            if "Y1.INITP" in line:
                init1plines.append(line)
            elif "Y1.INIT" in line:
                init1lines.append(line)
    return (init0lines, init0plines, init1lines, init1plines)


# Process the INIT lines one at a time.
# Pad them into 256 character lines and reverse them end to end.
# Return a list of them.
# They should appear in ascending order, this checks that.
# TODO: is it possible to have less than the full count of 64 INIT lines?
#           Yes: see design 512b18.
#       Would an INIT get left out of the FASM file it is was all zeroes?
#           It is possible - but haven't seen this yet since using random data.
#       To be safe, filling out full complement of lines with 0's in the code below.
#       May be overkill but hey...
def processInitLines(initlines, parity):
    inits = []
    for indx, line in enumerate(initlines):
        key = line.split(".")[2].split("_")[1][0:2]
        key = int(key, 16)
        assert key == indx
        val = line.split("'")[1][1:].rstrip()
        val = pad('0', 256, val)[::-1]
        inits.append(val)
    while len(inits) < (8 if parity else 64):
        inits.append("0" * 256)

    return inits
