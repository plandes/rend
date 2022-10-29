## makefile automates the build and deployment for python projects

## build config

# type of project
PROJ_TYPE =		python
PROJ_MODULES =		git python-resources python-cli python-doc python-doc-deploy
INFO_TARGETS +=		appinfo
PY_DEP_POST_DEPS +=	modeldeps

# project specific
ENTRY =			./showfile


include ./zenbuild/main.mk

.PHONY:			appinfo
appinfo:
			@echo "app-resources-dir: $(RESOURCES_DIR)"

.PHONY:			modeldeps
modeldeps:
			if [ $$(uname) == "Darwin" ] ; then \
				$(PIP_BIN) install -r $(PY_SRC)/requirements-darwin.txt ; \
			fi

.PHONY:			testpdf
testpdf:
			( unset SHOWFILERC ; $(ENTRY) show test-resources/sample.pdf )
			( unset SHOWFILERC ; $(ENTRY) show http://example.com )

.PHONY:			config
config:
			( unset SHOWFILERC ; $(ENTRY) config )

.PHONY:			testall
testall:		test testpdf
