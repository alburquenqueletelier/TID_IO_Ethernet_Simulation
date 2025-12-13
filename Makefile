# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= 
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile gen

gen:
	@echo "Generating Sphinx stubs..."
	@mkdir -p $(SOURCEDIR)/stubs

	# Stubs for files in the project root (main.py, sensor_control_app.py, etc)
	@find . -maxdepth 1 -type f -name '*.py' -print0 \
		| xargs -0 sphinx-autogen -o $(SOURCEDIR)/stubs

	# Stubs for the main package
	@find sensor_control_app -type f -name '*.py' -print0 \
		| xargs -0 sphinx-autogen -o $(SOURCEDIR)/stubs

	@echo "Done. Stubs saved in $(SOURCEDIR)/stubs"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
