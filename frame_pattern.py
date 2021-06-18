#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

import sys
import os
import re
import parseutil.parse_mdd as mddutil
import patch_mem
import json


def make_2D_list(numberOfLists, numberOfEntriesInLists, isZeroes=False):
    outputList = []
    if isZeroes:
        for i in range(numberOfLists):
            listEntry = ['0'] * numberOfEntriesInLists
            outputList.append(listEntry)
    else:
        for i in range(numberOfLists):
            listEntry = [None] * numberOfEntriesInLists
            outputList.append(listEntry)
    return outputList


def frame_pattern(
    fasmFile, dbFile, memoryToRead, mddFile, jsonFile, frmFile, outfile
):

    WORD_LENGTH = 8
    output = {}
    testsWorked = True

    writeFile = open(outfile, 'w')
    writeFile.truncate(0)

    mddData = patch_mem.readAndFilterMDDData(mddFile, memoryToRead)
    if len(mddData) == 0:
        exit(1)

    with open(fasmFile, 'r') as f:
        fasmLines = f.readlines()

    # Loop through the data multiple times, each time creating data relating to a specific tile.
    # Once the tile's frame data has been generated, add all of the data to a dictionary called output.
    for mddEntry in mddData:
        isRAMB36 = False
        initPStrings = []
        basicInitStrings = []

        # Loop through the FASM lines, and filter out any that are not INIT, or INITP relating to the current tile
        # Sets a flag "isRAMB36", which tells the software to make slight changes later to accomadate the extra data
        for segDataLine in fasmLines:
            if re.search(mddEntry.tile + "\\.",
                         segDataLine) != None and re.search(
                             "\.INIT_", segDataLine) != None:
                hexStringList = list(
                    re.search("\'.*", segDataLine).group(0)[2:]
                )
                hexStringList.reverse()
                basicInitStrings.append(hexStringList)
                if re.search("Y1\.INIT_", segDataLine) != None:
                    isRAMB36 = True
            elif re.search(mddEntry.tile + "\\.",
                           segDataLine) != None and re.search(
                               "\.INITP_", segDataLine) != None:
                hexStringList = list(
                    re.search("\'.*", segDataLine).group(0)[2:]
                )
                hexStringList.reverse()
                initPStrings.append(hexStringList)

        # Variable used later to determine how many frame lines will be generated
        numOfInitStrings = len(basicInitStrings)

        with open(dbFile, 'r') as f:
            unfilteredSegData = f.readlines()

        basicSegData = make_2D_list(numOfInitStrings, 256)
        initPSegData = make_2D_list(len(initPStrings), 256)

        #TODO: This will need to be fixed later. It currently automatically assumes how many BRAM you have based upon the flag, but it should be able to automaticcaly detect this instead
        # Maybe I could partition it into Y0, Y1, and INITP, and do them separate? Or it might always work, because they suggest that it will be consistent in filling all of Y0 first... Ask the professor about it

        # Partitions out the segData from the db file into 2D array locations based upon its related bit in the init string
        for segDataLine in unfilteredSegData:
            initRegexResult = re.search("\.INIT_..", segDataLine)
            initPRegexResult = re.search("\.INITP_..", segDataLine)
            if initRegexResult != None:
                BRAMSide = re.search("Y[01]", segDataLine).group(0)
                initStringIndex = int(initRegexResult.group(0)[6:].lower(), 16)
                bitIndex = int(re.search("\[...", segDataLine).group(0)[1:])
                if initStringIndex < numOfInitStrings:
                    if BRAMSide == "Y1" and isRAMB36:
                        basicSegData[initStringIndex +
                                     64][bitIndex] = segDataLine
                    elif BRAMSide == "Y0":
                        basicSegData[initStringIndex][bitIndex] = segDataLine
            elif initPRegexResult != None:
                BRAMSide = re.search("Y[01]", segDataLine).group(0)
                initStringIndex = int(
                    initPRegexResult.group(0)[7:].lower(), 16
                )
                bitIndex = int(re.search("\[...", segDataLine).group(0)[1:])
                if initStringIndex < len(initPStrings):
                    if BRAMSide == "Y1" and isRAMB36:
                        initPSegData[initStringIndex +
                                     8][bitIndex] = segDataLine
                    elif BRAMSide == "Y0":
                        initPSegData[initStringIndex][bitIndex] = segDataLine

        reorderedBits = []
        if isRAMB36:
            reorderedBits = make_2D_list(numOfInitStrings, 320, True)
        else:
            reorderedBits = make_2D_list(numOfInitStrings * 2, 320, True)

        # Uses the init strings, and the segData from the db file to reorder the init strings into the
        # Order used in the frm files
        for i in range(len(basicSegData)):
            for j in range(len(basicSegData[i])):
                segDataRegexResult = re.search(" .*_.*",
                                               basicSegData[i][j]).group(0)
                dataBreak = segDataRegexResult.find('_')
                initStringIndex = int(segDataRegexResult[1:dataBreak])
                bitIndex = int(segDataRegexResult[dataBreak + 1:])
                if j < len(basicInitStrings[i]):
                    reorderedBits[initStringIndex][bitIndex] = str(
                        basicInitStrings[i][j]
                    )

        # Same as above but done for the INITP strings
        for i in range(len(initPSegData)):
            for j in range(len(initPSegData[i])):
                segDataRegexResult = re.search(" .*_.*",
                                               initPSegData[i][j]).group(0)
                dataBreak = segDataRegexResult.find('_')
                initStringIndex = int(segDataRegexResult[1:dataBreak])
                bitIndex = int(segDataRegexResult[dataBreak + 1:])
                if j < len(initPStrings[i]):
                    reorderedBits[initStringIndex][bitIndex] = str(
                        initPStrings[i][j]
                    )

        # Takes the 2D array of binary output from above, and converts it into a 2D list of Hexadecimal 32 bit words
        frameStrings = []
        for bitList in reorderedBits:
            hexString = hex(int("".join(bitList)[::-1], 2))[2:]
            hexStringList = []
            for i in range(len(hexString), 0, -1 * WORD_LENGTH):
                if i == 0:
                    break
                elif i < WORD_LENGTH:
                    hexStringList.append(
                        "0x" + ("0" * (WORD_LENGTH - i)) +
                        hexString[0:i].upper()
                    )
                else:
                    hexStringList.append(
                        "0x" + hexString[i - WORD_LENGTH:i].upper()
                    )
            frameStrings.append(hexStringList)

        with open(jsonFile) as f:
            jsonData = json.load(f)

        bramTile = jsonData[mddEntry.tile]["bits"]["BLOCK_RAM"]
        writeFile.write(mddEntry.tile + "\n" + str(bramTile) + "\n")

        with open(frmFile) as f:
            frmData = f.readlines()

        # Skips forward to the part of the frame file that we want
        frmFilePointer = 0
        while frmFilePointer < len(frmData):
            if re.search("^" + bramTile["baseaddr"], frmData[frmFilePointer]):
                break
            frmFilePointer += 1

        # Checks to see if the hexadecimal that we generated from the init strings and db files
        # Matches the actual data from the frm files
        failFlag = False
        for i in range(bramTile["frames"]):
            offset = 11 * (bramTile["offset"] + 1)
            for j in range(bramTile["words"]):
                data = frmData[frmFilePointer][offset:offset + 10]
                offset += 11
                if data == "0x00000000" or data == frameStrings[i][j]:
                    continue
                else:
                    failIndex = i
                    failOffset = j
                    failFlag = True
                    break
            frmFilePointer += 1
            if len(frmData[frmFilePointer]) == 0 or frmFilePointer == 4970:
                break
        if failFlag:
            writeFile.write("Output and frame file mismatch\n")
            writeFile.write(
                "Expected Token: {}, Received Token: {}\n".format(
                    data, frameStrings[failIndex][failOffset]
                )
            )
            failHex = hex(int(bramTile["baseaddr"], 16) + failIndex)[2:]
            failAddress = "0x" + ("0" * (WORD_LENGTH - len(failHex))) + failHex
            writeFile.write(
                "Location at X: {}, Y: {}\n".format(failAddress, failOffset)
            )
            testsWorked = False
        else:
            writeFile.write("Output and Expected match in all instances\n")

        # Outputs the hexadecimal that we generated to the outfile
        for i in range(len(frameStrings)):
            addressHex = hex(int(bramTile["baseaddr"], 16) + i)[2:]
            formattedAddress = "0x" + (
                "0" * (WORD_LENGTH - len(addressHex))
            ) + addressHex
            writeFile.write(
                "{}:\t{}\n".format(formattedAddress, frameStrings[i])
            )
        writeFile.write("\n\n")

        # Actually writes the hexadecimal to a dictionary keyed by the tile name
        if len(output) == 0:
            output = {mddEntry.tile: frameStrings}
        else:
            output[mddEntry.tile] = frameStrings
    if not testsWorked:
        writeFile.write("There were some tests that failed!\n")

    writeFile.close()


if __name__ == '__main__':
    if len(sys.argv) == 8:
        frame_pattern(
            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
            sys.argv[6], sys.argv[7]
        )
    else:
        print(
            "Usage: fasmFile dbFile memoryToRead mddFile jsonFile frmFile outfile"
        )
