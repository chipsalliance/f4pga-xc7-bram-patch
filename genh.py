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


# Return a dict mapping names to [words, bits] lists
def getMDDMemories(mddName):
    mdd = parseutil.parse_mdd.read_mdd(mddName)
    lst = dict()
    for m in mdd:
        s = '/'.join(m.cell_name.split('/')[:-1]) + '/' + m.ram_name
        if s not in lst.keys():
            lst[s] = [int(m.addr_end) + 1, int(m.slice_end) + 1]
        else:
            itm = lst[s]
            wb = [0, 0]
            wb[0] = max(itm[0], int(m.addr_end) + 1)
            wb[1] = max(itm[1], int(m.slice_end) + 1)
            lst[s] = wb
    return lst


# The routine createBitMappings() above is intended to be called from other programs which require the mappings.
# This main routine below is designed to test it
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mddname", help='Name of mdd file to use')
    parser.add_argument("memname", help='Name of memory')
    parser.add_argument(
        'outfile',
        help='Name root of .h and .c files to write (without extension)'
    )
    parser.add_argument("words", help='Number of words in memory.')
    parser.add_argument("bits", help='Number of words in memory.')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    words = int(args.words)
    bits = int(args.bits)

    # Next 4 lines unused
    # The problem with the next 4 lines is that for small memories, Vivado doesn't tell us the correct size,
    # Example: for anything shallower than 1k, it gives the depth as 1024
    # Will need to come up with something to address this before doing all memories in one design.
    # Get list of .mdd file memory names
    mddMemoryNames = getMDDMemories(args.mddname)
    #for m in mddMemoryNames.keys():
    #    print("   {} = {}".format(m, mddMemoryNames[m]))

    mappings, mdd_data = genh(
        args.mddname, args.memname, words, bits, args.verbose,
        args.printmappings
    )

    # Now output the .h file
    with open(args.outfile + ".h", 'w') as f:
        f.write('#include "bert_types.h"\n\n')
        f.write('#define NUM_LOGICAL 1\n')
        f.write('\n')
        f.write("// local name for each memory\n")
        s = args.memname.replace("/", "_")
        f.write('#define {} 0\n\n'.format(s.upper()))

        f.write("extern const char * logical_names[NUM_LOGICAL];\n")
        f.write(
            "extern struct logical_memory logical_memories[NUM_LOGICAL];\n\n"
        )

    with open(args.outfile + ".c", "w") as f:
        f.write('#include "bert_types.h"\n\n')
        f.write('#define NUM_LOGICAL 1\n')
        f.write('\n')
        f.write("// local name for each memory\n")
        s = args.memname.replace("/", "_")
        f.write('#define {} 0\n\n'.format(s.upper()))
        f.write('const char * logical_names[]={')
        mname = "\"" + "/top/" + args.memname + "\"" + "};\n\n"
        f.write(mname)

        numRanges = len(mdd_data)
        for i, m in enumerate(mdd_data):
            if i == 0:
                ranges = "{" + "0x{:08x},{}".format(
                    m.baseaddr, m.numframes
                ) + "}"
            else:
                ranges += ",{" + "0x{:08x},{}".format(
                    m.baseaddr, m.numframes
                ) + "}"

        f.write(
            'struct frame_range mem0_frame_ranges[{}]='.format(numRanges) +
            "{" + ranges + '};\n\n'
        )
        f.write(
            'struct bit_loc mem0_bitlocs[{}]='.format(words * bits) + '{\n'
        )
        for i, m in enumerate(mappings):
            if i < len(mappings) - 1:
                s = '    {' + '0x{:08x}, '.format(m.frameAddr) + '{}'.format(
                    m.frameBitOffset
                ) + '},'
            else:
                s = '    {' + '0x{:08x}, '.format(m.frameAddr) + '{}'.format(
                    m.frameBitOffset
                ) + '}'

            f.write(s + "\n")
        f.write("};\n")
        f.write("\n")
        f.write('struct logical_memory logical_memories[NUM_LOGICAL] =\n')
        f.write('  {\n')
        f.write('   {')
        f.write(
            '{},{},{},mem0_frame_ranges,mem0_bitlocs'.format(
                numRanges, words, bits
            )
        )
        f.write('  }   ')
        s = args.memname.replace("/", "_")
        f.write('// {} 0\n'.format(s.upper()))
        f.write('};\n')
