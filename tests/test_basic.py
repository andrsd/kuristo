import subprocess


def test_cli_runs(tmp_path, minimal_workflow_yaml):
    wf = tmp_path / "workflow.yml"
    wf.write_text(minimal_workflow_yaml)

    # Call the CLI
    result = subprocess.run(
        ["kuristo", "--no-ansi", "run", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # assert "test-echo" in result.stdout
