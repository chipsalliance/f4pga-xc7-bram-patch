import os
import subprocess
import sys
from pathlib import Path, PurePath
import patch_mem as patch_mem


def genAlt(batchdir):
    patch_mem.patch_mem(
        fasm=os.path.join(batchdir, 'real.fasm'),
        init=os.path.join(batchdir, 'init', 'alt.mem'),
        mdd=os.path.join(batchdir, 'mapping.mdd'),
        outfile=os.path.join(batchdir, 'alt.fasm'),
        selectedMemToPatch='mem/ram'
    )


def main():
    widths_to_test = [
        1, 2, 4, 8
        #9, 16, 18, 32, 36, 64, 72, 128, 144, 256
    ]  #, 288]
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

    weird_widths_to_test = [
        3, 6, 11, 17, 19, 25, 34, 37, 69, 100, 127, 130, 200
    ]
    weird_depths_to_test = [
        ('1027', 1027),
        ('5k', 5000),
        ('7k', 7000),
        ('1050', 1050),
        ('36k', 1024 * 36),
        ('36k+20', 1024 * 36 + 20),
        ('72k', 1024 * 72),
        # do more later
    ]

    widths = widths_to_test  # + weird_widths_to_test
    depths = depths_to_test  # + weird_depths_to_test

    topdir = "./testing/tests"
    master = os.path.join(topdir, 'master')

    FORCE = True  # Force generation of new design

    for wid in widths:
        for depth_tup in depths:
            depthname = depth_tup[0]
            depth = depth_tup[1]
            design = '{}b{}'.format(depthname, wid)
            batchdir = os.path.join(master, design)
            batchbit = os.path.join(batchdir, 'vivado/{}.bit'.format(design))
            print("\n=============================\nDoing: " + batchbit)
            #            if not os.path.isfile(batchdir) or not os.path.isfile(batchbit):
            if FORCE or not os.path.isfile(batchbit):
                command = './testing/generate_tests_script.sh {} {} {}'.format(
                    wid, depthname, depth
                )
                print("Generating" + command)
                os.system(command)
                print("Calling genAlt({})".format(batchdir))
                genAlt(batchdir)
            else:
                print(
                    '    Design {} already generated, skipping...'.
                    format(design)
                )


if __name__ == "__main__":
    # Generate a series of tests
    if (len(sys.argv) == 1):
        main()
    # Generate a single directed test
    elif (len(sys.argv) == 4):
        wid = sys.argv[1]
        depthname = sys.argv[2]
        depth = sys.argv[3]
        command = './testing/generate_tests_script.sh {} {} {}'.format(
            wid, depthname, depth
        )
        print("Generating" + command)
        os.system(command)

        batchdir = os.path.join(
            "./testing/tests", 'master', '{}b{}'.format(depthname, wid)
        )
        print("Calling genAlt({})".format(batchdir))
        genAlt(batchdir)
    else:
        print(
            "Usage:\n   python generate_tests.py   #To run series of tests\nOR\n   python generate_tests.py width depthName depth  # To generate a directed test",
            file=sys.stderr
        )
        exit(1)
