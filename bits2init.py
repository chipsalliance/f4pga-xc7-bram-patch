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
def bits2init(
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

    # 2. Get the frames
    frames = DbgParser.loadFrames(
        baseDir / "vivado" / "{}.bit".format(designName)
    )

    # 3. Make arrays to hold the new init data
    initArrays = [[None for j in range(initbitwidth)] for k in range(words)]
    initStrings = [None for j in range(words)]

    # 4. Use mappings to take the frame data, and make ordered arrays of data
    print("Assembling init strings for {}".format(designName))
    for mapping in mappings:
        frameWord = int(mapping.frameBitOffset / 32)
        frameBit = mapping.frameBitOffset % 32
        binaryWord = bin(frames[mapping.frameAddr][frameWord])[2:]
        binaryWord = ('0' * (32 - len(binaryWord))) + binaryWord
        binaryWord = binaryWord[::-1]
        initArrays[mapping.word][mapping.bit] = binaryWord[frameBit]
    
    # 5. Combine the arrays into new init strings
    for i in range(words):
        string = "".join(initArrays[i])
        string = string[::-1]
        initStrings[i] = string

    # 5a. Check the new strings against existing .mem files
    # Only checks if the --check flag was set
    if origInitFile is not None:
        print("    Checking with original...")
        origInit = parseutil.parse_init_test.read_initfile(
            origInitFile, initbitwidth, reverse=False
        )
        for w in range(words):
            for b in range(initbitwidth):
                if initStrings[w][b] != origInit[w][b]:
                    print(
                        "Mismatch: {}:{} {} {}".format(
                            w, b, initStrings[w][b], origInit[w][b]
                        )
                    )
                    print("original: {}\nnew: {}".format(hex(int(origInit[w], 2)), hex(int(initStrings[w], 2))))
                    sys.exit(1)
        print("      Everything checked out successfully!!!")
    print("  Done assembling init strings")
    print("Writing to {}/init/new.mem".format(designName))

    # 6. Writes the string to new.mem in the init directory of a design
    with (baseDir / "init" / "new.mem").open('w+') as f:
        for string in initStrings:
            f.write(hex(int(string, 2))[2:])
            f.write("\n")
    print("  Done writing file")


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

    bits2init(
        baseDir, args.memname, baseDir / args.mddname,
        baseDir / "init/fromFasm.mem",
        baseDir / "init/init.mem" if args.check == True else None,
        baseDir / "real.fasm", args.verbose, args.printmappings
    )

    print("")