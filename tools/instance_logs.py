#!/usr/bin/env python3
"""
Watcher-first log helper for chutes.

Preferred path:
  chutes warmup <chute> --stream-logs

Compatibility path:
  Legacy API-key polling is used when the installed chutes CLI does not
  support --stream-logs or when watcher execution fails.
"""
import os
import re
import subprocess
import time
from configparser import ConfigParser

import httpx


def chutes_supports_stream_logs() -> bool:
    """Return True if the installed chutes CLI exposes --stream-logs on warmup."""
    try:
        result = subprocess.run(
            ["chutes", "warmup", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        help_text = f"{result.stdout}\n{result.stderr}"
        return "--stream-logs" in help_text
    except (subprocess.SubprocessError, OSError):
        return False


def run_watcher_logs(chute_ref: str) -> int:
    """Run SDK watcher mode and return process exit code."""
    cmd = ["chutes", "warmup", chute_ref, "--stream-logs"]
    print(f"Using SDK watcher mode: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print("chutes CLI not found in PATH.")
        return 127
    except OSError as exc:
        print(f"Unable to start watcher mode: {exc}")
        return 1


def get_api_key() -> str:
    """Get API key from environment, file, or prompt."""
    api_key = os.getenv("CHUTES_API_KEY")
    if api_key:
        return api_key

    key_file = os.path.expanduser("~/.chutes/api_key")
    if os.path.exists(key_file):
        with open(key_file, encoding="utf-8") as file_obj:
            return file_obj.read().strip()

    print("API key required for legacy log polling fallback.")
    print("Get one from: chutes keys list / chutes keys create <name>")
    api_key = input("Enter API key (cpk_...): ").strip()
    if api_key:
        save = input("Save to ~/.chutes/api_key? [y/N]: ").strip().lower()
        if save == "y":
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "w", encoding="utf-8") as file_obj:
                file_obj.write(api_key)
            print(f"Saved to {key_file}")
        return api_key
    raise RuntimeError("No API key provided")


def get_base_url() -> str:
    """Get API base URL from chutes config."""
    config = ConfigParser()
    config.read(os.path.expanduser("~/.chutes/config.ini"))
    return config.get("api", "base_url", fallback="https://api.chutes.ai")


def warmup_chute(module_path: str, timeout_seconds: int = 10) -> bool:
    """Legacy warmup helper used only in fallback mode."""
    try:
        proc = subprocess.Popen(
            ["chutes", "warmup", module_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as exc:
        print(f"Warmup error: {exc}")
        return False

    try:
        proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        proc.terminate()
        print("Warmup started; instance may still be spinning up.")
        return True

    output = ""
    if proc.stdout:
        output = proc.stdout.read()
    lowered = output.lower()
    if "not found" in lowered or "does not belong" in lowered:
        print("Chute not deployed - deploy first.")
        return False
    if "error" in lowered and "status: warm" not in lowered:
        print("Warmup issue detected in CLI output.")
        return False
    return True


def get_chute_instances(base_url: str, api_key: str, chute_id: str) -> list[dict]:
    """Get list of instances for a chute."""
    headers = {"Authorization": api_key}
    resp = httpx.get(f"{base_url}/chutes/{chute_id}", headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Failed to get chute: {resp.status_code} {resp.text[:200]}")
        return []
    data = resp.json()
    return data.get("instances", [])


def get_chute_id_by_name(chute_name: str) -> str | None:
    """Get chute ID by name using CLI output."""
    try:
        result = subprocess.run(
            ["chutes", "chutes", "get", chute_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        json_match = re.search(r"\{[\s\S]*\}", result.stdout)
        if json_match:
            import json

            data = json.loads(json_match.group())
            return data.get("chute_id")
    except Exception as exc:
        print(f"CLI lookup error: {exc}")
    return None


def fetch_instance_logs(
    base_url: str,
    api_key: str,
    instance_id: str,
    backfill: int = 100,
    timeout: int = 10,
) -> tuple[int, str]:
    """Fetch logs from an instance. Returns (status_code, content)."""
    headers = {"Authorization": api_key}
    try:
        resp = httpx.get(
            f"{base_url}/instances/{instance_id}/logs",
            headers=headers,
            params={"backfill": backfill},
            timeout=timeout,
        )
        return resp.status_code, resp.text
    except Exception as exc:
        return -1, str(exc)


def stream_instance_logs(
    base_url: str,
    api_key: str,
    instance_id: str,
    backfill: int = 100,
) -> None:
    """Stream logs from an instance to stdout."""
    headers = {"Authorization": api_key}
    try:
        with httpx.stream(
            "GET",
            f"{base_url}/instances/{instance_id}/logs",
            headers=headers,
            params={"backfill": backfill},
            timeout=None,
        ) as resp:
            if resp.status_code != 200:
                print(f"Error: {resp.status_code}")
                return
            for chunk in resp.iter_text():
                print(chunk, end="", flush=True)
    except KeyboardInterrupt:
        print("\n[Interrupted]")
    except Exception as exc:
        print(f"Stream error: {exc}")


def find_instance_with_logs(
    base_url: str,
    api_key: str,
    instances: list[dict],
    max_tries: int = 10,
) -> tuple[str | None, str]:
    """
    Try instances until one returns logs.
    Returns (instance_id, logs) or (None, error_msg).
    """

    def sort_key(inst: dict) -> tuple[bool, bool, str]:
        return (
            not inst.get("active", False),
            not inst.get("verified", False),
            inst.get("last_verified_at") or "",
        )

    sorted_instances = sorted(instances, key=sort_key)

    tried = 0
    for inst in sorted_instances:
        if tried >= max_tries:
            break
        inst_id = inst["instance_id"]
        verified = inst.get("verified", False)
        active = inst.get("active", False)

        print(f"  Trying {inst_id[:8]}... (active={active}, verified={verified})", end=" ")
        status, content = fetch_instance_logs(base_url, api_key, inst_id, backfill=200)
        tried += 1

        if status == 200 and content.strip():
            print(f"OK ({len(content)} bytes)")
            return inst_id, content
        if status == 200:
            print("empty")
        elif status == 404:
            print("gone")
        elif status == 403:
            print("forbidden")
        else:
            print(f"status={status}")

    return None, f"No instance returned logs after {tried} tries"


def check_logs(chute_name: str, warmup_module: str | None = None, stream: bool = False):
    """
    Check logs for a chute.

    Watcher-first behavior:
      - always attempts `chutes warmup <target> --stream-logs`
      - falls back to legacy polling when watcher mode is unavailable or fails

    Compatibility flags:
      - --warmup: only used in legacy fallback mode
      - --stream: only affects legacy fallback mode
    """
    watcher_target = chute_name

    if chutes_supports_stream_logs():
        status = run_watcher_logs(watcher_target)
        if status == 0:
            return
        if status == 130:
            return
        print(f"Watcher mode exited with status {status}; falling back to legacy polling.")
    else:
        print("Installed chutes CLI does not support --stream-logs; using legacy polling.")

    try:
        api_key = get_api_key()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    base_url = get_base_url()

    if warmup_module:
        print(f"Compatibility mode: legacy warmup using {warmup_module}...")
        if not warmup_chute(warmup_module, timeout_seconds=10):
            return

    print(f"Looking up chute '{chute_name}'...")
    chute_id = get_chute_id_by_name(chute_name)
    if not chute_id:
        if chute_name.count("-") == 4:
            chute_id = chute_name
        else:
            print(f"Chute not found: {chute_name}")
            return

    print(f"Chute ID: {chute_id}")

    max_retries = 4
    retry_delay = 8

    for attempt in range(max_retries):
        print(f"Getting instances... (attempt {attempt + 1}/{max_retries})")
        instances = get_chute_instances(base_url, api_key, chute_id)

        if not instances:
            if attempt < max_retries - 1:
                print(f"No instances yet, waiting {retry_delay}s...")
                time.sleep(retry_delay)
                continue
            print("No instances found (chute may be cold)")
            return

        print(f"Found {len(instances)} instance(s)")

        if stream:
            for inst in instances:
                if inst.get("verified"):
                    print(f"Streaming logs from {inst['instance_id']}...")
                    stream_instance_logs(base_url, api_key, inst["instance_id"])
                    return
            print("No verified instances to stream from")
            return

        inst_id, logs = find_instance_with_logs(base_url, api_key, instances)
        if inst_id:
            print(f"\n{'=' * 60}")
            print(f"Logs from instance {inst_id}:")
            print("=" * 60)
            print(logs)
            return
        if attempt < max_retries - 1:
            print(f"No logs yet, waiting {retry_delay}s...")
            time.sleep(retry_delay)
        else:
            print(f"\n{logs}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Watcher-first chute logs: uses `chutes warmup --stream-logs` when available, "
            "falls back to legacy API-key polling for older CLIs."
        )
    )
    parser.add_argument("chute_id", help="Chute ID or name")
    parser.add_argument(
        "--warmup",
        "-w",
        help="Compatibility mode only: module path used for legacy warmup fallback (e.g., deploy_xtts_whisper:chute)",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Compatibility mode only: stream continuously in legacy fallback",
    )

    args = parser.parse_args()
    check_logs(args.chute_id, warmup_module=args.warmup, stream=args.stream)
