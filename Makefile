.PHONY: check demo-transcript dist-check install-dev install-smoke package-smoke release-check validate dashboards clean

PYTHON ?= python3

check:
	$(PYTHON) tools/run_checks.py

demo-transcript:
	$(PYTHON) tools/render_demo_transcript.py

dist-check:
	$(PYTHON) tools/check_distribution.py

install-dev:
	$(PYTHON) -m pip install -e .

install-smoke:
	tmp_dir=$$(mktemp -d /tmp/adco-install-XXXXXX); \
	$(PYTHON) -m venv $$tmp_dir/venv; \
	$$tmp_dir/venv/bin/python -m pip install --upgrade pip >/dev/null; \
	$$tmp_dir/venv/bin/python -m pip install -e . --no-deps >/dev/null; \
	$$tmp_dir/venv/bin/adco --help >/dev/null; \
	$$tmp_dir/venv/bin/adco --version; \
	$$tmp_dir/venv/bin/adco doctor; \
	$$tmp_dir/venv/bin/adco-init $$tmp_dir/project >/dev/null; \
	$$tmp_dir/venv/bin/adco demo $$tmp_dir/demo --no-open; \
	$$tmp_dir/venv/bin/adco support-bundle $$tmp_dir/project; \
	$$tmp_dir/venv/bin/adco open-dashboard $$tmp_dir/project --no-open; \
	$$tmp_dir/venv/bin/adco-validate $$tmp_dir/project; \
	$$tmp_dir/venv/bin/adco-check; \
	echo "INSTALL_SMOKE=PASS $$tmp_dir"

package-smoke:
	tmp_dir=$$(mktemp -d /tmp/adco-package-XXXXXX); \
	$(PYTHON) -m venv $$tmp_dir/venv; \
	$$tmp_dir/venv/bin/python -m pip install --upgrade pip >/dev/null; \
	$$tmp_dir/venv/bin/python -m pip install . --no-deps >/dev/null; \
	$$tmp_dir/venv/bin/adco --version; \
	$$tmp_dir/venv/bin/adco doctor; \
	$$tmp_dir/venv/bin/adco-init $$tmp_dir/init-project >/dev/null; \
	$$tmp_dir/venv/bin/adco-validate $$tmp_dir/init-project >/dev/null; \
	$$tmp_dir/venv/bin/adco demo $$tmp_dir/demo --no-open; \
	$$tmp_dir/venv/bin/adco sample $$tmp_dir/project >/dev/null; \
	$$tmp_dir/venv/bin/adco support-bundle $$tmp_dir/project; \
	$$tmp_dir/venv/bin/adco open-dashboard $$tmp_dir/project --no-open; \
	$$tmp_dir/venv/bin/adco-validate $$tmp_dir/project; \
	$$tmp_dir/venv/bin/adco-check; \
	echo "PACKAGE_SMOKE=PASS $$tmp_dir"

release-check: check dist-check install-smoke package-smoke
	$(PYTHON) tools/render_demo_transcript.py --check
	echo "RELEASE_CHECK=PASS"

validate:
	$(PYTHON) tools/validate_project.py templates/project
	$(PYTHON) tools/validate_project.py examples/moncler_protocol_dry_run
	$(PYTHON) tools/validate_project.py examples/simulated_qingling_outdoor_launch

dashboards:
	$(PYTHON) tools/ad_creative_operator.py audit-dashboard examples/moncler_protocol_dry_run --render
	$(PYTHON) tools/ad_creative_operator.py audit-dashboard examples/simulated_qingling_outdoor_launch --render

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf build dist tools/*.egg-info
