import cProfile
import re
import sys

args = ""
for a in sys.argv:
    args += a + " "

cProfile.run(args, 'stats')
