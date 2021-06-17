# Copyright (C) 2017-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

all: format

PYTHON_SRCS=$(shell find . -path ./env -prune -o -path ./.git -prune -o -name "*.py" -print)

format: ${PYTHON_SRCS}
	yapf -i $?
