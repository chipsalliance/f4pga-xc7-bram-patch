import os
import subprocess
import sys
import math


def mylog2(n):
    val = 0
    while round(math.pow(2, val)) < n:
        val += 1
    return val


def main():
    topdir = "./testing/tests"
    master = os.path.join(topdir, 'master')

    widths_to_test = [1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72]
    depths_to_test = [
        ('128', 128),
        ('256', 256),
        ('512', 512),
        ('1k', 1024),
        ('2k', 2048),
        ('4k', 2048 * 2),
        ('8k', 2048 * 4),
        ('16k', 2048 * 8),
        ('32k', 2048 * 16)  #, ('64k', 2048 * 32), ('128k', 2048 * 64)
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

    widths = weird_widths_to_test
    depths = depths_to_test

    for wid in widths:
        for depth_tup in depths:
            depthname = depth_tup[0]
            depth = depth_tup[1]
            totalBits = int(wid) * depth
            # Specific to the xc7a50t part we are using...
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

            # Actually generate the test case
            doGenerate(False, master, wid, depthname, depth)


def doGenerate(force, master, wid, depthname, depth):
    design = '{}b{}'.format(depthname, wid)
    batchdir = os.path.join(master, design)
    batchbit = os.path.join(batchdir, 'vivado/{}.bit'.format(design))
    altfasm = os.path.join(batchdir, 'alt.fasm')
    print("\n=============================\nDoing: " + batchbit)
    if not force and os.path.isfile(altfasm):
        print('    Design {} already generated, skipping...'.format(design))
    else:
        command = r'./testing/generate_tests_script.sh {} {} {} {}'.format(
            master, wid, depthname, depth
        )
        print("Generating by calling: " + command, flush=True)
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


if __name__ == "__main__":
    # Generate a series of tests
    if (len(sys.argv) == 1):
        main()
    else:
        print("\n  Usage:\n    python generate_tests.py\n", file=sys.stderr)
        exit(1)
