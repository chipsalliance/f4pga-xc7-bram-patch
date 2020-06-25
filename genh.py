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


##############################################################################################
# Create the bitmappings for a design
##############################################################################################
def genh(
    baseDir,  # The directory where the design lives
    words,  # Number of words in init.mem file
    bits,  # Number of bits per word in init.memfile
    memName,
    mdd,
    verbose,
    printMappings
):
    designName = baseDir.name

    # 1. Load the MDD file.  Note the name is derived from the designName (it is "designName.mdd")
    mddName = "{}.mdd".format(baseDir.name) if mdd is None else mdd
    mdd_data = patch_mem.readAndFilterMDDData(str(baseDir / mddName), memName)
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
    for cell in mdd_data:
        mappings = bitMapping.createBitMapping(
            designName,  # Name of design
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


# The routine createBitMappings() above is intended to be called from other programs which require the mappings.
# This main routine below is designed to test it
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir", help='Directory where design is located.')
    parser.add_argument("words", help='Number of words in memory.')
    parser.add_argument("bits", help='Number of words in memory.')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--memname")
    parser.add_argument("--mddname")
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()

    words = int(args.words)
    bits = int(args.bits)
    memName = "mem/ram" if args.memname is None else args.memname

    mappings, mdd_data = genh(
        baseDir, words, bits, memName, args.mddname, args.verbose,
        args.printmappings
    )

    # Now output the .h file
    print('#include "bert_types.h"\n')
    print('#define NUM_LOGICAL 1')
    print()
    print("// local name for each memory")
    print('#define FOO_MEM 0\n')
    print('const char * logical_names[]={', end='')
    print('"ram/mem"};\n')

    numRanges = len(mdd_data)
    for i, m in enumerate(mdd_data):
        if i == 0:
            ranges = "{" + "0x{:08x},{}".format(m.baseaddr, m.numframes) + "}"
        else:
            ranges += ",{" + "0x{:08x},{}".format(
                m.baseaddr, m.numframes
            ) + "}"

    print(
        'struct frame_range mem0_frame_ranges[{}]='.format(numRanges) + "{" +
        ranges + '};\n'
    )
    print('struct bit_loc mem0_bitlocs[{}]='.format(words * bits) + '{')
    for i, m in enumerate(mappings):
        if i < len(mappings) - 1:
            s = '    {' + '0x{:08x}, '.format(m.frameAddr) + '{}'.format(
                m.frameBitOffset
            ) + '},'
        else:
            s = '    {' + '0x{:08x}, '.format(m.frameAddr) + '{}'.format(
                m.frameBitOffset
            ) + '}'

        print(s)
    print("};")
    print()
    print('struct logical_memory logical_memories[NUM_LOGICAL] =')
    print('{')
    print(' {', end='')
    print(
        '{},{},{},mem0_frame_ranges,mem0_bitlocs'.format(
            numRanges, words, bits
        ),
        end=''
    )
    print('}   // FOO_MEM 0')
    print('};')
