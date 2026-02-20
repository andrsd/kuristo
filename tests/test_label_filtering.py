from pathlib import Path
from kuristo.job_spec import JobSpec, parse_workflow_files
from kuristo.utils import filter_specs_by_labels


class TestLabelFiltering:
    """Test label filtering functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        # Create sample specs with and without labels
        self.spec_with_smoke = JobSpec(
            description="Smoke test",
            steps=[],
            labels=["smoke", "quick"]
        )
        self.spec_with_smoke.set_id("smoke-test")
        self.spec_with_smoke.set_file_name("test.yaml")

        self.spec_with_integration = JobSpec(
            description="Integration test",
            steps=[],
            labels=["integration", "slow"]
        )
        self.spec_with_integration.set_id("integration-test")
        self.spec_with_integration.set_file_name("test.yaml")

        self.spec_without_labels = JobSpec(
            description="No labels",
            steps=[],
            labels=None
        )
        self.spec_without_labels.set_id("no-label-test")
        self.spec_without_labels.set_file_name("test.yaml")

        self.spec_with_empty_labels = JobSpec(
            description="Empty labels",
            steps=[],
            labels=[]
        )
        self.spec_with_empty_labels.set_id("empty-label-test")
        self.spec_with_empty_labels.set_file_name("test.yaml")

    def test_filter_no_labels_returns_all(self):
        """When no labels specified, all specs are returned"""
        specs = [self.spec_with_smoke, self.spec_without_labels]
        filtered, total, count = filter_specs_by_labels(specs, None)
        assert count == 2
        assert total == 2
        assert len(filtered) == 2

    def test_filter_empty_list_returns_all(self):
        """When empty label list specified, all specs are returned"""
        specs = [self.spec_with_smoke, self.spec_without_labels]
        filtered, total, count = filter_specs_by_labels(specs, [])
        assert count == 2
        assert total == 2
        assert len(filtered) == 2

    def test_filter_single_label_exact_match(self):
        """Filter by single label matches jobs with that label"""
        specs = [self.spec_with_smoke, self.spec_with_integration, self.spec_without_labels]
        filtered, total, count = filter_specs_by_labels(specs, ["smoke"])
        assert count == 1
        assert total == 3
        assert len(filtered) == 1
        assert filtered[0].id == "smoke-test"

    def test_filter_or_logic_multiple_labels(self):
        """Multiple labels use OR logic"""
        specs = [self.spec_with_smoke, self.spec_with_integration, self.spec_without_labels]
        filtered, total, count = filter_specs_by_labels(specs, ["smoke", "integration"])
        assert count == 2
        assert total == 3
        assert len(filtered) == 2
        assert set(spec.id for spec in filtered) == {"smoke-test", "integration-test"}

    def test_filter_no_matches(self):
        """Filter with non-matching label returns empty"""
        specs = [self.spec_with_smoke, self.spec_with_integration]
        filtered, total, count = filter_specs_by_labels(specs, ["nonexistent"])
        assert count == 0
        assert total == 2
        assert len(filtered) == 0

    def test_filter_excludes_jobs_without_labels(self):
        """Jobs without labels are excluded when filter is active"""
        specs = [self.spec_with_smoke, self.spec_without_labels]
        filtered, total, count = filter_specs_by_labels(specs, ["smoke"])
        assert count == 1
        assert total == 2
        assert len(filtered) == 1
        assert filtered[0].id == "smoke-test"

    def test_filter_excludes_jobs_with_empty_labels(self):
        """Jobs with empty labels list are excluded when filter is active"""
        specs = [self.spec_with_smoke, self.spec_with_empty_labels]
        filtered, total, count = filter_specs_by_labels(specs, ["smoke"])
        assert count == 1
        assert total == 2
        assert len(filtered) == 1
        assert filtered[0].id == "smoke-test"

    def test_filter_label_from_first_label(self):
        """Filter matches label from first position"""
        specs = [self.spec_with_smoke]
        filtered, total, count = filter_specs_by_labels(specs, ["smoke"])
        assert count == 1
        assert len(filtered) == 1

    def test_filter_label_from_second_label(self):
        """Filter matches label from second position"""
        specs = [self.spec_with_smoke]
        filtered, total, count = filter_specs_by_labels(specs, ["quick"])
        assert count == 1
        assert len(filtered) == 1

    def test_filter_case_sensitive(self):
        """Label matching is case sensitive"""
        specs = [self.spec_with_smoke]
        filtered, total, count = filter_specs_by_labels(specs, ["Smoke"])
        assert count == 0
        assert len(filtered) == 0

    def test_parse_and_filter_from_file(self):
        """Test parsing and filtering from actual workflow file"""
        test_file = Path("tests/assets/test_labels/ktests.yaml")
        if test_file.exists():
            specs = parse_workflow_files([test_file])

            # All specs should have labels or be labelless
            assert len(specs) == 4

            # Filter by smoke
            filtered, total, count = filter_specs_by_labels(specs, ["smoke"])
            assert count == 2

            # Filter by smoke or integration
            filtered, total, count = filter_specs_by_labels(specs, ["smoke", "integration"])
            assert count == 3

            # Filter by nonexistent
            filtered, total, count = filter_specs_by_labels(specs, ["nonexistent"])
            assert count == 0
