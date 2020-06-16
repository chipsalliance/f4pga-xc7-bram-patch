import sys
import os
import glob
import json

#dirs = glob.glob("/home/nelson/mempatch/testing/tests/master/*")
dirs = ["1kb3"]
dirs.sort()
for d in dirs:
    fname = d.split("/")[-1]
    with open(d+"/"+fname+".mdd.json") as f:
        dat = json.load(f)
        for d in dat:
            if d["CELLTYPE"] != "RAMB18E1":
                continue
            bwid = d["BRAM_SLICE_END"]-d["BRAM_SLICE_BEGIN"]+1
            wdep = d["BRAM_ADDR_END"]-d["BRAM_ADDR_BEGIN"]+1
            rwid = d["READ_WIDTH_A"]
            pwid = int(d["MEM.PORTA.DATA_BIT_LAYOUT"].split("_")[0][1:])
            dwid = int(d["MEM.PORTA.DATA_BIT_LAYOUT"].split("_")[1][1:])
            if bwid != dwid+pwid:
                print("     ERROR: {} {} {} {}".format(bwid, rwid, pwid, dwid))
                continue
            islice = 32 if rwid == 36 else 16 if rwid == 18 else 8 if rwid == 9 else rwid
            pslice =  4 if rwid == 36 else  2 if rwid == 18 else 1 if rwid == 9 else 0
            #print("  Slices are {}:{}".format(pslice, islice))
            print("{} data bits will be found in {}({}) LSB's of INITP and {}({}) LSB's of INIT".format(bwid, pwid, pslice, dwid, islice), end='')
            print("    {} {} {} ({}) {}:{} {}.{}".format(
                d['DESIGN'], 
                d["CELLTYPE"],
                d["MEM.PORTA.DATA_BIT_LAYOUT"], 
                d["READ_WIDTH_A"],
                d["BRAM_ADDR_END"],
                d["BRAM_ADDR_BEGIN"],
                d["BRAM_SLICE_END"],
                d["BRAM_SLICE_BEGIN"],
                )
            )

            # Some sanity checks
            assert islice * wdep == 16384
            if pslice != 0:
                assert pslice * wdep == 2048

            print("    This is the correct BRAM block iff: {} >= r >= {} and {} >= b >= {}".format(
                d["BRAM_ADDR_END"],
                d["BRAM_ADDR_BEGIN"],
                d["BRAM_SLICE_END"],
                d["BRAM_SLICE_BEGIN"]
                )
            )
            numPerInit = (256/islice)
            assert int(numPerInit) == numPerInit
            print("    INIT row # =  w / {}".format(numPerInit))
            print("    Word offset = w % {}".format(numPerInit))
            print("    Bit offset in word = b - {}".format(d["BRAM_SLICE_END"]))

