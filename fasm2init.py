# File: fasm2Init.py
# Author: Brent Nelson
# Created: 25 June 2020
# Description:
#    Will convert a FASM file for a memory to the equivalent init.mem file
#    Will compare it to the original

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
def fasm2init(
    baseDir,  # pathlib.Path
    memName,  # str
    mdd,  # pathlib.Path
    words,
    initbitwidth,  # int
    initFile,  # pathlib.Path
    origInitFile,
    fasmFile,  # pathlib.Path
    verbose,  # bool
    printmappings  # bool
):

    designName = baseDir.name

    # 0. Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(mdd, memName)

    # 1. Get the mapping infols /
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

    # 2. Read the fasm file for this cell and collect the INIT/INITP lines
    init0lines, init0plines, init1lines, init1plines = readInitStringsFromFASMFile(
        fasmFile
    )

    newInitBits = [[None for j in range(initbitwidth)] for k in range(words)]
    # 3. Handle each cell
    for cell in mdd_data:
        # inits will be indexed as inits[y01][initinitp]
        inits = [[None for j in range(2)] for k in range(2)]

        # Convert the FASM lines into the proper format strings
        # Store them in a multi-dimensional array indexed by y01 and INITP/INIT (True/False)
        inits[0][False] = processInitLines("0s", init0lines, cell, False)
        inits[0][True] = processInitLines("0ps", init0plines, cell, True)
        inits[1][False] = processInitLines("1s", init1lines, cell, False)
        inits[1][True] = processInitLines("1ps", init1plines, cell, True)

        for w in range(words):
            for b in range(initbitwidth):
                if w < cell.addr_beg or w > cell.addr_end:
                    continue
                if b < cell.slice_beg or b > cell.slice_end:
                    continue

                # Get the bit from the FASM line
                mapping = bitMapping.findMapping(w, b, initbitwidth, mappings)
                assert mapping is not None, "{} {} {}".format(
                    w, b, initbitwidth
                )
                # Now get the actual bit
                fasmbit = inits[mapping.fasmY][mapping.fasmINITP][
                    mapping.fasmLine][mapping.fasmBit]

                # Put the bit into the array
                newInitBits[w][b] = fasmbit

    # 4. Now, create real init array
    newInitFile = []
    for w in range(words):
        wd = ""
        for b in range(initbitwidth):
            if newInitBits[w][b] is None:
                print("ERROR: None at {}:{}".format(w, b))
            else:
                wd += newInitBits[w][b]
        newInitFile.append(wd[::-1])  # Don't forget to reverse it

    # 5. Do checking if asked
    if origInitFile is not None:
        print("    Checking with original...")
        origInit = parseutil.parse_init_test.read_initfile(
            origInitFile, initbitwidth, reverse=False
        )
        for w in range(words):
            for b in range(initbitwidth):
                if newInitFile[w][b] != origInit[w][b]:
                    print(
                        "Mismatch: {}:{} {} {}".format(
                            w, b, newInitFile[w][b], origInit[w][b]
                        )
                    )
                    sys.exit(1)

    # 6. Finally, write it out
    with initFile.open('w') as f:
        for lin in newInitFile:
            f.write(lin[::-1] + "\n")

    # 7. If we got here we were successful
    print("      Initfile re-created successfully!")


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

    parser.add_argument("words", help='Number of words in memory')

    parser.add_argument("bits", help='Width of each word of memory')

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

    fasm2init(
        baseDir, args.memname, baseDir / "{}.mdd".format(designName),
        int(args.words), int(args.bits), baseDir / "init/fromFasm.mem",
        baseDir / "init/init.mem", baseDir / "real.fasm", args.verbose,
        args.printmappings
    )

    print("")
