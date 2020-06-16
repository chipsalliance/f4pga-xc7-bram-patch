# File: findTheBits_18.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Works for designs that use only RAMB18 primitives.
#    Will compute mapping from init.mem bit locations to FASM INIT/INITP lines/bits
#    Then will create feature name and find its mapping in segbits file from prjxray database
#    Finally, for each bits prints everything out
#    If a bit mismatch is found between a given init.mem file and locations in the FASM file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown, all bits match

import sys
import os
import glob
import json
import patch_mem
import parseutil
import parseutil.parse_mdd as mddutil
import parseutil.fasmread as fasmutil
import fasm
import argparse

def isInMem(w, b, cell):
    if b < cell.slice_beg or b > cell.slice_end:
        return False
    if w < cell.addr_beg or w > cell.addr_end:
        return False
    return True

def findMem(w, b, cells):
    for cell in cells:
        if isInMem(w, b, cell):
            return cell
    return None

def read_fasm(fname):
    fasm_tuples = fasmutil.get_fasm_tups(fname)
    #TODO: Why are tiles being computed if not being used?
    tiles = fasmutil.get_in_use_tiles(fasm_tuples)
    tiles = fasmutil.get_tile_data(tups=fasm_tuples, in_use=tiles)
    return fasm_tuples

def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)

def findAllBitsInDirs(dirs, verbose = True):
    #dirs = glob.glob("/home/nelson/mempatch/testing/tests/master/*")
    dirs.sort()
    for dr in dirs:
        fname = dr.split("/")[-1]

        # Read the MDD data and filter out the ones we want for this memory
        skip = False
        mdd_data = patch_mem.readAndFilterMDDData(dr + "/{}.mdd".format(fname), "mem/ram")
        for cell in mdd_data:
            if cell.type != "RAMB18E1":
                print("Skipping Cell: {} - it has RAMB36E1 primitive(s)".format(dr))
                skip = True
                break
        if skip:
            continue
       

        # Read the init.mem file for this design
        init = parseutil.parse_init_test.initfile_to_initlist(dr + "/init/init.mem", mdd_data)

        # Read the fasm file for this design and collect the INIT lines, they should be in ascending order
        fasmName = dr+"/real.fasm"
        initlines = []
        initplines = []
        with open(fasmName) as f:
            for line in f.readlines():
                if "Y0.INITP" in line:
                    initplines.append(line)
                elif "Y0.INIT" in line:
                    initlines.append(line)

        #print(fasmName)
        #print(initlines)
        #print(initplines)
        # Process each BRAM primitive in the MDD
        for cell in mdd_data:
            # Get all the init lines for this cell, pad them with 0's, and reverse them
            inits = []
            initps = []
            #BRAM_L_X6Y10.RAMB18_Y0.INIT_3F[240:0] = 241'b10
            i = 0
            for line in initlines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                inits.append(val)
                i += 1
            i = 0
            for line in initplines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                initps.append(val)
                i += 1

            # Now check if we can find all the bits in this cell
            # First, load the segbits database info
            segname = os.environ["XRAY_DIR"] + "/database/" + os.environ["XRAY_DATABASE"] + "/segbits_{}.block_ram.db".format(cell.tile[0:6].lower())
            with open(segname) as sf:
                segs = sf.readlines()
                for w in range(cell.addr_beg, cell.addr_beg + len(init)):
                    for b in range(cell.slice_beg, cell.slice_end+1):
                        bwid = cell.slice_end - cell.slice_beg + 1
                        wdep = cell.addr_end - cell.addr_beg + 1
                        rwid = cell.width
                        pwid = cell.pbits
                        dwid = cell.dbits
                        if bwid != dwid+pwid:
                            print("     ERROR: {} {} {} {}".format(bwid, rwid, pwid, dwid))
                            continue
                        islice = 32 if rwid == 36 else 16 if rwid == 18 else 8 if rwid == 9 else rwid
                        pslice =  4 if rwid == 36 else  2 if rwid == 18 else 1 if rwid == 9 else 0
                        if verbose:
                            print("Doing: {} {}".format(w, b))
                            print("{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT".format(bwid, pwid, pslice, dwid, islice), end='')
                            print("    {} {} ({}) {}:{} {}.{}".format(
                                cell.type,
                                cell.write_style,
                                cell.width,
                                cell.addr_end,
                                cell.addr_beg,
                                cell.slice_end,
                                cell.slice_beg,
                                )
                            )
                            print("    This is the correct BRAM block iff: {} >= r >= {} and {} >= b >= {}".format(
                                cell.addr_end,
                                cell.addr_beg,
                                cell.slice_end,
                                cell.slice_beg,
                            )
                        )


                        # Some sanity checks
                        assert islice * wdep == 16384
                        if pslice != 0:
                            assert pslice * wdep == 2048


                        # Is the bit in the INIT?
                        if b - cell.slice_beg < islice: 
                            bslice = islice
                            parity = False
                        else:
                            bslice = pslice  
                            parity = True
                        numPerInit = (256/bslice)  
                        assert int(numPerInit) == numPerInit
                        #print("    INIT row # =  w / {}".format(numPerInit))    # print INITP
                        #print("    Word offset = w % {}".format(numPerInit))
                        #print("    Bit offset in word = b - {}".format(cell.slice_end))
                        #print("{} {} {} {} {} {}".format(w, cell.width-1-b, len(init), len(init[w]), init[w], init[0][17]))
                        initbit = init[w][cell.width-1-b]
                        initRow = int(w / numPerInit)
                        wordOffset = int(w % numPerInit)
                        bitOffset = wordOffset*bslice + (b - cell.slice_beg - (islice if parity else 0)) 
                        if verbose:
                            print("{} {}".format(initRow, bitOffset))
                        #print(inits)
                        fasmbit = initps[initRow][bitOffset] if parity else inits[initRow][bitOffset]
                        if verbose:
                            print("Bit[{}][{}] = {} vs. {}".format(w, b, initbit, fasmbit))
                        assert initbit == fasmbit

                        #BRAM_L_X6Y10.RAMB18_Y0.INIT_3F[240:0] = 241'b10

                        # Now look it up in the segbits file
                        initRow = "{:02x}".format(initRow).upper()
                        if parity:
                            segfeature = "{}.{}_Y0.INITP_{}[{:03}]".format(cell.tile[0:6], cell.type[:-2], initRow, bitOffset)
                        else:
                            segfeature = "{}.{}_Y0.INIT_{}[{:03}]".format(cell.tile[0:6], cell.type[:-2], initRow, bitOffset)
                        segoffset = findSegOffset(segs, segfeature)
                        assert segoffset != "UNKNOWN"

                        if verbose:
                            if parity:
                                print("{} init.mem[{}][{}] -> {}.{}_Y0.INITP_{}[{:03}] -> {}".format(fname, w, b, cell.tile[0:6], cell.type[:-2], initRow, bitOffset, segoffset))
                            else:
                                print("{} init.mem[{}][{}] -> {}.{}_Y0.INIT_{}[{:03}] -> {}".format(fname, w, b, cell.tile[0:6], cell.type[:-2], initRow, bitOffset, segoffset))
        # Must have worked if we got here
        print("Cell: {} {} {} all checked out...".format(fname, cell.tile, cell.type), flush=True)

def findSegOffset(segs, segfeature):
    for line in segs:
        #print(line.rstrip())
        if line.split(" ")[0] == segfeature:
            return line.split(" ")[1]
    return "UNKNOWN"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()

    dirs = []
    dirs.append(args.baseDir)

    # Works for a single design given its directory
    findAllBitsInDirs(dirs, args.verbose)

