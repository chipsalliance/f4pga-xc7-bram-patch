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
    checkFile,  #pathlib.Path
    verbose,  # bool
    printmappings,  # bool
    partial  # bool
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

    # 2. Get the init data
    with initFile.open() as f:
        init_words = f.read().split()

    # 3. Reassemble init strings as a dictionary of arrays
    print("Assembling new FASM strings from {}".format(initFile.name))
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

    # 4. Combine reassembled init arrays into strings
    for tile in reassembled_init_array:
        for group in reassembled_init_array[tile]:
            for line in reassembled_init_array[tile][group]:
                for i in range(len(line)):
                    if line[i] == None:
                        line[i] = '0'
                full_word = ("".join(line))[::-1]
                reassembled_init_strings[tile][group].append(full_word[full_word.index('1'):])
    print("  Done assembling new fasm init strings")
    
    # 5. Get the base fasm data to edit later
    with fasmFile.open() as f:
        fasm_lines = f.readlines()

    # 6. Replace fasm init lines with newly constructed ones
    print("Editing fasm lines")
    for tile in reassembled_init_strings:
        for group in reassembled_init_strings[tile]:
            for i in range(len(reassembled_init_strings[tile][group])):
                string = reassembled_init_strings[tile][group][i]
                fasm_num = hex(i)[2:]
                k = -1
                for j in range(len(fasm_lines)):
                    if re.search(tile + "\.RAMB18_" + group[0:2] + "\." + group[2:] + "_0?" + fasm_num.upper() + "\[", fasm_lines[j]) != None:
                        k = j
                        break
                new_fasm_line = "{}.RAMB18_{}.{}_{}{}[{}:0] = {}'b{}\n".format(tile,group[0:2],group[2:],"" if len(fasm_num) == 2 else "0",fasm_num.upper(),str(len(string)-1),len(string),string)
                if k != -1:
                    fasm_lines[k] = new_fasm_line
                else:
                    fasm_int = int(fasm_num, 16)
                    for j in range(len(fasm_lines)):
                        if re.search(tile + "\.RAMB18_" + group[0:2] + "\." + group[2:] + "_", fasm_lines[j])  != None:
                            if fasm_int == 0:
                                fasm_lines.insert(j, new_fasm_line)
                                break
                            if fasm_int > int(re.search("_..\[", fasm_lines[j]).group(0)[1:3], 16):
                                entry_group = re.search(tile + "\.RAMB18_" + group[0:2] + "\." + group[2:] + "_..", fasm_lines[j+1])
                                if entry_group == None:
                                    fasm_lines.insert(j+1, new_fasm_line)
                                    break
                                entry_num = int(entry_group.group(0)[-2:], 16)
                                if fasm_int < entry_num:
                                    fasm_lines.insert(j+1, new_fasm_line)
                                    break
    print("  Done editing fasm lines")

    # 7. Write the new lines out to new.fasm
    with (baseDir / "new.fasm").open('w') as w:
        if partial:
            current_tile = ""
            for line in fasm_lines:
                for data in mdd_data:
                    if re.search(data.tile, line) != None:
                        if current_tile != "" and data.tile != current_tile:
                            w.write("\n")
                        w.write(line)
                        current_tile = data.tile
                        break 
        else:
            for line in fasm_lines:
                w.write(line)

    # 8. Check the new lines against real.fasm
    if checkFile != None:
        print("Checking new fasm lines against real.fasm")
        with checkFile.open() as f:
            check_lines = f.readlines()
        if len(check_lines) != len(fasm_lines):
            print("  There is a different number of fasm lines in the original and new file")
            exit(1)
        for i in range(len(check_lines)):
            if check_lines[i] != fasm_lines[i]:
                print("  Mismatch on line {}".format(i+1))
                print("    Expected: {}".format(check_lines[i]))
                print("    Actual: {}".format(fasm_lines[i]))
                exit(1)
        print("  Everything matches")

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
    parser.add_argument("--partial", action='store_true')
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    designName = baseDir.name

    init2fasm(
            baseDir, args.memname, baseDir / args.mddname,
            baseDir / args.memfile, baseDir / "real.fasm", 
            baseDir / "real.fasm" if args.check == True else None,
            args.verbose, args.printmappings, args.partial
        )