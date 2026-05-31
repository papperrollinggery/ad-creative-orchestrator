.PHONY: check demo-transcript install-dev install-smoke release-check validate dashboards clean

PYTHON ?= python3

check:
	$(PYTHON) tools/run_checks.py

demo-transcript:
	$(PYTHON) tools/render_demo_transcript.py

install-dev:
	$(PYTHON) -m pip install -e .

install-smoke:
	tmp_dir=$$(mktemp -d /tmp/adco-install-XXXXXX); \
	$(PYTHON) -m venv $$tmp_dir/venv; \
	$$tmp_dir/venv/bin/python -m pip install --upgrade pip >/dev/null; \
	$$tmp_dir/venv/bin/python -m pip install -e . --no-deps >/dev/null; \
	$$tmp_dir/venv/bin/adco --help >/dev/null; \
	$$tmp_dir/venv/bin/adco-init $$tmp_dir/project >/dev/null; \
	$$tmp_dir/venv/bin/adco-validate $$tmp_dir/project; \
	$$tmp_dir/venv/bin/adco-check; \
	echo "INSTALL_SMOKE=PASS $$tmp_dir"

release-check: check install-smoke
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
