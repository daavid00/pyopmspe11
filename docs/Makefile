SPHINXOPTS  ?=
SPHINXBUILD ?= sphinx-build
SOURCEDIR    = text
BUILDDIR     = _build
APIDIR       = text/api

.PHONY: help clean api html linkcheck github

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf "$(BUILDDIR)"

api:
	@mkdir -p "$(APIDIR)"
	sphinx-apidoc --private -e -f -o "$(APIDIR)" ../src/pyopmspe11

html: api
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

linkcheck:
	@$(SPHINXBUILD) -M linkcheck "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

github: html
	cp -a "$(BUILDDIR)/html/." .
