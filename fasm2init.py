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
def fasm2init(
    baseDir,  # pathlib.Path
    memName,  # str
    mdd,  # pathlib.Path
    initFile,  # pathlib.Path  
    origInitFile,  # if not None then will do checking between it and re-created initFile on the previous line
    fasmFile,  # pathlib.Path
    verbose,  # bool
    printmappings  # bool
):
    designName = baseDir.name

    # 0. Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(mdd, memName)
    words, initbitwidth = misc.getMDDMemorySize(mdd_data)

    # 1. Get the mapping info
    print("Loading mappings for {}...".format(designName))
    mappings = bitMapping.createBitMappings(
        baseDir,  # The directory where the design lives
        memName,
        mdd,
        False,
        printmappings
    )
    print("  Done loading mappings")

    # 2. Read the fasm file for this cell and collect the INIT/INITP lines
    init0lines, init0plines, init1lines, init1plines = misc.readInitStringsFromFASMFile(
        fasmFile
    )

    newInitBits = [[None for j in range(initbitwidth)] for k in range(words)]
    # 3. Handle each cell
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
        print("      Everything checked out successfully!!!")

    # 6. Finally, write it out
    with initFile.open('w') as f:
        for lin in newInitFile:
            f.write(lin[::-1] + "\n")

    # 7. If we got here we were successful
    print("      Initfile {} re-created successfully!".format(initFile))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument(
        "memname", help='Name of memory to check (as in "mem/ram")'
    )
    parser.add_argument("mddname", help='Name of mdd file)')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--check", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    designName = baseDir.name

    fasm2init(
        baseDir, args.memname, baseDir / args.mddname,
        baseDir / "init/fromFasm.mem",
        baseDir / "init/init.mem" if args.check == True else None,
        baseDir / "real.fasm", args.verbose, args.printmappings
    )

    print("")

#################################################################################################################
# fasm2init.py will take a .fasm file and re-create a new init.mem-type file from them.
# It deposits the new file into baseDir/init/fromFasm.mem
# If the --check flag is true it will compare what it constructs against the values from baseDir/init/init.mem (used mainly for testing)
#    If there is a mismatch it will print out an error message.
# A typical run of this program is:
#    python fasm2init.py testing/tests/master/128b1 mem/ram 128b1.mdd
# Or, you could do:
#    python fasm2init.py testing/tests/master/128b1 mem/ram 128b1.mdd --check
# The only difference is the second one does the check against baseDir/init/init.mem.
#################################################################################################################
