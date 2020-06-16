# File: findTheBits_36.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Works for designs that use only RAMB35 primitives.
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


def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)

def findAllBitsInDirs(dirs, verbose, mappings):
    dirs.sort()
    for dr in dirs:
        fname = dr.split("/")[-1]

        # Read the MDD data and filter out the ones we want for this memory
        skip = False
        mdd_data = patch_mem.readAndFilterMDDData(dr + "/{}.mdd".format(fname), "mem/ram")
        for cell in mdd_data:
            if cell.type != "RAMB36E1":
                print("Skipping Cell: {} - it has RAMB18E1 primitive(s)".format(dr))
                skip = True
                break
        if skip:
            continue
       
        print("Design: {}".format(fname))
        # Read the init.mem file for this design
        init = parseutil.parse_init_test.initfile_to_initlist(dr + "/init/init.mem", mdd_data)

        # Read the fasm file for this design and collect the INIT lines, they should be in ascending order
        fasmName = dr+"/real.fasm"
        init0lines = []
        init0plines = []
        init1lines = []
        init1plines = []
        with open(fasmName) as f:
            for line in f.readlines():
                if "Y0.INITP" in line:
                    init0plines.append(line)
                elif "Y0.INIT" in line:
                    init0lines.append(line)
                if "Y1.INITP" in line:
                    init1plines.append(line)
                elif "Y1.INIT" in line:
                    init1lines.append(line)

        # Now combine the INIT lines
        initlines = []
        initplines= []
        #print(fasmName)
        #print(initlines)
        #print(initplines)
        # Process each BRAM primitive in the MDD
        for cell in mdd_data:
            # Get all the init lines for this cell, pad them with 0's, and reverse them
            init0s = []
            init0ps = []
            init1s = []
            init1ps = []
            #BRAM_L_X6Y10.RAMB18_Y0.INIT_3F[240:0] = 241'b10
            i = 0
            for line in init0lines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                init0s.append(val)
                i += 1
            i = 0
            for line in init0plines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                init0ps.append(val)
                i += 1
            i = 0
            for line in init1lines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                init1s.append(val)
                i += 1
            i = 0
            for line in init1plines:
                if line.split(".")[0] != cell.tile:
                    continue
                key = line.split(".")[2].split("_")[1][0:2]
                key = int(key, 16)
                assert key == i
                val = line.split("'")[1][1:].rstrip()
                val = pad('0', 256, val)[::-1]
                init1ps.append(val)
                i += 1

            # Now zip them together
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

            if verbose:
                print(init0s[0])
                print("")
                print(init1s[0])
                print("")
                print("Inits: {}".format(inits[0]))

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
                    islice = 64 if rwid == 72 else 32 if rwid == 36 else 16 if rwid == 18 else 8 if rwid == 9 else rwid
                    pslice =  8 if rwid == 72 else 4 if rwid == 36 else  2 if rwid == 18 else 1 if rwid == 9 else 0
                    if verbose:
                        print("\nDoing: {} {}".format(w, b))
                        print("{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT".format(bwid, pwid, pslice, dwid, islice), end='')
                        print("   {} {} {} ({}) {}:{} {}.{}".format(
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
                        print("    This is the correct BRAM block iff: {} >= r >= {} and {} >= b >= {}".format(
                            cell.addr_end,
                            cell.addr_beg,
                            cell.slice_end,
                            cell.slice_beg,
                        )
                    )
                    # Some sanity checks
                    assert islice * wdep == 32768
                    if pslice != 0:
                        assert pslice * wdep == 4096
                    # Is the bit in the INIT?
                    if b - cell.slice_beg < islice: 
                        bslice = islice
                        parity = False
                    else:
                        bslice = pslice  
                        parity = True
                    numPerInit = (512/bslice)  
                    assert int(numPerInit) == numPerInit
                    #print("    INIT row # =  w / {}".format(numPerInit))    # print INITP
                    #print("    Word offset = w % {}".format(numPerInit))
                    #print("    Bit offset in word = b - {}".format(cell.slice_end))
                    if verbose:
                        print("{} {} {} {} {} {}".format(w, b, cell.width, len(init), len(init[w])-1-b, init[w]))  # change
                    initbit = init[w][len(init[w])-1-b]        # change
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
                    if mappings or verbose:
                        if parity:
                            print("{} init.mem[{}][{}] -> {}.{}_Y{}.INITP_{}[{:03}]".format(
                                fname, 
                                w, 
                                b, 
                                cell.tile[0:6], 
                                cell.type[:-2], 
                                '0' if bitOffset%2 == 0 else '1',  # change
                                initRow, 
                                int(bitOffset/2)  # change
                                )
                            )
                        else:
                            print("{} init.mem[{}][{}] -> {}.{}_Y{}.INIT_{}[{:03}]".format(
                                fname, 
                                w, 
                                b, 
                                cell.tile[0:6], 
                                cell.type[:-2], 
                                '0' if bitOffset%2 == 0 else '1',  # change
                                initRow, 
                                int(bitOffset/2)   # change
                                )
                            )
        # Must have worked if we got here
        print("Cell: {} {} {} all checked out...".format(fname, cell.tile, cell.type), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir")
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--nomappings", action='store_true')
    
    args = parser.parse_args()

    dirs = []
    dirs.append(args.baseDir)

    # Works for a single design given its directory
    findAllBitsInDirs(dirs, args.verbose, not args.nomappings)

