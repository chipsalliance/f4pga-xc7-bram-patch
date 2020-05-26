import os
import subprocess
import sys
from pathlib import Path, PurePath
import patch_mem as patch_mem
import math


def genAlt(batchdir):
    patch_mem.patch_mem(
        fasm=os.path.join(batchdir, 'real.fasm'),
        init=os.path.join(batchdir, 'init', 'alt.mem'),
        mdd=os.path.join(batchdir, 'mapping.mdd'),
        outfile=os.path.join(batchdir, 'alt.fasm'),
        selectedMemToPatch='mem/ram'
    )


def mylog2(n):
    val = 0
    while round(math.pow(2, val)) < n:
        val += 1
    return val


def main():
    widths_to_test = [
        1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256, 288
    ]
    depths_to_test = [
        ('128', 128), ('256', 256), ('512', 512), ('1k', 1024), ('2k', 2048),
        ('4k', 2048 * 2), ('8k', 2048 * 4), ('16k', 2048 * 8),
        ('32k', 2048 * 16), ('64k', 2048 * 32), ('128k', 2048 * 64)
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

    widths = widths_to_test
    depths = depths_to_test

    topdir = "./testing/tests"
    master = os.path.join(topdir, 'master')

    FORCE = False  # Force generation of new design
    ALT_ONLY = False  # Just generate alt.fasm files (no need to re-run Vivado)

    for wid in widths:
        for depth_tup in depths:
            depthname = depth_tup[0]
            depth = depth_tup[1]
            totalBits = int(wid) * depth
            if totalBits > 2457600:
                print(
                    "\n===========================\n*****************\nMemory too large: {}b{} = {}, skipping...\n******************"
                    .format(depthname, wid, totalBits)
                )
                continue
            totalPins = 2 + 2 * mylog2(depth) + 2 * int(wid)
            if totalPins > 250:
                print(
                    "\n===========================\n*****************\nMemory has too many pins: {}b{} = {}, skipping...\n******************"
                    .format(depthname, wid, totalPins)
                )
                continue
            design = '{}b{}'.format(depthname, wid)
            batchdir = os.path.join(master, design)
            batchbit = os.path.join(batchdir, 'vivado/{}.bit'.format(design))
            altfasm = os.path.join(batchdir, 'alt.fasm')
            print("\n=============================\nDoing: " + batchbit)
            #            if not os.path.isfile(batchdir) or not os.path.isfile(batchbit):
            if ALT_ONLY:
                print("Calling genAlt({})".format(batchdir), flush=True)
                genAlt(batchdir)
            elif FORCE or not os.path.isfile(altfasm):
                command = r'./testing/generate_tests_script.sh {} {} {}'.format(
                    wid, depthname, depth
                )
                print("Generating: " + command, flush=True)
                v = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    universal_newlines=True
                )
                stdout, stderr = v.communicate()
                print(stdout, flush=True)
                if stderr is not None:
                    print(stderr, flush=True)

                if not os.path.isfile(batchbit):
                    print(
                        "No bit file found: {}, skipping rest of generation..."
                        .format(batchbit)
                    )
                else:
                    print("Calling genAlt({})".format(batchdir), flush=True)
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
    # Just do the genAlt() step
    elif len(sys.argv) == 2:
        genAlt(sys.argv[1])
    else:
        print(
            "Usage:\n   python generate_tests.py   #To run series of tests\nOR",
            file=sys.stderr
        )
        print(
            "Usage:\n   python generate_tests.py width depthName depth  # To generate a directed test\nOR",
            file=sys.stderr
        )
        print(
            "Usage:\n   python generate_tests.py  batchDir #To run just genAlt()",
            file=sys.stderr
        )
        exit(1)
