## makefile automates the build and deployment for python projects

## build config

# type of project
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy
INFO_TARGETS +=		appinfo
ENTRY =			./showfile

include ./zenbuild/main.mk

.PHONY:			appinfo
appinfo:
			@echo "app-resources-dir: $(RESOURCES_DIR)"

.PHONY:			testpdf
testpdf:
			$(ENTRY) show --width 400 --height 600 test-resources/sample.pdf

.PHONY:			testall
testall:		test testpdf
