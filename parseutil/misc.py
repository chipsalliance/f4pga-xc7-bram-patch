# File: misc.py
# Author: Brent Nelson
# Created: 25 June 2020
# Description:
#    Miscellaneous routines

import parseutil


# Pad a string to a certain length with 'ch'
def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)


# Process the INIT lines one at a time.
# Pad them into 256 character lines and reverse them end to end.
# Return a list of them.
# They should appear in ascending order, this checks that.
# TODO: is it possible to have less than the full count of 64 INIT lines?
#           Yes: see design 512b18.
#       Would an INIT get left out of the FASM file it is was all zeroes?
#           It is possible - but haven't seen this yet since using random data.
#       To be safe, filling out full complement of lines with 0's in the code below.
#       May be overkill but hey...
def processInitLines(typ, initlines, cell, parity):
    if len(initlines) == 0:
        return []
    inits = []
    indx = 0
    for line in enumerate(initlines):
        lin = line[1].rstrip()
        if lin.split(".")[0] != cell.tile:
            continue
        key = lin.split(".")[2].split("_")[1][0:2]
        val = lin.split("=")[1][6:]
        key = int(key, 16)
        assert key == indx, "key={} indx={} line={}".format(key, indx, line)
        val = pad('0', 256, val)[::-1]
        inits.append(val)
        indx += 1
    while len(inits) < (8 if parity else 64):
        inits.append("0" * 256)
    return inits


# Read the FASM file and filter out Y0 and Y1 INIT and INITP strings
# for the current cell and put into lists to return.
def readInitStringsFromFASMFile(fasmFile):
    init0lines = []
    init0plines = []
    init1lines = []
    init1plines = []
    with fasmFile.open() as f:
        for line in f.readlines():
            if "Y0.INITP" in line:
                init0plines.append(line)
            elif "Y0.INIT" in line:
                init0lines.append(line)
            if "Y1.INITP" in line:
                init1plines.append(line)
            elif "Y1.INIT" in line:
                init1lines.append(line)
    return (init0lines, init0plines, init1lines, init1plines)


# Return a dict mapping names to [words, bits] lists
def getMDDMemories(mddName):
    mdd = parseutil.parse_mdd.read_mdd(mddName)
    lst = dict()
    for m in mdd:
        # Create memory name from cell_name and ram_name
        s = '/'.join(m.cell_name.split('/')[:-1]) + '/' + m.ram_name
        # Add it to list if not there already
        if s not in lst.keys():
            lst[s] = [int(m.addr_end) + 1, int(m.slice_end) + 1]
        else:
            # Update coordinates so we know how big the memory is
            itm = lst[s]
            wb = [0, 0]
            wb[0] = max(itm[0], int(m.addr_end) + 1)
            wb[1] = max(itm[1], int(m.slice_end) + 1)
            lst[s] = wb
    return lst
