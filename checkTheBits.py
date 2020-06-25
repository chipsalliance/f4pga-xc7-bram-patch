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
import argparse
import json
import pathlib
import struct
import DbgParser
import bitMapping
import patch_mem
import re


# Check the bits for a complete memory
def checkTheBits(
    baseDir,  # pathlib.Path
    memName,  # str
    mdd,  # pathlib.Path
    initbitwidth,  # int
    initFile,  # pathlib.Path
    fasmFile,  # pathlib.Path
    verbose,  # bool
    printmappings  # bool
):

    designName = baseDir.name

    # 0. Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(mdd, memName)

    # 1. Read the init.mem file for this design
    # Put the contents into an array of strings
    initMemContents = parseutil.parse_init_test.read_initfile(
        initFile, initbitwidth
    )
    #print(initMemContents)
    words = len(initMemContents)

    # 2. Get the mapping infols /
    print("Loading mappings for {}...".format(designName))
    mappings = bitMapping.createBitMappings(
        baseDir,  # The directory where the design lives
        words,  # Number of words in init.mem file
        initbitwidth,  # Number of bits per word in init.memfile
        memName,
        False,
        printmappings
    )
    print("  Done loading mappings")
    #i = 0
    #for m in mappings:
    #    print(m.toString())
    #    i += 1
    #    if i > 8:
    #        break
    #for m in mappings:
    #    print(m.toString())

    # 3. Load up the bit file
    frames = DbgParser.loadFrames(
        baseDir / "vivado" / "{}.bit".format(designName)
    )

    # 4. Read the fasm file for this cell and collect the INIT/INITP lines
    init0lines, init0plines, init1lines, init1plines = readInitStringsFromFASMFile(
        fasmFile
    )

    # 5. Check each cell
    for cell in mdd_data:
        # Convert the FASM lines into the proper format strings
        init0s = processInitLines("0s", init0lines, cell, False)
        init0ps = processInitLines("0ps", init0plines, cell, True)
        init1s = processInitLines("1s", init1lines, cell, False)
        init1ps = processInitLines("1ps", init1plines, cell, True)

        for w in range(words):
            for b in range(initbitwidth):
                if w < cell.addr_beg or w > cell.addr_end:
                    continue
                if b < cell.slice_beg or b > cell.slice_end:
                    continue

                # Get the bit from the memory
                initbit = initMemContents[w][b]
                #print("xxx {} {}".format(w, cell.width-1-b))
                #print(initMemContents[w])

                # Get the bit from the FASM line
                #print("Hi: {} {} {}".format(w, b, bits))
                mapping = bitMapping.findMapping(w, b, initbitwidth, mappings)
                assert mapping is not None, "{} {} {}".format(
                    w, b, initbitwidth
                )
                if mapping.fasmY == 0 and mapping.fasmINITP == True:
                    #print("0ps")
                    fasmbit = init0ps[mapping.fasmLine][mapping.fasmBit]
                elif mapping.fasmY == 1 and mapping.fasmINITP == True:
                    #print("1ps")
                    fasmbit = init1ps[mapping.fasmLine][mapping.fasmBit]
                elif mapping.fasmY == 0 and mapping.fasmINITP == False:
                    #print("\n0s {}".format(init0s[mapping.fasmLine]))
                    fasmbit = init0s[mapping.fasmLine][mapping.fasmBit]
                else:
                    #print("\n1s {}".format(init1s[mapping.fasmLine]))
                    fasmbit = init1s[mapping.fasmLine][mapping.fasmBit]

                #print("*** " + mapping.toString())
                #print("### {} {} {} {}".format(w, b, mapping.fasmLine, mapping.fasmBit))

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
                #print("{}:{}".format(w, b))
                #print(mapping.toString())
                assert fasmbit == initbit, "initbit: {} != fasmbit: {} ({}:{} {} {} \n   {})".format(
                    initbit, fasmbit, w, b, initMemContents[w], initbitwidth,
                    mapping.toString()
                )
                assert frbit == int(
                    initbit
                ), "initbit: {} != bitstream bit: {}".format(initbit, frbit)

        # If we got here, it worked.
        # So say so if you were asked to...
        print(
            "    Cell: {} {} {} all checked out and correct!".format(
                designName, cell.tile, cell.type
            ),
            flush=True
        )


# Pad a string to a certain length with 'ch'
def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)


# Read the FASM file and filter out Y0 and Y1 INIT and INITP strings
# for the current cell and put into lists to return.
def readInitStringsFromFASMFile(fasmFile):
    init0lines = []
    init0plines = []
    init1lines = []
    init1plines = []
    with fasmFile.open() as f:
        for line in f.readlines():
            #if line.split(".")[0] != cell.tile:
            #    continue
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
def processInitLines(typ, initlines, cell, parity):
    if len(initlines) == 0:
        return []
    inits = []
    indx = 0
    for line in enumerate(initlines):
        lin = line[1].rstrip()
        if lin.split(".")[0] != cell.tile:
            continue
        key = lin.split(".")[2].split("_")[1][0:2]
        val = lin.split("=")[1][6:]
        key = int(key, 16)
        assert key == indx, "key={} indx={} line={}".format(key, indx, line)
        val = pad('0', 256, val)[::-1]
        #print(key)
        #print(val)
        #print(typ)
        inits.append(val)
        indx += 1
    while len(inits) < (8 if parity else 64):
        inits.append("0" * 256)
    return inits


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument("bits", help='Width of each word of memory')

    parser.add_argument(
        "memname", help='Name of memory to check (as in "mem/ram")'
    )

    parser.add_argument("--design")

    parser.add_argument("--verbose", action='store_true')

    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )

    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    designName = baseDir.name

    checkTheBits(
        baseDir, args.memname, baseDir / "{}.mdd".format(designName),
        int(args.bits), baseDir / "init/init.mem", baseDir / "real.fasm",
        args.verbose, args.printmappings
    )

    print("")
