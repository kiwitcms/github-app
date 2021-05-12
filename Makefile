.PHONY: test
test:
	PYTHONWARNINGS=d EXECUTOR=standard AUTO_CREATE_SCHEMA='' coverage run \
	    --include "tcms_github_app/*.py" \
	    --omit "tcms_github_app/tests/*.py" \
	    ./manage.py test -v2 tcms_github_app.tests

FLAKE8_EXCLUDE=.git
.PHONY: flake8
flake8:
# ignore "line too long"
	@flake8 --exclude=$(FLAKE8_EXCLUDE) --ignore=E501 tcms_github_app/

KIWI_LINT_INCLUDE_PATH="../Kiwi/"

.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_LINT_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_LINT_INCLUDE_PATH); \
	fi

	PYTHONPATH=$(KIWI_LINT_INCLUDE_PATH) DJANGO_SETTINGS_MODULE="test_project.settings" \
	pylint --load-plugins=pylint_django --load-plugins=kiwi_lint -d similar-string \
	        -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	        *.py tcms_github_app/ test_project/ tcms_settings_dir/

.PHONY: test_for_missing_migrations
test_for_missing_migrations:
	./manage.py migrate
	./manage.py makemigrations --check

.PHONY: check
check: flake8 pylint test_for_missing_migrations test


.PHONY: messages
messages:
	./manage.py makemessages --locale en --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls tcms_github_app/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @
