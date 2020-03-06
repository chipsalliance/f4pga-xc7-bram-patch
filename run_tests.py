"""
run_tests.py
====================================
The core of the test infrastructure for prjxray-bram-patch.

Runs a series of tests on test designs to ensure patching is operational.

Test designs to be operated on are generated using the "generate_test.py" script and are located in
testing/tests/master.
"""

import os
import os.path
import subprocess
import sys
from os import path
from pathlib import Path, PurePath
import patch_mem as patch_mem

# Set all the path and file names


def clear_reports():
    """
    Empty out the files associated with the reports files (passed.txt, failed.txt, incomplete.txt), which are located in testing/tests.
    
    As tests are conducted by this script, status for each is recorded in the above 3 files.
    
    This is used for when you want to clear out those files.
    """
    for reportFile in [passed, failed, incomplete]:
        try:
            os.remove(reportFile)
            reportFile.touch()
            print('Cleared {}'.format(reportFile))
        except:
            print('Unable to clear report file: {}'.format(reportFile))


def doTest(fasmToPatch, init, mdd, patchedFasm, origFasm):
    """
    Test a specific design and report if it was successful.

    Parameters
    ---------
        fasmToPatch
            Path to fasm file to be patched
        init
            Path to new memory init file
        mdd
            Path to MDD file
        patchedFasm
            Where to put the patched file (typically in /tmp)
        origFasm
            What to compare the patchedFasm to
    """

    for fil in [fasmToPatch, init, mdd, origFasm]:
        assert fil.exists(), print("No such file: {}".format(fil))

#    print("{}\n{}\n{}\n{}\n{}".format(fasmToPatch, init, mdd, patchedFasm, origFasm))

#    # Testing requires an 'alt.fasm' file to exist.  This will create it if desired.
#    if GENERATE_ALT:
#        print("\n###############################################")
#        print("Generating alt fasm: {}".format(batchdir/alt_fasmpath))
#        patch_mem.patch_mem(fasm=real_fasm,#        patch_mem.patch_mem(fasm=real_fasm,
#                                    init=(batchdir/altpath),
#                                    mdd=mdd,
#                                    outfile=(batchdir/alt_fasmpath))

    patch_mem.patch_mem(
        fasm=fasmToPatch, init=init, mdd=mdd, outfile=patchedFasm
    )
    print('Checking results...')
    print("   {}\n   {}".format(origFasm, patchedFasm))
    diff = subprocess.run(
        ['diff', str(origFasm), str(patchedFasm)],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )  # , shell=True)

    if (diff.stdout == ''):
        print('Files match, success!\n')
        return "SUCCESS"
    else:
        print('ERROR: Files do not match\n')
        return "FAILURE"
    return "SUCCESS"


####################################################################################################
def main():
    """
    The main test driver routine.

    Parameters
    ---------
    """

    # Terminate early without running all tests?
    LAST_TEST = (1, '16k', 2048 * 8)
    MAKE_REPORT = True  # Do you want status updated into passed.txt, failed.txt, incomplete.txt?
    CLEAR_REPORTS = False  # Do you want status files cleared?
    GENERATE_ALT = True  # This needs to be set to true to force the creation of the alt.fasm file (only needed once)
    EXIT_ON_FAILURE = False  # Should you exit on a failure?
    EXIT_ON_INCOMPLETE = False  # Should you exit on an incomplete test?
    #ONE_TEST = None
    ONE_TEST = (1, '128', 1 * 128)
    SKIP_PASSED = True  # Should you skip over tests that are in the passed.txt file?

    widths_to_test = [
        1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256, 288
    ]
    depths_to_test = [
        ('128', 128),
        ('256', 256),
        ('512', 512),
        ('1k', 1024),
        ('2k', 2048),
        #('4k', 2048 * 2), ('8k', 2048 * 4), ('16k', 2048 * 8),
        #('32k', 2048 * 16), ('64k', 2048 * 32), ('128k', 2048 * 64)
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

    rootdir = os.environ.get("MEM_PATCH_DIR")
    assert rootdir is not None

    testsdir = Path(rootdir + '/testing/tests')
    stopfile = testsdir / 'stop'

    passed = testsdir / 'passed.txt'
    failed = testsdir / 'failed.txt'
    incomplete = testsdir / 'incomplete.txt'

    widths = widths_to_test + weird_widths_to_test
    depths = depths_to_test + weird_depths_to_test

    already_passed = []

    # Do we want to skip tests that have already passed or not?
    # If so, build the already_passed list from the passed.txt file
    if SKIP_PASSED:
        with open(str(passed), 'r') as p:
            for line in p:
                if line.strip() is not '':
                    already_passed.append(line.strip())

    if CLEAR_REPORTS:
        clear_reports()

    if ONE_TEST is not None:
        wid, depthname, depth = ONE_TEST

        design = '{}b{}'.format(depthname, wid)
        designdir = testsdir / 'master' / design
        status = doTest(
            fasmToPatch=designdir / 'alt.fasm',
            init=designdir / 'init/init.mem',
            mdd=designdir / 'mapping.mdd',
            patchedFasm=designdir / 'patched.fasm',
            origFasm=designdir / 'real.fasm'
        )
    else:  # Perform a whole collection of tests
        for wid in widths_to_test:
            for depth_tup in depths_to_test:
                depthname = depth_tup[0]
                depth = depth_tup[1]

                design = '{}b{}'.format(depthname, wid)
                designdir = testsdir / 'master' / design
                if design in already_passed:
                    print(
                        'Skipping {} because it already passed'.format(design)
                    )
                    continue

                if stopfile.is_file():
                    print('Stop file detected, stopping batch')
                    sys.exit()

                status = doTest(
                    fasmToPatch=designdir / 'alt.fasm',
                    init=designdir / 'init/init.mem',
                    mdd=designdir / 'mapping.mdd',
                    patchedFasm=designdir / 'patched.fasm',
                    origFasm=designdir / 'real.fasm'
                )

                print(already_passed)
                if status == "SUCCESS":
                    if MAKE_REPORT:
                        if design not in already_passed:
                            already_passed.append(design)
                            with passed.open('a') as f:
                                f.write('{}\n'.format(design))

                if status == "FAILURE":
                    if MAKE_REPORT:
                        with failed.open('r') as f:
                            already_failed = f.read()
                        if design not in already_failed:
                            with failed.open('a') as f:
                                f.write('{}\n'.format(design))
                    if EXIT_ON_FAILURE:
                        print('Failure detected, exiting')
                        sys.exit()

                if status == "INCOMPLETE":
                    with incomplete.open('r') as f:
                        already_incomplete = f.read()
                    if design not in already_incomplete:
                        with incomplete.open('a') as f:
                            f.write('{}\n'.format(design))

                    if EXIT_ON_INCOMPLETE:
                        print('Incomplete test detected, exiting')
                        sys.exit()

                if (wid, depthname, depth) == LAST_TEST:
                    print('Last test executed, stopping batch')
                    sys.exit()


if __name__ == "__main__":
    main()  # TODO: add command line parsing
