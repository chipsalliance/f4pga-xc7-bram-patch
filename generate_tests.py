import os
import subprocess
from os import path
from pathlib import Path, PurePath

widths_to_test = [1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256] #, 288]
depths_to_test = [
    ('128', 128)
#    ('256', 256),
#    ('512', 512),
#    ('1k', 1024),
#    ('2k', 2048),
#    ('4k', 2048*2),
#    ('8k', 2048*4),
#    ('16k', 2048*8),
#    ('32k', 2048*16),
#    ('64k', 2048*32),
#    ('128k', 2048*64)
]

weird_widths_to_test = [3, 6, 11, 17, 19, 25, 34, 37, 69, 100, 127, 130, 200]
weird_depths_to_test = [
    ('1027', 1027),
    ('5k', 5000),
    ('7k', 7000),
    ('1050', 1050),
    ('36k', 1024*36),
    ('36k+20', 1024*36+20),
    ('72k', 1024*72),
    # do more later
]


widths = widths_to_test # + weird_widths_to_test
depths = depths_to_test # + weird_depths_to_test

topdir = Path("./testing/tests").expanduser()
master = topdir / 'master'


for wid in widths:
    for depth_tup in depths:
        depthname = depth_tup[0]
        depth = depth_tup[1]
        design = '{}b{}'.format(depthname, wid)
        designpath = PurePath(design)
        bitpath = PurePath('vivado/{}.bit'.format(design))
        batchdir = master / designpath
        batchbit = batchdir / bitpath
        print(batchdir)
        if not batchdir.exists() or not batchbit.exists():
            command = './testing/generate_tests_script.sh {} {} {}'.format(wid, depthname, depth)
            print("Generating" + command)
            os.system(command)
        else:
            print('Design {} already generated'.format(design))
            print("{} {}".format(batchdir, batchbit))
