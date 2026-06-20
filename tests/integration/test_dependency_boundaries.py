from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_PATTERNS = {
    "services/api": ["apps.web", "apps/web", "services.browser_runtime"],
    "services/agent_runtime": ["apps.web", "apps/web", "services.api"],
    "services/learner_worker": ["apps.web", "apps/web", "services.api"],
    "services/browser_runtime": ["services/api", "live_demo_api"],
    "apps/web": ["live_demo_api", "AI_TEXT_API_KEY", "AI_TTS_API_KEY", "AI_STT_API_KEY"],
    "packages/contracts": ["apps/web", "services/api", "services/agent_runtime"],
}


def iter_source_files(root: Path) -> list[Path]:
    return sorted(
        [
            *root.rglob("*.py"),
            *root.rglob("*.ts"),
            *root.rglob("*.tsx"),
        ]
    )


def test_forbidden_dependency_directions_are_not_used() -> None:
    violations: list[str] = []

    for relative_root, forbidden_patterns in FORBIDDEN_PATTERNS.items():
        source_root = ROOT / relative_root
        for path in iter_source_files(source_root):
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden_patterns:
                if pattern in text:
                    violations.append(
                        f"{path.relative_to(ROOT)} contains forbidden pattern {pattern}"
                    )

    assert violations == []
