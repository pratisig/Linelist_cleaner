import os
import subprocess
import pytest


def test_cli_help():
    result = subprocess.run(["python3", "-m", "linelist_cleaner.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Linelist Cleaner" in result.stdout


def test_cli_sample_and_inspect(tmp_path):
    sample_file = tmp_path / "test_cholera.csv"
    res_sample = subprocess.run(
        ["python3", "-m", "linelist_cleaner.cli", "sample", "-t", "cholera", "-o", str(sample_file)],
        capture_output=True,
        text=True
    )
    assert res_sample.returncode == 0
    assert os.path.exists(sample_file)

    # Inspect
    res_inspect = subprocess.run(
        ["python3", "-m", "linelist_cleaner.cli", "inspect", str(sample_file)],
        capture_output=True,
        text=True
    )
    assert res_inspect.returncode == 0
    assert "Mapped Epi Tag" in res_inspect.stdout

    # Clean
    cleaned_file = tmp_path / "test_cholera_cleaned.csv"
    res_clean = subprocess.run(
        ["python3", "-m", "linelist_cleaner.cli", "clean", str(sample_file), "-o", str(cleaned_file)],
        capture_output=True,
        text=True
    )
    assert res_clean.returncode == 0
    assert os.path.exists(cleaned_file)
