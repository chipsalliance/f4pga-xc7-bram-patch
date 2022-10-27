import checkTheBits
import argparse
import pathlib
import bits2init


def designSizes(designName):
    words = designName.split('b')[0]
    if words[-1] == 'k':
        words = int(words[:-1]) * 1024
    else:
        words = int(words)
    bits = int(designName.split('b')[1])
    return (words, bits)


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
        words, bits = designSizes(designName)
        print(designName)
        bits2init.bits2init(
            d, "mem/ram", d / "{}.mdd".format(designName), d / "init/new.mem",
            d / "init/init.mem", d / "real.fasm", args.verbose,
            args.printmappings
        )
        print("")
    print("")
