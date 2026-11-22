"""CLI-level tests for gen.py — assert exit codes through subprocess."""
import subprocess
import sys
from pathlib import Path

GEN = str(Path(__file__).parent / "gen.py")

TEMPLATE = "<html><title>{{title}}</title>{{body}}</html>"
POST = "# Hello\n\nA **bold** word.\n"


def run(*args, cwd):
    return subprocess.run(
        [sys.executable, GEN, *map(str, args)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def make_template(tmp_path):
    p = tmp_path / "template.html"
    p.write_text(TEMPLATE)
    return p


def make_src(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "hello.md").write_text(POST)
    return d


def assert_clean_failure(result):
    assert result.returncode == 1, result.stderr
    assert "Traceback" not in result.stderr
    error_lines = [line for line in result.stderr.splitlines() if line.strip()]
    assert len(error_lines) == 1, result.stderr


def test_missing_src_exits_one(tmp_path):
    tpl = make_template(tmp_path)
    result = run(tmp_path / "no-such-src", tmp_path / "out", "--template", tpl, cwd=tmp_path)
    assert_clean_failure(result)
    assert "Error" in result.stderr  # exception type is present, not swallowed


def test_missing_template_exits_one(tmp_path):
    src = make_src(tmp_path)
    result = run(src, tmp_path / "out", "--template", tmp_path / "missing.html", cwd=tmp_path)
    assert_clean_failure(result)
    assert "Error" in result.stderr


def test_unwritable_out_exits_one(tmp_path):
    src = make_src(tmp_path)
    tpl = make_template(tmp_path)
    blocked = tmp_path / "out-is-a-file"
    blocked.write_text("not a directory")
    result = run(src, blocked, "--template", tpl, cwd=tmp_path)
    assert_clean_failure(result)


def test_success_exits_zero(tmp_path):
    src = make_src(tmp_path)
    tpl = make_template(tmp_path)
    out = tmp_path / "out"
    result = run(src, out, "--template", tpl, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (out / "hello.html").exists()
    assert "done" in result.stdout


def test_version_prints_package_version(tmp_path):
    result = run("--version", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "0.1.0" in result.stdout


def test_md_named_directory_is_ignored(tmp_path):
    src = make_src(tmp_path)
    (src / "drafts.md").mkdir()
    tpl = make_template(tmp_path)
    out = tmp_path / "out"
    result = run(src, out, "--template", tpl, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "built hello.md" in result.stdout
    assert "done" in result.stdout
    assert sorted(p.name for p in out.iterdir()) == ["hello.html"]


def test_non_markdown_files_and_directories_are_ignored(tmp_path):
    src = make_src(tmp_path)
    (src / "notes.txt").write_text("ignored")
    (src / "archive").mkdir()
    tpl = make_template(tmp_path)
    out = tmp_path / "out"
    result = run(src, out, "--template", tpl, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert sorted(p.name for p in out.iterdir()) == ["hello.html"]


def test_heading_levels_three_through_six(tmp_path):
    src = make_src(tmp_path)
    (src / "headings.md").write_text("# Title\n\n## Two\n\n### Deep\n\n###### Six\n")
    tpl = make_template(tmp_path)
    out = tmp_path / "out"
    result = run(src, out, "--template", tpl, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    html = (out / "headings.html").read_text()
    assert "<h2>Two</h2>" in html
    assert "<h3>Deep</h3>" in html
    assert "<h6>Six</h6>" in html


def test_uppercase_md_extension_is_built(tmp_path):
    src = make_src(tmp_path)
    (src / "Notes.MD").write_text("# Notes\n\nUpper extension.\n")
    tpl = make_template(tmp_path)
    out = tmp_path / "out"
    result = run(src, out, "--template", tpl, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "built Notes.MD" in result.stdout
    assert sorted(p.name for p in out.iterdir()) == ["Notes.html", "hello.html"]
    assert "<h1>Notes</h1>" in (out / "Notes.html").read_text()
