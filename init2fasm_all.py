import init2fasm
import argparse
import pathlib

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument("--verbose", action='store_true')

    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )

    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    dirs = list(baseDir.glob("*"))
    dirs.sort()

    for d in dirs:
        designName = d.name
        init2fasm.init2fasm(
            d, "mem/ram", d / "{}.mdd".format(designName),
            d / "init/init.mem", d / "real.fasm", d / "real.fasm",
            args.verbose, args.printmappings
        )
        print("")