import sys
import os
import glob
import json

dirs = glob.glob("1kb*")
dirs.sort()
for d in dirs:
    print("########################################################################")
    print(d)
    try:
        with open(d+"/"+d+".mdd.json") as f:
            dat = json.load(f)
            print(len(dat))
            for d in dat:
                print("{} {} {} {} {}:{} {}:{}".format(
                    d['DESIGN'], 
                    d["CELLTYPE"],
                    d["MEM.PORTA.DATA_BIT_LAYOUT"], 
                    d["READ_WIDTH_A"],
                    d["BRAM_ADDR_END"],
                    d["BRAM_ADDR_BEGIN"],
                    d["BRAM_SLICE_END"],
                    d["BRAM_SLICE_BEGIN"]
                    )
                )
    except:
        print("No JSON file found: {}".format(d))
print("########################################################################")


