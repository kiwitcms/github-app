KIWI_INCLUDE_PATH=../Kiwi
PATH_TO_SITE_PACKAGES = $(shell python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())')

.PHONY: test
test:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	    rm -rf $(PATH_TO_SITE_PACKAGES)/test_project; \
	fi

	PYTHONPATH=$(KIWI_INCLUDE_PATH) PYTHONWARNINGS=d EXECUTOR=standard AUTO_CREATE_SCHEMA='' \
	KIWI_TENANTS_DOMAIN="example.org" coverage run \
	    --include "tcms_github_app/*.py" \
	    --omit "tcms_github_app/tests/*.py" \
	    ./manage.py test -v2 tcms_github_app.tests

FLAKE8_EXCLUDE=.git
.PHONY: flake8
flake8:
# ignore "line too long"
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=E501 tcms_github_app/

.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	    rm -rf $(PATH_TO_SITE_PACKAGES)/test_project; \
	fi

	PYTHONPATH=$(KIWI_INCLUDE_PATH) DJANGO_SETTINGS_MODULE="test_project.settings" \
	pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d similar-string \
	        -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	        *.py tcms_github_app/ test_project/ tcms_settings_dir/

.PHONY: test_for_missing_migrations
test_for_missing_migrations:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	    rm -rf $(PATH_TO_SITE_PACKAGES)/test_project; \
	fi

	PYTHONPATH=$(KIWI_INCLUDE_PATH) KIWI_TENANTS_DOMAIN="example.org" ./manage.py migrate
	PYTHONPATH=$(KIWI_INCLUDE_PATH) KIWI_TENANTS_DOMAIN="example.org" ./manage.py makemigrations --check

.PHONY: check
check: flake8 pylint test_for_missing_migrations test


.PHONY: messages
messages:
	./manage.py makemessages --locale en --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls tcms_github_app/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
