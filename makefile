#@meta {author: "Paul Landes"}
#@meta {desc: "build, test and deploy automation", date: "2025-06-22"}


## Build config
#
# type of project
PROJ_TYPE =		python
PROJ_MODULES =		python/doc python/package python/deploy
PY_TEST_ALL_TARGETS +=	runshow
INFO_TARGETS +=		appinfo


## Includes
#
include ./zenbuild/main.mk


## Targets
#
.PHONY:			appinfo
appinfo:
			@echo "app-resources-dir: $(RESOURCES_DIR)"

# print the isolated configuration
.PHONY:			runconfig
runconfig:
			@$(MAKE) $(PY_MAKE_ARGS) invokeisolate ARG=config


# run the harness isolated from the environment (variables)
.PHONY:			invokeisolate
invokeisolate:
			@( unset RENDRC ; unset ZENSOLSRC ; \
			   $(MAKE) $(PY_MAKE_ARGS) pyharn ARG="$(ARG)" )

# show a PDF file
.PHONY:			runshowpdf
runshowpdf:
			@$(MAKE) $(PY_MAKE_ARGS) invokeisolate \
				ARG="show test-resources/sample.pdf"


# show tabular data
.PHONY:			runshowcsv
runshowcsv:
			@$(MAKE) $(PY_MAKE_ARGS) invokeisolate \
				ARG="show test-resources/states.csv"

# show a website
.PHONY:			runshowwebsite
runshowwebsite:
			@$(MAKE) $(PY_MAKE_ARGS) invokeisolate \
				ARG="show http://example.com"

.PHONY:			runshow
runshow:		runshowpdf runshowcsv runshowwebsite
