all: format

PYTHON_SRCS=$(shell find . -path ./env -prune -o -path ./.git -prune -o -name "*.py" -print)

format: ${PYTHON_SRCS}
	yapf -i $?
