#!/usr/bin/env python3
"""Network Tools dashboard — Flask app. Port 5050 (macOS often uses 5000 for AirPlay)."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
from http.client import HTTPConnection, HTTPSConnection
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Flask, request, send_from_directory
import dns.resolver

app = Flask(__name__, static_folder=".")

EXTERNAL_NAMESERVERS = ["8.8.8.8", "8.8.4.4"]
_SAFE_TARGET = re.compile(r"^[a-zA-Z0-9._:\-]+$")
_MAX_LEN_HOSTNAME = 253
PORT = int(os.getenv("PORT", "5050"))


def _resolver(scope: str) -> dns.resolver.Resolver:
    if scope == "external":
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = EXTERNAL_NAMESERVERS
    else:
        r = dns.resolver.Resolver()
    r.timeout = 3
    r.lifetime = 8
    return r


def dns_ips_display(hostname: str, scope: str) -> str:
    ips: list[str] = []
    res = _resolver(scope)
    for rtype in ("A", "AAAA"):
        try:
            for ans in res.resolve(hostname, rtype):
                ips.append(str(ans))
        except Exception:
            pass
    if not ips:
        try:
            import socket as _s
            for info in _s.getaddrinfo(hostname, None)[:10]:
                ips.append(info[4][0])
        except Exception:
            pass
    seen: set[str] = set()
    uniq = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            uniq.append(ip)
    return ", ".join(uniq[:8]) if uniq else "—"


def http_and_ssl_summary(hostname: str, timeout: float = 8.0) -> dict[str, str]:
    last_err: Exception | None = None
    for scheme in ("https", "http"):
        try:
            parsed = urlparse(f"{scheme}://{hostname}/")
            host = parsed.hostname or hostname
            port = parsed.port or (443 if scheme == "https" else 80)
            Conn = HTTPSConnection if scheme == "https" else HTTPConnection
            conn = Conn(host, port, timeout=timeout)
            conn.request("GET", "/", headers={"User-Agent": "NetworkTools/1.0", "Host": host})
            resp = conn.getresponse()
            code = resp.status
            resp.read(256)
            conn.close()
            if 200 <= code < 400:
                http_status = "Connected"
            else:
                http_status = f"HTTP {code}"
            http_detail = f"{scheme.upper()} {code}"
            if scheme == "https":
                ssl_verify = _ssl_verify_column(host, port)
            else:
                ssl_verify = "N/A (HTTP only)"
            return {
                "http_status": http_status,
                "http_detail": http_detail,
                "ssl_verify": ssl_verify,
            }
        except Exception as e:
            last_err = e
            continue
    return {
        "http_status": "Failed",
        "http_detail": str(last_err) if last_err else "—",
        "ssl_verify": "—",
    }


def _ssl_verify_column(hostname: str, port: int) -> str:
    try:
        ctx = ssl.create_default_context()
        import socket as _s
        with _s.create_connection((hostname, port), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                _ = ssock.getpeercert()
                return "OK"
    except ssl.SSLCertVerificationError as e:
        return f"Verify failed: {e.verify_message}"
    except ssl.SSLError as e:
        return f"SSL: {e.reason}"
    except Exception as e:
        return str(e)[:80]


def run_checks():
    data = request.get_json(force=True, silent=True) or {}
    hostnames = data.get("hostnames") or []
    scope = (data.get("scope") or "external").lower()
    if scope not in ("internal", "external"):
        scope = "external"
    rows: list[dict[str, Any]] = []
    for h in hostnames:
        h = str(h).strip()
        if not h:
            continue
        summ = http_and_ssl_summary(h)
        rows.append(
            {
                "hostname": h,
                "dns": dns_ips_display(h, scope),
                "http_status": summ["http_status"],
                "http_detail": summ["http_detail"],
                "ssl_verify": summ["ssl_verify"],
            }
        )
    return app.response_class(
        response=json.dumps({"scope": scope, "results": rows}, indent=2),
        status=200,
        mimetype="application/json",
    )


def _strip_brackets(zone_stripped: str) -> str:
    t = zone_stripped.strip()
    if len(t) >= 2 and t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        if ":" in inner:
            return inner.split("%", 1)[0]
        return inner
    return t.split("%", 1)[0] if "%" in t else t


def _parse_possible_ip(raw: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Parse IPv4/IPv6 literals; strips optional [brackets] and zone id (%iface). Hostnames → None."""
    t = raw.strip()
    if not t:
        return None
    if t.startswith("["):
        end = t.find("]")
        if end != -1:
            inner = t[1:end]
            try:
                return ipaddress.ip_address(inner.split("%", 1)[0])
            except ValueError:
                return None
    try:
        return ipaddress.ip_address(_strip_brackets(t))
    except ValueError:
        return None


def _safe_target(t: str) -> bool:
    t = t.strip()
    if not t:
        return False
    if _parse_possible_ip(t) is not None:
        return len(t) <= 512
    if len(t) > _MAX_LEN_HOSTNAME:
        return False
    return bool(_SAFE_TARGET.match(t))


def _run(argv: list[str], timeout: float = 25.0) -> str:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode != 0 and not out.strip():
            out = f"(exit {p.returncode})"
        return out.strip() or "(no output)"
    except FileNotFoundError:
        return f"Command not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return str(e)


def _ping_argv(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> list[str]:
    """macOS `ping` is IPv4-only; IPv6 literals need ``ping6`` when available."""
    if isinstance(addr, ipaddress.IPv6Address):
        tip = addr.compressed
        if shutil.which("ping6"):
            return ["ping6", "-c", "4", tip]
        # Linux/other: ``ping`` from iputils often supports ``-6``
        return ["ping", "-6", "-c", "4", "-W", "2", tip]
    s = str(addr)
    return ["ping", "-c", "4", s] if sys.platform == "darwin" else ["ping", "-c", "4", "-W", "2", s]


def _nmap_argv(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> list[str]:
    """nmap scans IPv6 only with -6."""
    base = ["nmap", "-Pn", "-F", "--host-timeout", "20s"]
    if isinstance(addr, ipaddress.IPv6Address):
        return base + ["-6", addr.compressed]
    return base + [str(addr)]


def network_command_output(target: str, command: str, scope: str) -> str:
    target = target.strip()
    parsed_ip = _parse_possible_ip(target)
    if not _safe_target(target):
        return "Invalid hostname or IP."
    command = (command or "all").lower()
    chunks: list[str] = []

    relaxed = command == "all"
    t_shell = 12.0 if relaxed else 25.0
    t_ping = 16.0 if relaxed else 20.0
    t_nmap = 38 if relaxed else 60

    if command in ("all", "host"):
        chunks.append("— host —\n" + _run(["host", target.split("%", 1)[0]], timeout=t_shell))

    if command in ("all", "dig"):
        prefix = ["dig", "@8.8.8.8"] if scope == "external" else ["dig"]
        if parsed_ip is not None:
            argv = [*prefix, "-x", str(parsed_ip), "+noall", "+answer"]
            headline = "— dig PTR @8.8.8.8 —" if scope == "external" else "— dig PTR (reverse) —"
        else:
            argv = [*prefix, target.split("%", 1)[0], "+noall", "+answer"]
            headline = "— dig @8.8.8.8 —" if scope == "external" else "— dig —"
        chunks.append(headline + "\n" + _run(argv, timeout=t_shell))

    if command in ("all", "nslookup"):
        chunks.append(
            "— nslookup —\n" + _run(["nslookup", target.split("%", 1)[0]], timeout=t_shell),
        )

    if command in ("all", "ping"):
        if parsed_ip is not None:
            ping_head = (
                "— ping6 (IPv6) —"
                if isinstance(parsed_ip, ipaddress.IPv6Address)
                else "— ping —"
            )
            argv_p = _ping_argv(parsed_ip)
        else:
            ping_head = "— ping —"
            tgt = target.split("%", 1)[0]
            argv_p = (
                ["ping", "-c", "4", tgt]
                if sys.platform == "darwin"
                else ["ping", "-c", "4", "-W", "2", tgt]
            )
        chunks.append(ping_head + "\n" + _run(argv_p, timeout=t_ping))

    if command in ("all", "nmap"):
        if parsed_ip is not None:
            nmap_argv = _nmap_argv(parsed_ip)
            lbl = "— nmap (-6 IPv6) —\n" if isinstance(parsed_ip, ipaddress.IPv6Address) else "— nmap —\n"
            chunks.append(lbl + _run(nmap_argv, timeout=t_nmap))
        else:
            chunks.append("— nmap —\n" + _run(["nmap", "-Pn", "-F", "--host-timeout", "20s", target.split("%", 1)[0]], timeout=t_nmap))

    return "\n\n".join(chunks) if chunks else "Unknown command."


def network_command():
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    command = (data.get("command") or "all").lower()
    scope = (data.get("scope") or "external").lower()
    if scope not in ("internal", "external"):
        scope = "external"
    if command not in ("all", "dig", "nslookup", "host", "nmap", "ping"):
        command = "all"
    if not target:
        return json.dumps({"target": "", "command": command, "output": "Enter a hostname or IP."}, indent=2)
    out = network_command_output(target, command, scope)
    return json.dumps({"target": target, "command": command, "output": out}, indent=2)


def ip_lookup() -> tuple[str, int, dict[str, str]]:
    data = request.get_json(force=True, silent=True) or {}
    raw = (data.get("ip") or "").strip()
    if not raw:
        return json.dumps({"error": "Enter an IP address."}), 400, {"Content-Type": "application/json"}
    addr = _parse_possible_ip(raw)
    if addr is None:
        return json.dumps({"error": "Invalid IP address."}), 400, {"Content-Type": "application/json"}
    slug = addr.compressed
    try:
        req = Request(f"https://ipinfo.io/{slug}/json", headers={"User-Agent": "NetworkTools/1.0"})
        with urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            parsed = json.loads(body)
    except Exception as e:
        return json.dumps({"error": str(e), "ip": slug}, indent=2), 200, {"Content-Type": "application/json"}
    return json.dumps(parsed, indent=2), 200, {"Content-Type": "application/json"}


def _format_name(name: Any) -> str:
    if not name:
        return ""
    parts: list[str] = []
    for rdn in name:
        for k, v in rdn:
            parts.append(f"{k}={v}")
    return ", ".join(parts)


def _format_cert_text(hostname: str, port: int) -> str:
    import socket as _s
    lines = ["=" * 48, f"TLS CERTIFICATE for {hostname}:{port}", "=" * 48]
    try:
        ctx = ssl.create_default_context()
        with _s.create_connection((hostname, port), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    lines.append("(no certificate)")
                    return "\n".join(lines)
                lines.append("----- Certificate 1 (leaf) -----")
                lines.append("subject=" + _format_name(cert.get("subject")))
                lines.append("issuer=" + _format_name(cert.get("issuer")))
                if cert.get("notBefore"):
                    lines.append(f"notBefore={cert['notBefore']}")
                if cert.get("notAfter"):
                    lines.append(f"notAfter={cert['notAfter']}")
                san = cert.get("subjectAltName")
                if san:
                    lines.append("Subject Alternative Name:")
                    for typ, val in san:
                        lines.append(f"  {typ}:{val}")
                lines.append("")
                lines.append(f"{hostname} OK (TLS handshake OK)")
    except Exception as e:
        lines.append(f"Error: {e}")
    return "\n".join(lines)


def _parse_host_port(line: str) -> tuple[str, int] | None:
    line = line.strip()
    if not line:
        return None
    if ":" in line:
        host, _, port_s = line.rpartition(":")
        try:
            p = int(port_s)
            if 1 <= p <= 65535:
                return host.strip(), p
        except ValueError:
            pass
    return line, 443


def ssl_check() -> tuple[str, int, dict[str, str]]:
    data = request.get_json(force=True, silent=True) or {}
    lines_in = data.get("domains") or []
    if isinstance(lines_in, str):
        lines_in = [lines_in]
    outputs: list[dict[str, str]] = []
    for line in lines_in[:20]:
        line = str(line).strip()
        if not line:
            continue
        parsed = _parse_host_port(line)
        if not parsed:
            continue
        host, port = parsed
        if not _safe_target(host):
            outputs.append({"domain": line, "text": "Invalid hostname."})
            continue
        outputs.append({"domain": f"{host}:{port}", "text": _format_cert_text(host, port)})
    if not outputs:
        return json.dumps({"outputs": [], "note": "Enter at least one domain."}), 200, {"Content-Type": "application/json"}
    return json.dumps({"outputs": outputs}, indent=2), 200, {"Content-Type": "application/json"}


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/check", methods=["POST"])
def check_route():
    return run_checks()


@app.route("/network-command", methods=["POST"])
def network_command_route():
    return app.response_class(response=network_command(), status=200, mimetype="application/json")


@app.route("/ip-lookup", methods=["POST"])
def ip_lookup_route():
    body, status, _ = ip_lookup()
    return app.response_class(response=body, status=status, mimetype="application/json")


@app.route("/ssl-check", methods=["POST"])
def ssl_check_route():
    body, status, _ = ssl_check()
    return app.response_class(response=body, status=status, mimetype="application/json")


if __name__ == "__main__":
    print(f"Open: http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
