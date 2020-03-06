import os
import os.path
import subprocess
import sys
from os import path
from pathlib import Path, PurePath
import patch_mem as patch_mem
# import utils.patch_readmem as patch_readmem

rootdir = os.environ.get("MEM_PATCH_DIR")
if rootdir is None:
    print("ERROR: must set environment variable MEM_PATCH_DIR, exiting.")
    sys.exit()

topdir = Path(rootdir + "/testing/tests").expanduser()
stopfile = topdir / 'stop'
passed = topdir / 'passed.txt'
failed = topdir / 'failed.txt'
incomplete = topdir / 'incomplete.txt'
mddpath = PurePath('mapping.mdd')
initpath = PurePath('init/init.mem')
altpath = PurePath('init/alt.mem')
alt_fasmpath = PurePath('alt.fasm')
patched_fasmpath = PurePath('patched.fasm')
real_fasmpath = PurePath('real.fasm')


def clear_reports():
    try:
        # passed.touch()
        os.remove(passed)
        passed.touch()
        print('Cleared passed.txt')
    except:
        print('Unable to clear passed.txt')
    try:
        # failed.touch()
        os.remove(failed)
        failed.touch()
        print('Cleared failed.txt')
    except:
        print('Unable to clear failed.txt')
    try:
        # incomplete.touch()
        os.remove(incomplete)
        incomplete.touch()
        print('Cleared incomplete.txt')
    except:
        print('Unable to clear incomplete.txt')


def doTest(design, depthname, depth, wid):
    batchdir = topdir / 'master' / design
    mdd = batchdir / mddpath
    bit = batchdir / 'vivado' / '{}.bit'.format(design)
    real_fasm = batchdir / real_fasmpath
    patched_fasm = batchdir / patched_fasmpath

    #print(mdd)
    #print(bit)
    #print(real_fasm)

    if not mdd.exists() or not bit.exists() or not real_fasm.exists():
        return "INCOMPLETE"

    if GENERATE_ALT:
        print("\n###############################################")
        print("Generating alt fasm: {}".format(batchdir / alt_fasmpath))
        patch_mem.patch_mem(
            fasm=real_fasm,
            init=(batchdir / altpath),
            mdd=mdd,
            outfile=(batchdir / alt_fasmpath)
        )

    print("\n###############################################")
    print(
        "\nDoing patching of:\n   {}\nusing\n   {}\nto\n   {}".format(
            batchdir / alt_fasmpath, batchdir / initpath, patched_fasm
        )
    )
    patch_mem.patch_mem(
        fasm=(batchdir / alt_fasmpath),
        init=(batchdir / initpath),
        mdd=mdd,
        outfile=patched_fasm
    )
    print("\n###############################################")
    print('\nChecking results...')
    diff = subprocess.run(
        ['diff', str(real_fasm), str(patched_fasm)],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )  # , shell=True)
    diff = diff.stdout
    # print(diff)

    if (diff == ''):
        print('  Files match, success!\n')
        if MAKE_REPORT:
            if design not in str(already_passed):
                with passed.open('a') as f:
                    f.write('{}\n'.format(design))
                # passed.write_text(f'{design}')
    else:
        print('ERROR: Files do not match\n')
        if MAKE_REPORT:
            with failed.open('r') as f:
                already_failed = f.read()
            if design not in str(already_failed):
                with failed.open('a') as f:
                    f.write('{}\n'.format(design))
            # failed.write_text(f'{design}')
            return "FAILURE"
    return "SUCCESS"

    # command = f'./generate/patch_check.sh {wid} {depth_tup[0]} {depth_tup[1]} {move_files}'
    # os.system(command)


# LAST_TEST = (4, '128k', 2048*64)
LAST_TEST = (1, '16k', 2048 * 8)
MOVE_FILES = False
MAKE_REPORT = True
CLEAR_REPORTS = False
GENERATE_ALT = False  # This needs to be set to true to force the creation of the alt.fasm file (only needed once)
EXIT_ON_FAILURE = False
EXIT_ON_INCOMPLETE = False
ONE_TEST_ONLY = True
#ONE_TEST = (8, '128k', 2048*64)
ONE_TEST = (1, '128', 1 * 128)
SKIP_PASSED = False

widths_to_test = [1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256, 288]
depths_to_test = [
    ('128', 128), ('256', 256), ('512', 512), ('1k', 1024), ('2k', 2048),
    ('4k', 2048 * 2), ('8k', 2048 * 4), ('16k', 2048 * 8), ('32k', 2048 * 16),
    ('64k', 2048 * 32), ('128k', 2048 * 64)
]

weird_widths_to_test = [3, 6, 11, 17, 19, 25, 34, 37, 69, 100, 127, 130, 200]
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

widths = widths_to_test + weird_widths_to_test
depths = depths_to_test + weird_depths_to_test
completed_widths = []
completed_depths = []
already_passed = []

if SKIP_PASSED:
    with open(passed, 'r') as p:
        for line in p:
            if line.strip() is not '':
                already_passed.append(line)
                # print(line)

if MAKE_REPORT and CLEAR_REPORTS:
    clear_reports()

if ONE_TEST_ONLY:
    # y'all got hijacked
    wid, depthname, depth = ONE_TEST
    design = '{}b{}'.format(depthname, wid)
    status = doTest('{}b{}'.format(depthname, wid), depthname, depth, wid)
    if status == "INCOMPLETE":
        print(
            '\tUnable to perform check because bitstream and/or mdd file were not found.'
        )
else:
    for wid in widths_to_test:
        if wid in completed_widths:
            continue
        for depth_tup in depths_to_test:
            if depth_tup[0] in completed_depths:
                continue

            depthname = depth_tup[0]
            depth = depth_tup[1]

            design = '{}b{}'.format(depthname, wid)
            print(design)
            if design in str(already_passed):
                print('Skipping {} because it already passed'.format(design))
                continue

            if stopfile.is_file():
                print('Stop file detected, stopping batch')
                sys.exit()

            status = doTest(design, depthname, depth, wid)
            if status == "FAILURE":
                if EXIT_ON_FAILURE:
                    print('Failure detected, exiting')
                    sys.exit()

            if status == "INCOMPLETE":
                print(
                    '\tUnable to perform check because bitstream and/or mdd file were not found.'
                )
                print('\tAdded {} to \"incomplete\" list\n'.format(design))
                with incomplete.open('r') as f:
                    already_incomplete = f.read()
                if design not in str(already_incomplete):
                    with incomplete.open('a') as f:
                        f.write('{}\n'.format(design))

                if EXIT_ON_INCOMPLETE:
                    print('Incomplete test detected, exiting')
                    sys.exit()

            if (wid, depthname, depth) == LAST_TEST:
                print('Last test executed, stopping batch')
                sys.exit()
