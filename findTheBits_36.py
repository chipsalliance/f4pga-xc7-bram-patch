# File: findTheBits_36.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Will compute bit mappings from init.mem bit locations to FASM INIT/INITP lines/bits
#    If a bit mismatch is found between a given init.mem file and locations in the FASM file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown, all bits match

import os
import glob
import parseutil
import argparse

def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)

def findAllBits(dr, mdd_data, cell, verbose = False, mappings = True):
    fname = dr.split("/")[-1]

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

    # Get all the init lines for this cell, pad them with 0's, and reverse them
    init0s = []
    init0ps = []
    init1s = []
    init1ps = []
    #Sample: BRAM_L_X6Y10.RAMB36_Y0.INIT_3F[240:0] = 241'b10
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

    # Now zip them together into big 512 character lines
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
    
    # Now check if we can find all the bits in this cell
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
                print("Doing: {} {}".format(w, b))
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

            if verbose:
                print("{} {} {} {} {} {}".format(w, b, cell.width, len(init), len(init[w])-1-b, init[w]))  # change
            initbit = init[w][len(init[w])-1-b]
            initRow = int(w / numPerInit)
            wordOffset = int(w % numPerInit)
            bitOffset = wordOffset*bslice + (b - cell.slice_beg - (islice if parity else 0)) 
            if verbose:
                print("FASM initRow = {} bitOffset = {}".format(initRow, bitOffset))

            fasmbit = initps[initRow][bitOffset] if parity else inits[initRow][bitOffset]
            if verbose:
                print("Bit[{}][{}] = {} vs. {}".format(w, b, initbit, fasmbit))
            assert initbit == fasmbit

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
