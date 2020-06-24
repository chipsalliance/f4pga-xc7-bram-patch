# File: findTheBits_18.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Will compute bit mappings from init.mem bit locations to FASM INIT/INITP lines/bits
#    If a bit mismatch is found between a given init.mem file and locations in the FASM file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown because all bits matched.

import os
import sys
import glob
import parseutil
import argparse
import json
import pathlib
import struct
import DbgParser
import patch_mem

class Mapping:
    def __init__(self, word, bit, fasmY, fasmINITP, fasmLine, fasmBit, frameAddr, frameBitOffset):
        self.word = word
        self.bit = bit
        self.fasmY = fasmY
        self.fasmINITP = fasmINITP
        self.fasmLine = fasmLine
        self.fasmBit = fasmBit
        self.frameAddr = frameAddr
        self.frameBitOffset = frameBitOffset
    def toString(self):
        return "word={}, bit={}, fasmY={}, fasmINITP={}, fasmLine={}, fasmBit={}, frameAddr={:x}, frameBitOffset={}".format(
            self.word, self.bit, self.fasmY, self.fasmINITP, self.fasmLine, self.fasmBit, self.frameAddr, self.frameBitOffset)

def createBitMappings(
    designName, words, bits, mdd_data, cell, verbose, printMappings
):

    # Flag of whether this is RAMB36E cell or not
    ramb36 = (cell.type == "RAMB36E1")


    # Step 1: Read the segbits database information for later use.  Also find record in tilegrid.json
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

    # Step 2: Initialize data structure to return
    mappings = []

    # Step 3: Now build the mappings
    for w in range(words):
        for b in range(bits):
            # Just do the locations covered by this RAMB primitive
            if w < cell.addr_beg or w > cell.addr_end or b < cell.slice_beg or b > cell.slice_end:
                continue

            # Compute characteristics of this particular RAMB primitive
            RAMBwidth = cell.slice_end - cell.slice_beg + 1
            RAMBdepth = cell.addr_end - cell.addr_beg + 1
            RAMBreadwidth = cell.width
            RAMBparitywidth = cell.pbits
            RAMBdatawidth = cell.dbits
            assert RAMBwidth == RAMBdatawidth + RAMBparitywidth, "RAMBwidth ERROR: {} {} {} {}".format(
                        RAMBwidth, RAMBreadwidth, RAMBparitywidth, RAMBdatawidth
                    )

            # Determine how many bits are in parity and how many are in the "normal" bits
            if not ramb36:
                assert not RAMBreadwidth == 72
            initSliceWidth = 64 if RAMBreadwidth == 72 else 32 if RAMBreadwidth == 36 else 16 if RAMBreadwidth == 18 else 8 if RAMBreadwidth == 9 else RAMBreadwidth
            initpSliceWidth = 8 if RAMBreadwidth == 72 else 4 if RAMBreadwidth == 36 else 2 if RAMBreadwidth == 18 else 1 if RAMBreadwidth == 9 else 0

            if verbose:
                print("Doing: {} {}".format(w, b))
                print(
                    "{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT"
                    .format(RAMBwidth, RAMBparitywidth, initpSliceWidth, RAMBdatawidth, initSliceWidth),
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
            assert initSliceWidth * RAMBdepth == (32768 if ramb36 else 16384)
            assert initpSliceWidth == 0 or initpSliceWidth * RAMBdepth == (4096 if ramb36 else 2048)

            # Is the bit of interest in the INIT portion or the INITP portion?
            if b - cell.slice_beg < initSliceWidth:
                # In the INIT portion
                sliceWidth = initSliceWidth
                parity = False
            else:
                # In the INITP portion
                sliceWidth = initpSliceWidth
                parity = True

            # Compute how many "words" fit into each INIT string.
            # This may be the width of the memory or it may not since
            # Vivado often pads.  Example: for a 128b1 the "read width" is 18.
            # That means the memory has a 16-bit word in the INIT and a 2-bit word in the INITP.
            # In the INIT there are 15 0's as padding + the 1 bit of data.  The INITP is all 0's in this case.
            initStringLen = 512 if ramb36 else 256

            # How many words are in each INIT and INITP string?
            numWordsPerInit = (initStringLen / sliceWidth)
            # Make sure it divides evenly or there must be a problem
            assert int(numWordsPerInit) == numWordsPerInit

            if verbose:
                print(
                    "{} {} {} {} {} {}".format(
                        w, b, cell.width, len(initMemContents),
                        len(initMemContents[w]) - 1 - b, initMemContents[w]
                    )
                )

            # Compute where to find the bit in the INIT strings
            # Find which INIT or INITP entry it is in (00-3F for INIT, 00-07 for INITP)
            initRow = int(w / numWordsPerInit)

            # Now, compute the actual bit offset into that INIT or INITP string
            wordOffset = int(w % numWordsPerInit)
            bitOffset = wordOffset * sliceWidth + (
                b - cell.slice_beg - (initSliceWidth if parity else 0)
            )
            if verbose:
                print(
                    "FASM initRow = {} bitOffset = {}".format(
                        initRow, bitOffset
                    )
                )

            # Now, look up the actual frame/bit numbers from the
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

            # Compute the bitstream location of the bit
            # Frame number is tilegrid.json's baseaddr + segbits frame offset number
            frameNum = cell.baseaddr + int(segoffset.split("_")[0])
            # Bit offset is given in segbits file
            frameBitOffset = int(segoffset.split("_")[1]) + cell.wordoffset*32

            # Print out the mapping if requested
            if printMappings or verbose:
                if parity:
                    print(
                        "{} init.mem[{}][{}] -> {}.{}_Y{}.INITP_{}[{:03}] -> {} {} {} wordoffset = {}"
                        .format(
                            designName, w, b, cell.tile,
                            cell.type[:-2], ynum, initRow,
                            int(bitOffset / 2) if ramb36 else bitOffset,
                            cell.tile, hex(cell.baseaddr), segoffset,
                            cell.wordoffset
                        )
                    )

                else:
                    print(
                        "{} init.mem[{}][{}] -> {}.{}_Y{}.INIT_{}[{:03}] -> {} {} {} wordoffset = {}"
                        .format(
                            designName, w, b, cell.tile,
                            cell.type[:-2], ynum, initRow,
                            int(bitOffset / 2) if ramb36 else bitOffset,
                            cell.tile, hex(cell.baseaddr), segoffset,
                            cell.wordoffset
                        )
                    )

            # Finally, build Mapping object to eventually be returned
            # Elements are: word, bit, fasmY, fasmINITP, fasmLine, fasmBit, frameAddr, frameBitOffset
            mappings.append(
                Mapping(
                    w, 
                    b, 
                    ynum, 
                    parity, 
                    initRow, 
                    int(bitOffset / 2) if ramb36 else bitOffset,
                    frameNum, 
                    frameBitOffset
                )
            )

    if verbose:
        for m in mappings:
            print(m.toString())

    return mappings


# Given a name, find the segOffset for it
def findSegOffset(segs, segfeature):
    for line in segs:
        #print(line.rstrip())
        if line.split(" ")[0] == segfeature:
            return line.split(" ")[1].rstrip()
    return "UNKNOWN"

# The routine createBitMappings() above is intended to be called from other programs which require the mappings.
# This main routine below is designed to test it
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design is located.'
    )
    parser.add_argument(
        "words", help='Number of words in memory.'
    )
    parser.add_argument(
        "bits", help='Number of words in memory.'
    )
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir)
    baseDir = baseDir.resolve()

    mdd_data = patch_mem.readAndFilterMDDData(
        str(baseDir / "{}.mdd".format(baseDir.name)), "mem/ram"
    )

    # words, bits, mdd_data, cell, verbose, mappings

    for cell in mdd_data:
        mappings = createBitMappings(
            baseDir.name,
            int(args.words), 
            int(args.bits), 
            mdd_data,
            cell,
            args.verbose, 
            args.printmappings
        )
        # Since this is a test program, print out what was returned
        print("\nFor cell: {} ({})".format(cell.tile, cell.type))
        for m in mappings:
            print(" {}".format(m.toString()))
    print("")
