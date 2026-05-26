#!/usr/bin/env python3
"""Optional stdio helper for editors and automation: exposes the Flask routes behind the Network Tools UI.

Runs against ``server.py`` through Flask's test client, so HTTP does not need to be listening unless you explicitly
spawn it. Depends on packages from ``requirements-mcp.txt`` (notably ``mcp`` alongside Flask).

See ``editor-config/mcp-servers.example.json`` for the mergeable JSON fragment your editor expects next to this checkout.
"""

from __future__ import annotations

import ipaddress
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Literal
from urllib.error import URLError
from urllib.parse import unquote_plus
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

import server as _server_bundle
from server import app as flask_app

mcp = FastMCP(
    "network-tools-dashboard",
    instructions=(
        "Prefer network_lookup_smart when the user's intent is ambiguous—it classifies IPs, host:port strings, "
        "and domains. Dedicated helpers mirror each browser panel in this project. Offer start_network_dashboard only "
        "when localhost HTTP truly must respond (browser previews or fetch failures). Other routes keep Flask "
        "in-memory. External scope favors Google DNS; internal follows the workstation resolver."
    ),
)

def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _dashboard_listen_url(port: int) -> str:
    return f"http://127.0.0.1:{int(port)}/"


def _dashboard_accepting_connections(port: int, timeout_sec: float = 2.0) -> bool:
    try:
        req = Request(_dashboard_listen_url(port), headers={"User-Agent": "NetworkTools-stdio-helper/1.0"})
        with urlopen(req, timeout=timeout_sec) as r:
            code = int(r.getcode())
            return 200 <= code < 500
    except (OSError, URLError, ValueError):
        return False


def _wait_dashboard_ready(port: int, retries: int = 20, delay_sec: float = 0.35) -> bool:
    for _ in range(retries):
        if _dashboard_accepting_connections(port, timeout_sec=2.5):
            return True
        time.sleep(delay_sec)
    return False


def _split_hosts(raw: str) -> list[str]:
    text = raw.replace(",", "\n")
    rows: list[str] = []
    for line in text.splitlines():
        t = line.strip()
        if t:
            rows.append(unquote_plus(t.strip()))
    return rows


def _looks_like_ip_token(token: str) -> bool:
    t = token.strip()
    if not t:
        return False
    try:
        ipaddress.ip_address(t)
        return True
    except ValueError:
        if t.startswith("[") and t.endswith("]"):
            try:
                ipaddress.ip_address(t[1:-1])
                return True
            except ValueError:
                return False
    return False


def _segment_kind(seg: str) -> Literal["ip", "tls", "domain"]:
    """Pick ipinfo vs TLS vs domain HTTP buckets for a token."""
    s = seg.strip()

    if s.startswith("["):
        end = s.find("]")
        if end > 1:
            inner = s[1:end]
            tail = s[end + 1 :]
            ip_ok = False
            try:
                ipaddress.ip_address(inner.split("%", 1)[0])
                ip_ok = True
            except ValueError:
                ip_ok = False
            if ip_ok:
                if not tail:
                    return "ip"
                if tail.startswith(":"):
                    port_str = tail[1:]
                    if port_str.isdigit() and 1 <= int(port_str) <= 65535:
                        return "tls"
                return "domain"
        return "domain"

    if _looks_like_ip_token(s.split("%", 1)[0]):
        return "ip"
    if ":" not in s:
        return "domain"

    lhs, sep, rhs = s.rpartition(":")
    return "tls" if sep and rhs.isdigit() and 1 <= int(rhs) <= 65535 and lhs.strip() else "domain"


@mcp.tool()
def network_lookup_smart(
    targets: str,
    scope: str = "external",
    extras_command: str = "none",
) -> str:
    """Fast path when callers mix targets without declaring each flavor.

    Splits commas/newlines then routes each token:

    • IPv4/IPv6 literals → ``ip_geo_lookup`` ipinfo payloads (same pathway as IP Check pane).
    • Values with trailing ``:port`` (not ambiguous bare IPv6) → ``ssl_certificate_inspect``.
    • Hostnames/domains → ``domain_check`` (DNS rows + HTTP/HTTPS reachability).

    Args:
        targets: Mixed list (IPs, domains, optional host:8443 tails).
        scope: "external" favors Google DNS; "internal" follows the workstation resolver.
        extras_command: "none" by default—or "all"|"dig"|"host"|"nslookup"|"ping"|"nmap" to append bounded shell snippets
          for unique tokens (currently capped near twelve hosts).

    Notes:
        IPv6 with zone identifiers is accepted when stripping ``%`` keeps a valid literal.
        Narrow shell-only digs can still funnel through ``network_commands`` individually.
    """
    s = scope.lower().strip()
    if s not in ("internal", "external"):
        s = "external"
    xc = extras_command.strip().lower() if extras_command else "none"
    if xc not in ("none", "all", "dig", "host", "nslookup", "ping", "nmap"):
        xc = "none"

    segs = _split_hosts(targets)
    if not segs:
        return "No targets: pass hostnames, IPs, or host:port lines."

    ips: list[str] = []
    tls_lines: list[str] = []
    domains: list[str] = []

    seen_tokens: set[str] = set()
    for raw in segs:
        raw = raw.strip()
        if not raw or raw in seen_tokens:
            continue
        seen_tokens.add(raw)
        match _segment_kind(raw):
            case "ip":
                ips.append(raw)
            case "tls":
                tls_lines.append(raw)
            case "domain":
                domains.append(raw)

    parts: list[str] = []

    if domains:
        with flask_app.test_client() as c:
            body = c.post("/check", json={"hostnames": domains, "scope": s}).get_data(as_text=True)
        parts.append(f"### Domain DNS + HTTP/TLS ({s})\n\n```json\n{body}\n```")

    if ips:
        ip_blocks = []
        with flask_app.test_client() as c:
            for ip in ips:
                body = c.post("/ip-lookup", json={"ip": ip.strip()}).get_data(as_text=True)
                ip_blocks.append(f"#### {ip.strip()}\n```json\n{body}\n```")
        parts.append("### IP geolocation (ipinfo)\n\n" + "\n\n".join(ip_blocks))

    if tls_lines:
        with flask_app.test_client() as c:
            body = c.post("/ssl-check", json={"domains": tls_lines}).get_data(as_text=True)
        parts.append("### TLS certificates\n\n```json\n" + body + "\n```")

    if xc != "none":
        shell_targets = list(dict.fromkeys(domains + ips + tls_lines))
        shell_targets = shell_targets[:12]
        cmd_blocks = []
        with flask_app.test_client() as c:
            for t in shell_targets:
                tb = (
                    c.post(
                        "/network-command",
                        json={"target": t, "command": xc, "scope": s},
                    )
                    .get_data(as_text=True)
                )
                try:
                    out = json.loads(tb).get("output", tb)
                except json.JSONDecodeError:
                    out = tb
                cmd_blocks.append(f"#### `{t}` (`{xc}`)\n```\n{out}\n```")
        parts.append(f"### Network shell extras (`{xc}`)\n\n" + "\n\n".join(cmd_blocks))

    classify_summary = []
    classify_summary.extend([f"- **{h}** → domain check bucket" for h in domains])
    classify_summary.extend([f"- **{p}** → ipinfo bucket" for p in ips])
    classify_summary.extend([f"- **{t}** → TLS inspect bucket" for t in tls_lines])
    preview = "**Classified**\n\n" + "\n".join(classify_summary)

    body = ("\n\n---\n\n".join(parts) if parts else "_No lookups ran — check classification._")
    return f"{preview}\n\n---\n\n## Results\n\n{body}"


@mcp.tool()
def domain_check(hostnames: str, scope: str = "external") -> str:
    """DNS plus HTTP/TLS summaries matching the site's Domain Check area.

    Args:
        hostnames: Hostnames separated by newlines or commas (e.g. "example.com, www.example.org").
        scope: "external" favors 8.8.8.8/8.8.4.4; "internal" follows the workstation resolver.
    """
    s = scope.lower().strip()
    if s not in ("internal", "external"):
        s = "external"
    lines = _split_hosts(hostnames)
    if not lines:
        return '{"error":"Provide at least one hostname."}'
    with flask_app.test_client() as c:
        r = c.post("/check", json={"hostnames": lines, "scope": s})
        return r.get_data(as_text=True)


@mcp.tool()
def network_commands(target: str, command: str = "all", scope: str = "external") -> str:
    """Run bounded shell tools: host, dig, nslookup, ping, or nmap (if installed).

    Args:
        target: Hostname or IP (alphanumeric plus . _ : -).
        command: One of all, dig, host, nslookup, ping, nmap.
        scope: external dig uses @8.8.8.8; internal uses default resolver settings.
    """
    s = scope.lower().strip()
    if s not in ("internal", "external"):
        s = "external"
    with flask_app.test_client() as c:
        r = c.post("/network-command", json={"target": target.strip(), "command": command, "scope": s})
        return r.get_data(as_text=True)


@mcp.tool()
def ip_geo_lookup(ip: str) -> str:
    """Return ipinfo.io JSON for an IPv4/IPv6 (org, city, ASN when available).

    Requires outbound HTTPS to ipinfo.io (same as dashboard).
    """
    with flask_app.test_client() as c:
        r = c.post("/ip-lookup", json={"ip": ip.strip()})
        return r.get_data(as_text=True)


@mcp.tool()
def ssl_certificate_inspect(domains: str) -> str:
    """Fetch and summarize TLS certificates (subject, SANs, expiry) per host[:port].

    Args:
        domains: Lines or commas; each entry optional :port (default 443), e.g. "example.com, api.example.org:8443".
    """
    items = _split_hosts(domains)
    if not items:
        return '{"outputs":[],"note":"Enter at least one domain."}'
    with flask_app.test_client() as c:
        r = c.post("/ssl-check", json={"domains": items})
        return r.get_data(as_text=True)


@mcp.tool()
def start_network_dashboard(
    port: int | None = None,
    open_browser: bool = False,
) -> str:
    """Start the Network Tools Flask listener in the background (real HTTP server for browser panels).

    Most routed helpers reuse Flask privately and do **not** need this. Use when previews want
    ``http://127.0.0.1:{port}/`` (default commonly **5050**) or browsers log **Failed to fetch** because nothing listens.

    If the port already answers HTTP, skips starting and returns ``already_running: true``.
    Respect env **PORT** (from ``server.py`` defaults) unless ``port`` is passed here.

    Args:
        port: Listen port (default: same as ``server.PORT``, usually **5050**).
        open_browser: If true, best-effort open the dashboard URL via the OS (``webbrowser``).
    """
    root = _project_root()
    listen = int(port) if port is not None else int(_server_bundle.PORT)
    if not (1 <= listen <= 65535):
        return json.dumps({"ok": False, "error": "port must be 1–65535"}, indent=2)

    url = _dashboard_listen_url(listen)
    if _dashboard_accepting_connections(listen):
        if open_browser:
            webbrowser.open(url)
        return json.dumps(
            {
                "ok": True,
                "already_running": True,
                "url": url,
                "message": "Dashboard already responding on this port.",
                "open_browser_attempted": open_browser,
            },
            indent=2,
        )

    script = root / "server.py"
    if not script.is_file():
        return json.dumps({"ok": False, "error": f"server.py not found at {script}"}, indent=2)

    env = dict(os.environ)
    env["PORT"] = str(listen)

    popen_kw: dict = {
        "args": [sys.executable, str(script)],
        "cwd": str(root),
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creation = subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creation |= subprocess.CREATE_NO_WINDOW  # type: ignore[operator]
        popen_kw["creationflags"] = creation  # type: ignore[assignment]
    else:
        popen_kw["start_new_session"] = True
        popen_kw["close_fds"] = True

    try:
        subprocess.Popen(**popen_kw)  # noqa: SIM115 — long-lived Flask child process
    except OSError as e:
        return json.dumps({"ok": False, "error": str(e), "url": url}, indent=2)

    ok = _wait_dashboard_ready(listen)
    payload: dict[str, object] = {
        "ok": ok,
        "already_running": False,
        "url": url,
        "message": (
            "Dashboard process started and answered HTTP." if ok else "Process spawned but HTTP not ready yet; check port clashes or rerun."
        ),
        "port": listen,
        "working_directory": str(root),
        "executable": sys.executable,
        "open_browser_attempted": open_browser,
    }
    if ok and open_browser:
        webbrowser.open(url)
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    mcp.run()
