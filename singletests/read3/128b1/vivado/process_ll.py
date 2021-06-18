#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

with open("test.ll") as f:
    lines = f.readlines()
    for lin in lines:
        tmp = lin.split()
        if len(tmp) != 6:
            continue
        if tmp[0] != "Bit":
            continue
        if tmp[4] != "Block=RAMB18_X0Y2":
            continue
        if "PARBIT" in lin:
            continue
        print(
            "{}\t{}\t{}\t{}".format(
                tmp[2],
                str(tmp[5].split(":")[1][3:]).rjust(8), tmp[3], tmp[1]
            )
        )
