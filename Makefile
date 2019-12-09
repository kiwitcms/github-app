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

.PHONY: pylint
pylint:
	pylint --load-plugins=pylint_django -d missing-docstring -d duplicate-code *.py \
	    -d wildcard-import -d unused-wildcard-import tcms_github_app/ test_project/

.PHONY: test_for_missing_migrations
test_for_missing_migrations:
	./manage.py migrate
	./manage.py makemigrations --check

.PHONY: check
check: flake8 pylint test_for_missing_migrations test
