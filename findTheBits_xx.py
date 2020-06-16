# File: findTheBits_18.py
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

# Read the FASM file and filter out Y0 and Y1 INIT and INITP strings and put into lists to return
def collectInitStrings(cell, fasmFile):
        init0lines = []
        init0plines = []
        init1lines = []
        init1plines = []
        with open(fasmFile) as f:
            for line in f.readlines():
                if line.split(".")[0] != cell.tile:
                    continue
                if "Y0.INITP" in line:
                    init0plines.append(line)
                elif "Y0.INIT" in line:
                    init0lines.append(line)
                if "Y1.INITP" in line:
                    init1plines.append(line)
                elif "Y1.INIT" in line:
                    init1lines.append(line)
        return(init0lines, init0plines, init1lines, init1plines)

# Read the INIT lines one at a time
# Pad them into 256 character lines and reverse them end to end
# Return a list of them
def processInitLines(cell, initlines):
    inits = []
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
    return inits


def findAllBits(designName, mdd_data, cell, initFile, fasmFile, verbose=False, mappings=True):

    # Flag of whether this is RAMB36E cell or not
    r36 = cell.type == "RAMB36E1"

    # Step 1: Read the init.mem file for this design
    init = parseutil.parse_init_test.initfile_to_initlist(
        initFile, mdd_data
    )
    # Step 2: Read the fasm file for this design and collect the INIT lines, they should be in ascending order
    if r36:
        # Get all the INIT lines
        init0lines, init0plines, init1lines, init1plines = collectInitStrings(cell, fasmFile)

        # Convert those into the proper format strings
        init0s = processInitLines(cell, init0lines)
        init0ps = processInitLines(cell, init0plines)
        init1s = processInitLines(cell, init1lines)
        init1ps = processInitLines(cell, init1plines)

        # Now zip them together into big 512 character lines
        # That is, the even characters will come from Y0 and the odd from Y1
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
    else: # !r36
        # Get all the INIT lines
        # Only the init0 and init0p should have anything since this is a RAMB18E1 primitive
        init0lines, init0plines, init1lines, init1plines = collectInitStrings(cell, fasmFile)
        assert len(init1lines) == 0 and len(init1plines) == 0, "{} {}".format(len(init1lines), len(init1plines))

        # Get all the init lines for this cell, pad them with 0's, and reverse them
        inits =  processInitLines(cell, init0lines)
        initps = processInitLines(cell, init0plines)

    # Step 3: Now check if we can find all the bits in this cell
    for w in range(cell.addr_beg, cell.addr_beg + len(init)):
        for b in range(cell.slice_beg, cell.slice_end + 1):
            bwid = cell.slice_end - cell.slice_beg + 1
            wdep = cell.addr_end - cell.addr_beg + 1
            rwid = cell.width
            pwid = cell.pbits
            dwid = cell.dbits
            if bwid != dwid + pwid:
                print("     ERROR: {} {} {} {}".format(bwid, rwid, pwid, dwid))
                continue
            # Chop up the bits between parity and normal bits
            # Only the RAMB36E1 can have an rwid of 72
            if not r36:
                assert not rwid == 72
            islice = 64 if rwid == 72 else 32 if rwid == 36 else 16 if rwid == 18 else 8 if rwid == 9 else rwid
            pslice = 8 if rwid == 72 else 4 if rwid == 36 else 2 if rwid == 18 else 1 if rwid == 9 else 0

            if verbose:
                print("Doing: {} {}".format(w, b))
                print(
                    "{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT"
                    .format(bwid, pwid, pslice, dwid, islice),
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
            # Number of bits in INIT and INITP should be 32K/16K and 4K respectively (r32) or 16K and 2K respectively
            assert islice * wdep == (32768 if r36 else 16384)
            if pslice != 0:
                assert pslice * wdep == (4096 if r36 else 2048)

            # Is the bit in the INIT portion of the INITP portion?
            if b - cell.slice_beg < islice:
                bslice = islice
                parity = False
            else:
                bslice = pslice
                parity = True

            # Computer how many bits make up each "word"
            initLen = 512 if r36 else 256
            numPerInit = (initLen / bslice)
            assert int(numPerInit) == numPerInit

            if verbose:
                print(
                    "{} {} {} {} {} {}".format(
                        w, b, cell.width, len(init),
                        len(init[w]) - 1 - b, init[w]
                    )
                )
            # Get the bit from the .mem inititalization file array
            initbit = init[w][len(init[w]) - 1 - b]

            # Computer where to find the bit in the INIT strings (after they were combined and reversed above)
            initRow = int(w / numPerInit)
            wordOffset = int(w % numPerInit)
            bitOffset = wordOffset * bslice + (b - cell.slice_beg - (islice if parity else 0)
            )
            if verbose:
                print(
                    "FASM initRow = {} bitOffset = {}".format(
                        initRow, bitOffset
                    )
                )
            # Read the bit from either the INIT or the INITP section
            fasmbit = initps[initRow][bitOffset] if parity else inits[initRow][
                bitOffset]
            if verbose:
                print("Bit[{}][{}] = {} vs. {}".format(w, b, initbit, fasmbit))

            # Check that the bits match each other, proving that the above algorithm is correct
            assert initbit == fasmbit

            # Finally, print out the mapping if requested
            initRow = "{:02x}".format(initRow).upper()
            if mappings or verbose:
                if parity:
                    print(
                        "{} init.mem[{}][{}] -> {}.{}_Y{}.INITP_{}[{:03}] ".
                        format(
                            designName, 
                            w, 
                            b, 
                            cell.tile[0:6], 
                            cell.type[:-2],
                            '0' if (r36 is False or bitOffset % 2 == 0) else '1',  # change
                            initRow, 
                            int(bitOffset/2) if r36 else bitOffset
                        )
                    )
                else:
                    print(
                        "{} init.mem[{}][{}] -> {}.{}_Y{}.INIT_{}[{:03}] ".
                        format(
                            designName, 
                            w, 
                            b, 
                            cell.tile[0:6], 
                            cell.type[:-2],
                            '0' if (r36 is False or bitOffset % 2 == 0) else '1',  # change
                            initRow, 
                            int(bitOffset/2) if r36 else bitOffset
                        )
                    )
    # If we got here, it worked so say so...
    print(
        "    Cell: {} {} {} all checked out...".format(
            designName, cell.tile, cell.type
        ),
        flush=True
    )
