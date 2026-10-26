# Compile all .tex files in this directory.
# PDFs → here; aux/log/out → build/
#
#   make          build all PDFs
#   make clean    remove auxiliary files from build/
#   make distclean  remove build/ entirely

TEXFILES := $(wildcard *.tex)
PDFS := $(TEXFILES:.tex=.pdf)

.PHONY: all clean distclean

all: $(PDFS)

%.pdf: %.tex .latexmkrc
	latexmk -pdf $<

clean:
	latexmk -c -auxdir=build $(TEXFILES)

distclean: clean
	rm -rf build
