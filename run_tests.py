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
import patch_mem as patch_mem


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
        assert os.path.isfile(fil), print("No such file: {}".format(fil))

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
        ['diff', origFasm, patchedFasm],
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
    CLEAR_REPORTS = True  # Do you want status files cleared?
    GENERATE_ALT = True  # This needs to be set to true to force the creation of the alt.fasm file (only needed once)
    EXIT_ON_FAILURE = False  # Should you exit on a failure?
    EXIT_ON_INCOMPLETE = False  # Should you exit on an incomplete test?
    ONE_TEST = None
    #ONE_TEST = (1, '128', 1 * 128)
    SKIP_PASSED = True  # Should you skip over tests that are in the passed.txt file?

    widths_to_test = [
        1,
        2,  #4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256, 288
    ]
    depths_to_test = [
        ('128', 128),
        #('256', 256),
        #('512', 512),
        #('1k', 1024),
        #('2k', 2048),
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

    testsdir = os.path.join(rootdir, 'testing', 'tests')
    stopfile = os.path.join(testsdir, 'stop')

    passed = os.path.join(testsdir, 'passed.txt')
    failed = os.path.join(testsdir, 'failed.txt')
    incomplete = os.path.join(testsdir, 'incomplete.txt')

    widths = widths_to_test + weird_widths_to_test
    depths = depths_to_test + weird_depths_to_test

    already_passed = []

    if CLEAR_REPORTS:
        print("Clearing 'passed.txt', 'failed,txt', 'incomplete.txt'")
        for reportFile in [passed, failed, incomplete]:
            if os.path.isfile(reportFile):
                try:
                    os.remove(reportFile)
                    with open(reportFile, mode='w') as r:
                        pass
                except:
                    print('Unable to clear report file: {}'.format(reportFile))
            else:
                with open(reportFile, mode='w') as r:
                    pass

    # Do we want to skip tests that have already passed or not?
    # If so, build the already_passed list from the passed.txt file
    if SKIP_PASSED:
        with open(passed) as p:
            for line in p:
                if line.strip() is not '':
                    already_passed.append(line.strip())

    if ONE_TEST is not None:
        wid, depthname, depth = ONE_TEST

        design = '{}b{}'.format(depthname, wid)
        designdir = os.path.join(testsdir, 'master', design)
        status = doTest(
            fasmToPatch=os.path.join(designdir, 'alt.fasm'),
            init=os.path.join(designdir, 'init', 'init.mem'),
            mdd=os.path.join(designdir, 'mapping.mdd'),
            patchedFasm=os.path.join(designdir, 'patched.fasm'),
            origFasm=os.path.join(designdir, 'real.fasm')
        )
    else:  # Perform a whole collection of tests
        for wid in widths_to_test:
            for depth_tup in depths_to_test:
                depthname = depth_tup[0]
                depth = depth_tup[1]

                design = '{}b{}'.format(depthname, wid)
                designdir = os.path.join(testsdir, 'master', design)
                if design in already_passed:
                    print(
                        'Skipping {} because it already passed'.format(design)
                    )
                    continue

                if os.path.isfile(stopfile):
                    print('Stop file detected, stopping batch')
                    sys.exit()

                status = doTest(
                    fasmToPatch=os.path.join(designdir, 'alt.fasm'),
                    init=os.path.join(designdir, 'init', 'init.mem'),
                    mdd=os.path.join(designdir, 'mapping.mdd'),
                    patchedFasm=os.path.join(designdir, 'patched.fasm'),
                    origFasm=os.path.join(designdir, 'real.fasm')
                )

                if status == "SUCCESS":
                    if MAKE_REPORT:
                        if design not in already_passed:
                            already_passed.append(design)
                            with open(passed, mode='a') as f:
                                f.write('{}\n'.format(design))

                if status == "FAILURE":
                    if MAKE_REPORT:
                        with open(failed) as f:
                            already_failed = f.read()
                        if design not in already_failed:
                            with open(failed, mode='a') as f:
                                f.write('{}\n'.format(design))
                    if EXIT_ON_FAILURE:
                        print('Failure detected, exiting')
                        sys.exit()

                if status == "INCOMPLETE":
                    with open(incomplete) as f:
                        already_incomplete = f.read()
                    if design not in already_incomplete:
                        with open(incomplete, mode='a') as f:
                            f.write('{}\n'.format(design))

                    if EXIT_ON_INCOMPLETE:
                        print('Incomplete test detected, exiting')
                        sys.exit()

                if (wid, depthname, depth) == LAST_TEST:
                    print('Last test executed, stopping batch')
                    sys.exit()


if __name__ == "__main__":
    # Run a series of tests
    if (len(sys.argv) == 1):
        main()
    # Run a single directed test
    elif (len(sys.argv) == 6):
        assert os.path.isfile(sys.argv[1])
        doTest(
            fasmToPatch=sys.argv[1],
            init=sys.argv[2],
            mdd=sys.argv[3],
            patchedFasm=sys.argv[4],
            origFasm=sys.argv[5]
        )
    else:
        print(
            "Usage:\n   python run_tests.py   #To run series of tests\nOR\n   python run_tests.py fasmToPatch, init, mdd, patchedFasm, origFasm  # To run a directed test",
            file=sys.stderr
        )
        exit(1)
