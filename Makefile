.PHONY: check validate dashboards clean

PYTHON ?= python3

check:
	$(PYTHON) tools/run_checks.py

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
