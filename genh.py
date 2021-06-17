#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

# File: genh.py
# Author: Brent Nelson
# Created: 25 June 2020
# Description:
#    Outputs .h file format

import bitMapping
import pathlib
import argparse
import patch_mem
import os
import json
import parseutil
import parseutil.misc as misc


class Mem:
    def __init__(self, name, words, bits):
        self.name = name
        self.words = words
        self.bits = bits

    def toString(self):
        return "name={}, words={}, bits = {}".format(
            self.name, self.words, self.bits
        )


##############################################################################################
# Create the bitmappings for a design
##############################################################################################
def genh(
    mddName,
    memName,
    words,  # Number of words in init.mem file
    bits,  # Number of bits per word in init.memfile
    verbose,
    printMappings
):
    # 1. Load the MDD file.
    mdd_data = patch_mem.readAndFilterMDDData(mddName, memName)
    # Add some info to the mdd_data
    tilegridname = os.environ["XRAY_DIR"] + "/database/" + os.environ[
        "XRAY_DATABASE"] + "/" + os.environ["XRAY_PART"] + "/tilegrid.json"
    with open(tilegridname) as f:
        tilegrid = json.load(f)

    for m in mdd_data:
        tilegridinfo = tilegrid[m.tile]
        m.baseaddr = int(tilegridinfo["bits"]["BLOCK_RAM"]["baseaddr"], 16)
        m.numframes = int(tilegridinfo["bits"]["BLOCK_RAM"]["frames"])

    # 2. Load the segment data from the prjxray database.
    #    This uses the environment variables set by prjxray
    #    Passing it into createBitMappings() each time will save a lot of time since it can be reused for all
    #       the BRAMs in a design.
    segs = bitMapping.loadSegs()

    # 3. Define the data structure to hold the mappings that are returned.
    #    Format is: [word, bit, tileName, bits (width of each init.mem word), fasmY, fasmINITP, fasmLine, fasmBit, frameAddr, frameBitOffset]
    mappings = []

    # 4. Create the bitmappings for each BRAM Primitive
    if printMappings:
        print("Cell = {}".format(memName))
    for cell in mdd_data:
        mappings = bitMapping.createBitMapping(
            segs,  # The segs info
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

    return (mappings, mdd_data)


# This is the main driver program to generate the .c and .h files
if __name__ == "__main__":

    # Method to figure out if string already in the ranges set
    def inRanges(ranges, s):
        for r in ranges:
            if r == s:
                return True
        return False

    parser = argparse.ArgumentParser()
    parser.add_argument("mddname", help='Name of mdd file to use')
    #parser.add_argument("memname", help='Name of memory')
    parser.add_argument(
        'outfile',
        help='Name root of .h and .c files to write (without extension)'
    )
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument(
        "--extendedoutput",
        help='Print out short mapping record info into .c file',
        action='store_true'
    )
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    # Make a list of the memories in the design and their sizes
    mddMemoryNames = misc.getMDDMemories(args.mddname)
    print("Here are the memories in this design:")
    for m in mddMemoryNames.keys():
        print("     {} = {}".format(m, mddMemoryNames[m]))

    # Now, make 3 parallel lists:  the memory names, the mappings for each memory, the mdd entries for each memory
    # We will loop across those below
    memnamesLst = []
    mappingsLst = []
    mddsLst = []
    for m in mddMemoryNames.keys():
        tmp_mappings, tmp_mdd_data = genh(
            args.mddname, m, int(mddMemoryNames[m][0]),
            int(mddMemoryNames[m][1]), args.verbose, args.printmappings
        )
        mappingsLst.append(tmp_mappings)
        mddsLst.append(tmp_mdd_data)
        memnamesLst.append(m)

    # Now output the .h file
    with open(args.outfile + ".h", 'w') as f:
        f.write('#include "bert_types.h"\n\n')
        f.write('#define NUM_LOGICAL {}\n'.format(len(mddMemoryNames.keys())))
        f.write('\n')
        f.write("// local name for each memory\n")
        for i, m in enumerate(mddMemoryNames.keys()):
            s = m.replace("/", "_")
            f.write('#define {} {}\n'.format(s.upper(), i))

        f.write('\n')

        f.write("extern const char * logical_names[NUM_LOGICAL];\n")
        f.write(
            "extern struct logical_memory logical_memories[NUM_LOGICAL];\n\n"
        )

    # Next, output the .c file
    with open(args.outfile + ".c", "w") as f:
        f.write('#include "bert_types.h"\n\n')
        f.write('#define NUM_LOGICAL {}\n'.format(len(mddMemoryNames.keys())))
        f.write('\n')
        f.write("// local name for each memory\n")
        for i, m in enumerate(mddMemoryNames.keys()):
            s = m.replace("/", "_")
            f.write('#define {} {}\n'.format(s.upper(), i))

        f.write('\n')

        f.write('const char * logical_names[]={\n')
        for i, m in enumerate(mddMemoryNames.keys()):
            if i < len(mddMemoryNames.keys()) - 1:
                f.write("  \"" + "/top/" + m + "\"" + ",\n")
            else:
                f.write("  \"" + "/top/" + m + "\"" + "\n")
        f.write("};\n\n")

        # Loop across each memory to output the needed information
        for i in range(len(mappingsLst)):
            mdd_data = mddsLst[i]
            mappings = mappingsLst[i]
            memname = memnamesLst[i]

            # Figure out the ranges of frames for a given memory
            # Be sure to eliminate duplicates
            numRanges = len(mdd_data)
            ranges = set()
            for m in mdd_data:
                s = "{" + "0x{:08x},{}".format(m.baseaddr, m.numframes) + "}"
                if not inRanges(ranges, s):
                    ranges.add(s)

            # Output those ranges for this memory
            f.write(
                'struct frame_range mem{}_frame_ranges[{}]= \n'.format(
                    i, len(ranges)
                )
            )
            f.write("{\n")
            for j, r in enumerate(ranges):
                if j < len(ranges) - 1:
                    f.write("  " + r + ",\n")
                else:
                    f.write("  " + r + "\n")
            f.write("};\n\n")

            # Output the actual mappings now.  This is taken from the mappings info returned from calling createBitMapping() above.
            # They are output in word/bit order as in word0/bit0, word0/bit1, ..., word1/bit0, word1/bit1, ...
            f.write(
                'struct bit_loc mem{}_bitlocs[{}]='.format(
                    i, mddMemoryNames[memname][0] * mddMemoryNames[memname][1]
                ) + '{\n'
            )
            for j, m in enumerate(mappings):
                if j < len(mappings) - 1:
                    s = '    {' + '0x{:08x}, '.format(
                        m.frameAddr
                    ) + '{:6d}'.format(m.frameBitOffset) + '},'
                    s += ' \t// [{}][{}]'.format(m.word, m.bit)
                    if args.extendedoutput:
                        s += ' \t ' + m.toString()
                else:
                    s = '    {' + '0x{:08x}, '.format(
                        m.frameAddr
                    ) + '{:6d}'.format(m.frameBitOffset) + '},'
                    s += ' \t// [{}][{}]'.format(m.word, m.bit)
                    if args.extendedoutput:
                        s += ' \t' + m.toString()

                f.write(s + "\n")
            f.write("};\n")
            f.write("\n")

        # Finally write the struct info for each memory and be done
        f.write('struct logical_memory logical_memories[NUM_LOGICAL] =\n')
        f.write('{\n')
        for i in range(len(mappingsLst)):
            f.write('   {')
            if i < len(mappingsLst) - 1:
                f.write(
                    '{},{},{},mem{}_frame_ranges,mem{}_bitlocs'.format(
                        len(ranges), mddMemoryNames[memname][1],
                        mddMemoryNames[memname][0], i, i
                    )
                )
                f.write('},')
                s = memnamesLst[i].replace("/", "_")
                f.write('    // {} {}\n'.format(s.upper(), i))
            else:
                f.write(
                    '{},{},{},mem{}_frame_ranges,mem{}_bitlocs'.format(
                        len(ranges), mddMemoryNames[memname][1],
                        mddMemoryNames[memname][0], i, i
                    )
                )
                f.write('}')
                s = memnamesLst[i].replace("/", "_")
                f.write('    // {} {}'.format(s.upper(), i))
        f.write('\n};\n')
