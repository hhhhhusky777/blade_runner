"""Build the local review ZIP from a fixed file allowlist; never publish it.

Run with the project's Python after dependency installation. The historical
chapters' exported copies rebind lab links; the frozen whiteboard stays identical.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = (
    ".github/spec-driven-delivery/solution-whiteboard.md",
    "README.md",
    "docs/reports/evidence/conversation-time-audit.json",
    "docs/reports/evidence/conversation-turn-times.csv",
    "docs/reports/evidence/delivery-evidence.json",
    "docs/reports/evidence/historical-index.json",
    "docs/reports/evidence/historical/stage1-task-metrics.json",
    "docs/reports/evidence/historical/stage2-task-metrics.json",
    "docs/reports/evidence/historical/stage3-task-metrics.json",
    "docs/reports/evidence/issues-readback.json",
    "docs/reports/evidence/migration-runner-focused.json",
    "docs/reports/evidence/migration-sources.json",
    "docs/reports/evidence/migration-stage1.json",
    "docs/reports/evidence/migration-typed.json",
    "docs/reports/evidence/regression-inventory.json",
    "docs/reports/recruitment-comparisons.png",
    "docs/reports/recruitment-delivery-report.md",
    "docs/reports/recruitment-work-time.png",
    "docs/reports/stage-1-report.md",
    "docs/reports/stage-2-report.md",
    "docs/reports/stage-2-timing.png",
    "docs/reports/stage-3-report.md",
    "docs/reports/stage-3-timing.png",
    "game_solver/.env.example",
    "game_solver/api_client/__init__.py",
    "game_solver/api_client/client.py",
    "game_solver/api_client/models.py",
    "game_solver/pyproject.toml",
    "game_solver/solver/__init__.py",
    "game_solver/solver/__main__.py",
    "game_solver/solver/api.py",
    "game_solver/solver/capital.py",
    "game_solver/solver/child.py",
    "game_solver/solver/reference.py",
    "game_solver/solver/resource_guidance.py",
    "game_solver/solver/runner.py",
    "game_solver/solver/samples.json",
    "game_solver/solver/stage1.py",
    "game_solver/solver/stage1_preset.py",
    "game_solver/solver/stage2.py",
    "game_solver/solver/stage2_reference.py",
    "game_solver/solver/stage3.py",
    "game_solver/solver/stage3_reference.py",
    "game_solver/tests/__init__.py",
    "game_solver/tests/fixtures/server-regressions.json",
    "game_solver/tests/fixtures/stage1-basic.json",
    "game_solver/tests/fixtures/stage1-controls.json",
    "game_solver/tests/fixtures/stage2-capabilities.json",
    "game_solver/tests/fixtures/stage2-controls.json",
    "game_solver/tests/fixtures/stage2-fixtures.json",
    "game_solver/tests/fixtures/stage3-capabilities.json",
    "game_solver/tests/fixtures/stage3-controls.json",
    "game_solver/tests/fixtures/stage3-fixtures.json",
    "game_solver/tests/run_regressions.py",
    "game_solver/tests/test_package_boundaries.py",
    "game_solver/tests/test_runner_attempt.py",
    "game_solver/tests/test_runner_creation_retries.py",
    "game_solver/tests/test_runner_creation_timeout.py",
    "game_solver/tests/test_runner_loop.py",
    "game_solver/tests/test_runner_recovery.py",
    "game_solver/tests/test_runner_stage2.py",
    "game_solver/tests/test_runner_stage3.py",
    "game_solver/tests/test_runner_verification.py",
    "game_solver/tests/test_stage1.py",
    "game_solver/tests/test_stage2.py",
    "game_solver/tests/test_stage3.py",
    "game_solver/uv.lock",
    "submit.sh",
    "tools/build_delivery.py",
)
# Final-gate output is included once it exists, never replaced with an invented pass.
FINAL_EVIDENCE = ("docs/reports/evidence/migration-full.json",)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(output):
    """Write an allowlisted archive, content inventory and external ZIP checksum."""
    from dotenv import dotenv_values

    config = {**dotenv_values(ROOT / "game_solver/.env"), **os.environ}
    secrets = [config[k].encode() for k in ("GAME_SERVER_TOKEN", "ARBITER_TOKEN") if config.get(k)]
    index = json.loads((ROOT / "docs/reports/evidence/historical-index.json").read_text())[
        "sources"
    ]
    payload = {}
    inventory = {}
    selected = list(FILES) + [name for name in FINAL_EVIDENCE if (ROOT / name).exists()]
    for name in selected:
        source = ROOT / name
        if not source.resolve().is_relative_to(ROOT) or not source.is_file():
            raise ValueError("Allowlisted source is missing or outside the project: " + name)
        data = source.read_bytes()
        source_sha = sha(data)
        if re.fullmatch(r"docs/reports/stage-[123]-report\.md", name) and not data.startswith(
            b"> Historical stage chapter."
        ):
            text = data.decode()

            def bind_link(match):
                target = match.group(1)
                if "experiments/" not in target:
                    return match.group(0)
                resolved = str((source.parent / target.split("#")[0]).resolve().relative_to(ROOT))
                entry = index[resolved]
                bundled = entry.get("bundled_copy")
                replacement = (
                    "evidence/historical/" + Path(bundled).name
                    if bundled
                    else "evidence/historical-index.json"
                )
                return "](" + replacement + ")"

            text = re.sub(r"\]\(([^)]+)\)", bind_link, text)
            text = (
                "> Historical stage chapter. Measurements are unchanged. This distribution copy\n"
                "> rebinds lab links to compact metrics or the source-hash index; bulk trial logs\n"
                "> remain owner-held. Original chapter SHA256: `" + source_sha + "`.\n\n" + text
            )
            data = text.encode()
        if any(secret in data for secret in secrets):
            raise ValueError("Configured credential found in allowlisted content: " + name)
        if any(
            part in (".git", ".venv", "__pycache__", ".sdd-runtime") for part in Path(name).parts
        ):
            raise ValueError("Excluded private/generated directory in allowlist")
        if Path(name).name == ".env" or name.startswith("experiments/"):
            raise ValueError("Excluded private/research file in allowlist")
        payload[name] = data
        inventory[name] = dict(sha256=sha(data), bytes=len(data), source_sha256=source_sha)
    # Current guide/report links must resolve inside this portable distribution.
    # Frozen whiteboard historical references are explicitly owner-held provenance.
    for name in ["README.md"] + [
        n for n in payload if n.startswith("docs/reports/") and n.endswith(".md")
    ]:
        for target in re.findall(r"\]\(([^)]+)\)", payload[name].decode()):
            if target.startswith(("http:", "https:", "#")):
                continue
            relative = target.split("#")[0]
            normalized = Path(os.path.normpath(str(Path(name).parent / relative))).as_posix()
            if normalized not in payload and not any(
                p.startswith(normalized.rstrip("/") + "/") for p in payload
            ):
                raise ValueError("Unresolved delivery link: " + name + " -> " + target)
    manifest = dict(
        schema=1,
        content_boundary="Workspace bytes, bound below; no implied publication or Git release.",
        historical_exports="Only stage chapter links/annotations change; original source hashes are retained. Frozen whiteboard bytes are unchanged.",
        exclusions=["credentials", "Git data", "venvs/caches", "raw conversation", "bulk research"],
        files=inventory,
    )
    payload["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    payload["SHA256SUMS"] = "".join(
        sha(data) + "  " + name + "\n" for name, data in sorted(payload.items())
    ).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo("blade-runner-review/" + name, date_time=(2000, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
            archive.writestr(entry, data)
    checksum = sha(output.read_bytes())
    output.with_suffix(output.suffix + ".sha256").write_text(checksum + "  " + output.name + "\n")
    print(
        json.dumps(
            dict(
                archive=str(output),
                files=len(inventory),
                bytes=output.stat().st_size,
                sha256=checksum,
            )
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/blade-runner-review.zip")
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()
