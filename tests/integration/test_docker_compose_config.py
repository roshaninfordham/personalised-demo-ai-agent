import subprocess
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parents[2]


def test_docker_compose_config_is_valid() -> None:
    docker_path = which("docker")
    assert docker_path is not None

    result = subprocess.run(  # noqa: S603
        [docker_path, "compose", "config", "--quiet"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
