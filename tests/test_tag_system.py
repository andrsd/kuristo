import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import kuristo.utils as utils


@pytest.fixture
def temp_log_dir():
    """Create a temporary log directory for testing"""
    with TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)
        runs_dir = log_dir / "runs"
        runs_dir.mkdir(parents=True)
        yield log_dir


@pytest.fixture
def sample_runs(temp_log_dir):
    """Create sample runs for testing"""
    runs_dir = temp_log_dir / "runs"

    # Create three sample runs
    run_ids = [
        "20260220-172532-000001",
        "20260220-172533-000002",
        "20260220-172536-000003",
    ]

    for run_id in run_ids:
        run_dir = runs_dir / run_id
        run_dir.mkdir()
        # Create a dummy report file
        (run_dir / "report.yaml").write_text("results: []\n")

    return temp_log_dir, run_ids


class TestTagNameValidation:
    """Test tag name validation"""

    def test_valid_tag_names(self):
        """Test that valid tag names are accepted"""
        valid_names = [
            "v1.0",
            "v1",
            "baseline",
            "v1.0",
            "v1-0",
            "test123",
            "TEST",
            "test_tag_name",
            "test-tag-name",
            "v1.0.0",
            "release.1.2.3",
        ]
        for name in valid_names:
            assert utils.validate_tag_name(name), f"'{name}' should be valid"

    def test_invalid_tag_names(self):
        """Test that invalid tag names are rejected"""
        invalid_names = [
            "test/tag",  # Slash not allowed
            "test tag",  # Space not allowed
            "test@tag",  # @ not allowed
            "test#tag",  # # not allowed
            "",  # Empty string
            "test:tag",  # Colon not allowed
            "test$tag",  # $ not allowed
        ]
        for name in invalid_names:
            assert not utils.validate_tag_name(name), f"'{name}' should be invalid"


class TestCreateTag:
    """Test tag creation"""

    def test_create_tag_latest_run(self, sample_runs):
        """Test creating a tag for the latest run"""
        log_dir, run_ids = sample_runs
        runs_dir = log_dir / "runs"

        # Create latest symlink
        latest_link = runs_dir / "latest"
        latest_link.symlink_to(run_ids[2], target_is_directory=True)

        # Create a tag
        utils.create_tag(log_dir, "v1.0", run_ids[2])

        # Verify tag was created
        tag_path = log_dir / "tags" / "v1.0"
        assert tag_path.exists()
        assert tag_path.is_symlink()

        # Verify symlink points to correct run
        assert tag_path.resolve().name == run_ids[2]

    def test_create_tag_specific_run(self, sample_runs):
        """Test creating a tag for a specific run"""
        log_dir, run_ids = sample_runs

        utils.create_tag(log_dir, "baseline", run_ids[0])

        tag_path = log_dir / "tags" / "baseline"
        assert tag_path.exists()
        assert tag_path.resolve().name == run_ids[0]

    def test_create_tag_nonexistent_run(self, sample_runs):
        """Test error when tagging a non-existent run"""
        log_dir, _ = sample_runs

        with pytest.raises(RuntimeError, match="does not exist"):
            utils.create_tag(log_dir, "v1.0", "nonexistent-run")

    def test_invalid_tag_name(self, sample_runs):
        """Test error with invalid tag name"""
        log_dir, run_ids = sample_runs

        with pytest.raises(RuntimeError, match="Invalid tag name"):
            utils.create_tag(log_dir, "invalid/tag", run_ids[0])

    def test_overwrite_existing_tag(self, sample_runs):
        """Test that creating a tag with same name overwrites the old one"""
        log_dir, run_ids = sample_runs

        # Create initial tag pointing to first run
        utils.create_tag(log_dir, "latest_release", run_ids[0])

        # Overwrite with new tag pointing to second run
        utils.create_tag(log_dir, "latest_release", run_ids[1])

        tag_path = log_dir / "tags" / "latest_release"
        assert tag_path.resolve().name == run_ids[1]


class TestDeleteTag:
    """Test tag deletion"""

    def test_delete_existing_tag(self, sample_runs):
        """Test deleting an existing tag"""
        log_dir, run_ids = sample_runs

        # Create a tag
        utils.create_tag(log_dir, "v1.0", run_ids[0])

        # Delete the tag
        utils.delete_tag(log_dir, "v1.0")

        # Verify tag was deleted
        tag_path = log_dir / "tags" / "v1.0"
        assert not tag_path.exists()
        assert not tag_path.is_symlink()

    def test_delete_nonexistent_tag(self, sample_runs):
        """Test error when deleting a non-existent tag"""
        log_dir, _ = sample_runs

        with pytest.raises(RuntimeError, match="does not exist"):
            utils.delete_tag(log_dir, "nonexistent")

    def test_delete_tag_preserves_run(self, sample_runs):
        """Test that deleting a tag does not delete the run"""
        log_dir, run_ids = sample_runs

        # Create a tag
        utils.create_tag(log_dir, "v1.0", run_ids[0])

        # Delete the tag
        utils.delete_tag(log_dir, "v1.0")

        # Verify the run still exists
        run_path = log_dir / "runs" / run_ids[0]
        assert run_path.exists()


class TestListTags:
    """Test tag listing"""

    def test_list_empty_tags(self, sample_runs):
        """Test listing tags when none exist"""
        log_dir, _ = sample_runs

        tags = utils.list_tags(log_dir)

        assert tags == []

    def test_list_multiple_tags(self, sample_runs):
        """Test listing multiple tags"""
        log_dir, run_ids = sample_runs

        # Create multiple tags
        utils.create_tag(log_dir, "v1.0", run_ids[0])
        utils.create_tag(log_dir, "baseline", run_ids[1])
        utils.create_tag(log_dir, "latest_dev", run_ids[2])

        tags = utils.list_tags(log_dir)

        # Should return list of tuples sorted by tag name
        assert len(tags) == 3
        tag_names = [name for name, _ in tags]
        assert tag_names == sorted(tag_names)
        assert ("v1.0", run_ids[0]) in tags
        assert ("baseline", run_ids[1]) in tags
        assert ("latest_dev", run_ids[2]) in tags

    def test_list_tags_sorted(self, sample_runs):
        """Test that listed tags are sorted by name"""
        log_dir, run_ids = sample_runs

        # Create tags in non-alphabetical order
        utils.create_tag(log_dir, "zebra", run_ids[0])
        utils.create_tag(log_dir, "apple", run_ids[1])
        utils.create_tag(log_dir, "banana", run_ids[2])

        tags = utils.list_tags(log_dir)
        tag_names = [name for name, _ in tags]

        assert tag_names == ["apple", "banana", "zebra"]


class TestGetTagsForRun:
    """Test getting tags for a specific run"""

    def test_get_tags_for_untagged_run(self, sample_runs):
        """Test getting tags for a run with no tags"""
        log_dir, run_ids = sample_runs

        tags = utils.get_tags_for_run(log_dir, run_ids[0])

        assert tags == []

    def test_get_single_tag_for_run(self, sample_runs):
        """Test getting a single tag for a run"""
        log_dir, run_ids = sample_runs

        utils.create_tag(log_dir, "v1.0", run_ids[0])

        tags = utils.get_tags_for_run(log_dir, run_ids[0])

        assert tags == ["v1.0"]

    def test_get_multiple_tags_for_run(self, sample_runs):
        """Test getting multiple tags for the same run"""
        log_dir, run_ids = sample_runs

        utils.create_tag(log_dir, "v1.0", run_ids[0])
        utils.create_tag(log_dir, "baseline", run_ids[0])
        utils.create_tag(log_dir, "important", run_ids[0])

        tags = utils.get_tags_for_run(log_dir, run_ids[0])

        assert len(tags) == 3
        assert set(tags) == {"v1.0", "baseline", "important"}


class TestIsRunTagged:
    """Test checking if a run is tagged"""

    def test_untagged_run(self, sample_runs):
        """Test that untagged run returns False"""
        log_dir, run_ids = sample_runs

        assert not utils.is_run_tagged(log_dir, run_ids[0])

    def test_tagged_run(self, sample_runs):
        """Test that tagged run returns True"""
        log_dir, run_ids = sample_runs

        utils.create_tag(log_dir, "v1.0", run_ids[0])

        assert utils.is_run_tagged(log_dir, run_ids[0])


class TestPruneOldRunsWithTags:
    """Test that prune_old_runs respects tags"""

    def test_prune_protects_tagged_runs(self, sample_runs):
        """Test that tagged runs are not deleted during pruning"""
        log_dir, run_ids = sample_runs

        # Set specific modification times to ensure predictable sort order
        import time
        runs_dir = log_dir / "runs"
        time.sleep(0.01)
        (runs_dir / run_ids[1]).touch()
        time.sleep(0.01)
        (runs_dir / run_ids[2]).touch()

        # Tag the oldest run
        utils.create_tag(log_dir, "v1.0", run_ids[0])

        # Prune keeping only last 2 runs
        utils.prune_old_runs(log_dir, keep_last_n=2)

        # The oldest run should still exist because it's tagged
        run_path = log_dir / "runs" / run_ids[0]
        assert run_path.exists()

        # The two newest runs should still exist (we're keeping 2)
        assert (log_dir / "runs" / run_ids[1]).exists()
        assert (log_dir / "runs" / run_ids[2]).exists()

    def test_prune_deletes_untagged_old_runs(self, sample_runs):
        """Test that untagged old runs are deleted during pruning"""
        log_dir, run_ids = sample_runs

        # Tag only the middle run
        utils.create_tag(log_dir, "v1.0", run_ids[1])

        # Prune keeping only last 1 run (by modification time)
        # We need to set different mtimes
        runs_dir = log_dir / "runs"
        import time
        time.sleep(0.01)
        (runs_dir / run_ids[1]).touch()
        time.sleep(0.01)
        (runs_dir / run_ids[2]).touch()

        utils.prune_old_runs(log_dir, keep_last_n=1)

        # The newest run should exist
        assert (runs_dir / run_ids[2]).exists()

        # The tagged run should exist despite being old
        assert (runs_dir / run_ids[1]).exists()

        # The oldest untagged run should be deleted
        assert not (runs_dir / run_ids[0]).exists()
