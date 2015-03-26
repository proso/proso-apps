TEST_DIR=$(CURDIR)/test
RESOURCES_DIR=$(CURDIR)/resources

PEP8=pep8 --ignore=E501,E225,E123,E128
APPS=proso_common proso_feedback proso_flashcards proso_models proso_questions proso_questions_client proso_user
GRUNT_APPS=proso_questions_client

VERSION_FULL:=$(shell grep "VERSION = '.*'" proso/release.py | awk -F ' = ' '{print $$2}' | tr -d "'")
VERSION:=$(shell echo $(VERSION_FULL) | awk -F '-' '{print $$1}')
VERSION_SUFFIX:=$(shell echo $(VERSION_FULL) | awk -F '-' '{print $$2}')
MAJOR_VERSION=$(word 1,$(subst ., ,$(VERSION)))
MINOR_VERSION=$(word 2,$(subst ., ,$(VERSION)))
MICRO_VERSION=$(word 3,$(subst ., ,$(VERSION)))


################################################################################

upload: grunt test register
	python setup.py sdist upload

register:
	python setup.py register


################################################################################

test: reinstall
	python -m unittest discover -p test_*.py -s proso
	for APP in $(APPS); do \
		python manage.py test $$APP --traceback; \
	done;

reinstall: check uninstall install

develop: check
	python setup.py develop

install: check
	python setup.py sdist
	pip install dist/proso-apps-$(VERSION_FULL)*

uninstall:
	pip uninstall --yes proso-apps

check:
	flake8 --ignore=E501,E225,E123,E128 --exclude=*/migrations/*.py,*/static/bower_components proso_models $(APPS)

grunt:
	for APP in $(GRUNT_APPS); do \
		cd $${APP}; \
		npm install; \
		grunt deploy; \
		cd -; \
	done;


################################################################################

release:
	$(MAKE) MILESTONE="$(MILESTONE)" milestone; \
	if [ "$(MILESTONE)" ]; then \
		$(MAKE) snapshot; \
		git add proso/release.py; \
		$(MAKE) commit-back-to-snapshot; \
	else \
		$(MAKE) upload; \
		$(MAKE) increase-minor; \
		$(MAKE) snapshot; \
		git add proso/release.py; \
		$(MAKE) commit-start-working; \
	fi; \

milestone:
	MAJOR=$(MAJOR_VERSION); \
	MINOR=$(MINOR_VERSION); \
	MICRO=$(MICRO_VERSION); \
	if [ "$(MILESTONE)" ]; then \
		SUFFIX="-$(MILESTONE)"; \
	else \
		SUFFIX=""; \
	fi; \
	sed -i "s/VERSION = '.*'/VERSION = '$${MAJOR}.$${MINOR}.$${MICRO}$${SUFFIX}'/g" proso/release.py; \
	$(MAKE) publish-version; \

commit-back-to-snapshot:
	git commit -m 'back to $(VERSION_FULL)'; \

commit-start-working:
		git commit -m 'start working on $(VERSION)'; \

snapshot:
	MAJOR=$(MAJOR_VERSION); \
	MINOR=$(MINOR_VERSION); \
	MICRO=$(MICRO_VERSION); \
	sed -i "s/VERSION = '.*'/VERSION = '$${MAJOR}.$${MINOR}.$${MICRO}-SNAPSHOT'/g" proso/release.py; \

publish-version:
	git reset
	git add proso/release.py
	git commit -m 'release a new version $(VERSION_FULL)'
	git tag release-$(VERSION_FULL)
	git push origin release-$(VERSION_FULL)

increase-major:
	MAJOR=`expr $(MAJOR_VERSION) + 1`; \
	MINOR=0; \
	MICRO=0; \
	sed -i "s/VERSION = '.*'/VERSION = '$${MAJOR}.$${MINOR}.$${MICRO}'/g" proso/release.py; \

increase-minor:
	MAJOR=$(MAJOR_VERSION); \
	MINOR=`expr $(MINOR_VERSION) + 1`; \
	MICRO=0; \
	sed -i "s/VERSION = '.*'/VERSION = '$${MAJOR}.$${MINOR}.$${MICRO}'/g" proso/release.py;

increase-micro:
	MAJOR=$(MAJOR_VERSION); \
	MINOR=$(MINOR_VERSION); \
	MICRO=`expr $(MICRO_VERSION) + 1`; \
	sed -i "s/VERSION = '.*'/VERSION = '$${MAJOR}.$${MINOR}.$${MICRO}'/g" proso/release.py;
