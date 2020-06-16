import sys
import os
import glob
import json

print(sys.argv)

with open("s3.txt") as f:
    for line in f.readlines():
        line = line.rstrip()
        if len(line) == 0:
            continue
        for arg in sys.argv[1:]:
            #print("Arg is {}".format(arg))
            if not arg in  line:
                continue
            print(line)