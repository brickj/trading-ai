"""SSH helper to prepare the trading AI project on a freshly provisioned EC2 host."""

from __future__ import annotations

import pathlib
import shlex
import sys
from typing import Iterable

import paramiko


# Replace this with the absolute path to the PEM key used for SSH authentication.
PEM_KEY_PATH = "/path/to/your-key.pem"

# Repository configuration.
REPOSITORY_URL = "https://github.com/example/trading-ai.git"
PROJECT_DIR = "trading-ai"
PYTHON_EXECUTABLE = "python3"

# Remote commands executed on the EC2 instance in order.
REMOTE_COMMANDS: list[list[str]] = [
    ["sudo", "dnf", "update", "-y"],
    ["sudo", "dnf", "install", "-y", "git", "python3", "python3-pip"],
    ["git", "clone", REPOSITORY_URL],
    [PYTHON_EXECUTABLE, "-m", "pip", "install", "--upgrade", "pip"],
    [PYTHON_EXECUTABLE, "-m", "pip", "install", "-r", f"{PROJECT_DIR}/requirements.txt"],
    [PYTHON_EXECUTABLE, f"{PROJECT_DIR}/start_app.py"],
]


def _format_command(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def bootstrap_instance(hostname: str, username: str = "ec2-user") -> None:
    """Connect to the remote host and run the bootstrap commands."""

    key_path = pathlib.Path(PEM_KEY_PATH).expanduser()
    if not key_path.exists():
        raise FileNotFoundError(f"PEM key not found at {key_path}. Update PEM_KEY_PATH.")

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(
            hostname=hostname,
            username=username,
            key_filename=str(key_path),
            look_for_keys=False,
            allow_agent=False,
            timeout=30,
        )
    except Exception as exc:  # pylint: disable=broad-except
        raise RuntimeError(f"Failed to connect to {hostname}: {exc}") from exc

    try:
        for command in REMOTE_COMMANDS:
            formatted = _format_command(command)
            print(f"Executing: {formatted}")
            _stdin, stdout, stderr = ssh_client.exec_command(formatted)
            exit_status = stdout.channel.recv_exit_status()
            stdout_output = stdout.read().decode("utf-8", errors="ignore")
            stderr_output = stderr.read().decode("utf-8", errors="ignore")

            if stdout_output:
                print(stdout_output)
            if stderr_output:
                print(stderr_output, file=sys.stderr)
            if exit_status != 0:
                raise RuntimeError(f"Command '{formatted}' failed with exit status {exit_status}")
    finally:
        ssh_client.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_remote_instance.py <public_dns_or_ip> [username]", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    user = sys.argv[2] if len(sys.argv) > 2 else "ec2-user"

    try:
        bootstrap_instance(host, user)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Bootstrap failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
