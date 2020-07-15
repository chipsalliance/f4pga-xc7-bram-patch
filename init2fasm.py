import pathlib
import argparse
import bitMapping
import patch_mem
import parseutil.misc as misc
import re

def create_dictionary (mdd_data):
    output_dict = {}
    for data in mdd_data:
        output_dict[data.tile] = {
            'Y0INIT' : [],
            'Y1INIT' : [],
            'Y0INITP': [],
            'Y1INITP': []
        }
    return output_dict

def init2fasm (
    baseDir,  # pathlib.Path
    memName,  # str
    mdd,  # pathlib.Path
    initFile,  # pathlib.Path  
    fasmFile,  # pathlib.Path
    checkFile, #pathlib.Path
    verbose,  # bool
    printmappings  # bool
):
    designName = baseDir.name

    # 0. Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(mdd, memName)
    words, initbitwidth = misc.getMDDMemorySize(mdd_data)

    reassembled_init_array = create_dictionary(mdd_data)
    reassembled_init_strings = create_dictionary(mdd_data)

    # 1. Get the mapping info
    print("Loading mappings for {}...".format(designName))
    mappings = bitMapping.createBitMappings(
        baseDir,  # The directory where the design lives
        memName,
        mdd,
        False,
        printmappings
    )
    print("  Done loading mappings")

    with initFile.open() as f:
        init_words = f.read().split()

    for mapping in mappings:
        if mapping.fasmY:
            index_string = 'Y1'
        else:
            index_string = 'Y0'
        if mapping.fasmINITP:
            index_string += 'INITP'
        else:
            index_string += 'INIT'
        while len(reassembled_init_array[mapping.tile][index_string]) <= mapping.fasmLine:
            reassembled_init_array[mapping.tile][index_string].append([None] * 256)
        bin_word = (bin(int(init_words[mapping.word], 16))[2:])[::-1]
        if mapping.bit >= len(bin_word):
            reassembled_init_array[mapping.tile][index_string][mapping.fasmLine][mapping.fasmBit] = '0'
        else:
            reassembled_init_array[mapping.tile][index_string][mapping.fasmLine][mapping.fasmBit] = bin_word[mapping.bit]

    for tile in reassembled_init_array:
        for group in reassembled_init_array[tile]:
            for line in reassembled_init_array[tile][group]:
                for i in range(len(line)):
                    if line[i] == None:
                        line[i] = '0'
                full_word = ("".join(line))[::-1]
                reassembled_init_strings[tile][group].append(full_word[full_word.index('1'):])
    
    with fasmFile.open() as f:
        fasm_lines = f.readlines()

    for tile in reassembled_init_strings:
        for group in reassembled_init_strings[tile]:
            for i in range(len(reassembled_init_strings[tile][group])):
                string = reassembled_init_strings[tile][group][i]
                fasm_num = hex(i)[2:]
                print(fasm_num)
                print(string)
                fasm_entry = None
                k = -1
                for j in range(len(fasm_lines)):
                    if re.search(tile + "\.RAMB18_" + group[0:2] + "\." + group[2:] + "_" + fasm_num.upper(), fasm_lines[j]) != None:
                        k = j
                        break
                if k != -1:
                    pass
                else:
                    print("We haven't created this feature yet")
                    exit(1)

    #newInitBits = [[None for j in range(initbitwidth)] for k in range(words)]
    # 3. Handle each cell
    #for cell in mdd_data:
        ## inits will be indexed as inits[y01][initinitp]
        #inits = [[None for j in range(2)] for k in range(2)]

        ## Convert the FASM lines into the proper format strings
        ## Store them in a multi-dimensional array indexed by y01 and INITP/INIT (True/False)
        #inits[0][False] = misc.processInitLines("0s", init0lines, cell, False)
        #inits[0][True] = misc.processInitLines("0ps", init0plines, cell, True)
        #inits[1][False] = misc.processInitLines("1s", init1lines, cell, False)
        #inits[1][True] = misc.processInitLines("1ps", init1plines, cell, True)

    #    for w in range(words):
    #        for b in range(initbitwidth):
    #            if w < cell.addr_beg or w > cell.addr_end:
    #                continue
    #            if b < cell.slice_beg or b > cell.slice_end:
    #                continue

    #            # Get the bit from the FASM line
    #            mapping = bitMapping.findMapping(w, b, initbitwidth, mappings)
    #            assert mapping is not None, "{} {} {}".format(
    #                w, b, initbitwidth
    #            )
    #            # Now get the actual bit
    #            fasmbit = inits[mapping.fasmY][mapping.fasmINITP][
    #                mapping.fasmLine][mapping.fasmBit]

    #            # Put the bit into the array
    #            newInitBits[w][b] = fasmbit
    ## 4. Now, create real init array
    #newInitFile = []
    #or w in range(words):
    #   wd = ""
    #   for b in range(initbitwidth):
    #       if newInitBits[w][b] is None:
    #            print("ERROR: None at {}:{}".format(w, b))
    #        else:
    #            wd += newInitBits[w][b]
    #    newInitFile.append(wd[::-1])  # Don't forget to reverse it

    # 5. Do checking if asked
    #if origInitFile is not None:
    #   print("    Checking with original...")
    #    origInit = parseutil.parse_init_test.read_initfile(
    #        origInitFile, initbitwidth, reverse=False
    #    )
    #   for w in range(words):
    #       for b in range(initbitwidth):
    #           if newInitFile[w][b] != origInit[w][b]:
    #               print(
    #                   "Mismatch: {}:{} {} {}".format(
    #                       w, b, newInitFile[w][b], origInit[w][b]
    #                   )
    #               )
    #                sys.exit(1)
    #    print("      Everything checked out successfully!!!")

    # 6. Finally, write it out
    #with initFile.open('w') as f:
    #    for lin in newInitFile:
    #        f.write(lin[::-1] + "\n")

    # 7. If we got here we were successful
    #print("      Initfile {} re-created successfully!".format(initFile))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument(
        "memname", help='Name of memory to check (as in "mem/ram")'
    )
    parser.add_argument("mddname", help='Name of mdd file)')
    parser.add_argument("memfile", help='Name of the mem file to use')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--check", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    designName = baseDir.name

    init2fasm(
            baseDir, args.memname, baseDir / args.mddname,
            baseDir / args.memfile, baseDir / "real.fasm", 
            baseDir / "real.fasm" if args.check == True else None,
            args.verbose, args.printmappings
        )
