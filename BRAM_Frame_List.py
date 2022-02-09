#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


import sys
import os
import json
import patch_mem


def listTiles(mddFile, memoryToPrint, jsonFile):
    with open(jsonFile) as openFile:
        jsonData = json.load(openFile)
    mddData = patch_mem.readAndFilterMDDData(mddFile, memoryToPrint)
    for mdd in mddData:
        assert mdd.tile in jsonData
        entry = jsonData[mdd.tile]["bits"]["BLOCK_RAM"]
        print(
            "Tile: {},\tFrame Address: {},\t# of Frames: {:4d},\tWord Offset: {:3d},\t# of Words: {:4d}"
            .format(
                mdd.tile, entry["baseaddr"], entry["frames"], entry["offset"],
                entry["words"]
            )
        )


if __name__ == "__main__":
    assert len(sys.argv) == 4, \
        "Usage: mddFile memoryToPrint jsonFile"
    listTiles(sys.argv[1], sys.argv[2], sys.argv[3])
