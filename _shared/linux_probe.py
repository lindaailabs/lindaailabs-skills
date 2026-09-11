"""Read-only Linux process probes. No raw command lines leave this module."""
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import sys
import time
from urllib import error, parse, request

import psutil


def clean(value):
    return "".join(c for c in str(value) if c.isprintable())[:180]


def java_identity(argv):
    jar = None
    main = None
    options = []
    skip = False
    for index, arg in enumerate(argv[1:], 1):
        if skip:
            skip = False
            continue
        if arg == "-jar":
            jar = clean(Path(argv[index + 1]).name) if index + 1 < len(argv) else None
            break
        if arg in ("-cp", "-classpath", "--class-path", "-p", "--module-path"):
            skip = True
            continue
        if arg in ("-m", "--module"):
            main = clean(argv[index + 1]) if index + 1 < len(argv) else None
            break
        if re.fullmatch(r"-Xm[sx]\d+[kKmMgG]?", arg) or re.fullmatch(
            r"-XX:(?:MaxRAMPercentage|InitialRAMPercentage)=\d+(?:\.\d+)?", arg
        ):
            options.append(arg)
        if not arg.startswith("-"):
            main = clean(arg)
            break
    return {"service": jar or main or "java (identity unavailable)",
            "jar": jar, "main_class": main, "jvm_options": options}


def describe(proc, ports=False):
    with proc.oneshot():
        name = proc.name()
        is_java = name in ("java", "javaw")
        item = {"pid": proc.pid, "name": clean(name), "java": is_java,
                "service": clean(name), "started_at": proc.create_time(),
                "uptime_seconds": max(0, int(time.time() - proc.create_time())),
                "status": proc.status(), "rss_bytes": proc.memory_info().rss}
        if is_java:
            try:
                item.update(java_identity(proc.cmdline()))
            except psutil.AccessDenied:
                item["identity_warning"] = "command line access denied"
        if ports:
            try:
                listeners = proc.net_connections(kind="tcp")
                item["listeners"] = sorted({
                    (conn.laddr.ip, conn.laddr.port) for conn in listeners
                    if conn.status == psutil.CONN_LISTEN
                })
            except psutil.AccessDenied:
                item["listeners"] = None
    return item


def inventory():
    services = []
    denied = 0
    for proc in psutil.process_iter():
        try:
            if proc.name() in ("java", "javaw"):
                services.append(describe(proc, ports=True))
        except psutil.AccessDenied:
            denied += 1
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    services.sort(key=lambda row: row["rss_bytes"], reverse=True)
    return {"services": services, "inaccessible_processes": denied}


def select_target(services, target):
    target = str(target).strip()
    if target.isdecimal():
        return [row for row in services if row["pid"] == int(target)]
    exact = [row for row in services if row["service"].casefold() == target.casefold()]
    return exact or [row for row in services if target.casefold() in row["service"].casefold()]


def cpu_sample(target=""):
    processes = []
    denied = 0
    for proc in psutil.process_iter():
        try:
            info = describe(proc)
            proc.cpu_percent(None)
            processes.append((proc, info))
        except psutil.AccessDenied:
            denied += 1
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    # All process counters share this interval; 100% means one logical CPU.
    before = time.monotonic()
    system = psutil.cpu_times_percent(interval=1.0)
    rows = []
    for proc, info in processes:
        try:
            if proc.is_running() and proc.create_time() == info["started_at"]:
                info["cpu_percent"] = proc.cpu_percent(None)
                rows.append(info)
        except psutil.AccessDenied:
            denied += 1
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    rows.sort(key=lambda row: row["cpu_percent"], reverse=True)
    selected = select_target(rows, target) if target else []
    return {"cpu_count": psutil.cpu_count() or 1,
            "sample_seconds": round(time.monotonic() - before, 2),
            "busy_percent": round(max(0, 100 - system.idle - system.iowait), 1),
            "iowait_percent": system.iowait, "steal_percent": system.steal,
            "load_average": list(os.getloadavg()), "processes": rows[:10],
            "target": clean(target), "selected": selected[:20],
            "inaccessible_processes": denied}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_health_url(url, listeners):
    parsed = parse.urlsplit(url)
    if (parsed.scheme not in ("http", "https") or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not parsed.hostname):
        raise ValueError("health_url must be HTTP(S), without credentials, query or fragment")
    if any(ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError("health_url contains control characters")
    host = parsed.hostname
    if host == "localhost":
        host = "127.0.0.1"
    address = ipaddress.ip_address(host)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    matches = [(ip, p) for ip, p in (listeners or [])
               if p == port and (ip == host or (address.is_loopback and
                   ip in (("0.0.0.0",) if address.version == 4 else ("::",))))]
    if not matches:
        raise ValueError("health_url must match a visible listening address/port of this PID")
    host_text = f"[{host}]" if address.version == 6 else host
    return parse.urlunsplit((parsed.scheme, f"{host_text}:{port}", parsed.path or "/", "", ""))


def http_health(url):
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request.Request(url, method="GET"), timeout=3) as response:
            data = response.read(16385)
            app_status = None
            if len(data) <= 16384:
                try:
                    body = json.loads(data)
                    if isinstance(body, dict) and isinstance(body.get("status"), str):
                        app_status = body["status"].upper()
                except (ValueError, UnicodeError):
                    pass
            return {"status_code": response.status,
                    "application_status": app_status if app_status in
                    ("UP", "DOWN", "OUT_OF_SERVICE", "UNKNOWN") else None}
    except error.HTTPError as exc:
        return {"status_code": exc.code, "application_status": None}
    except (error.URLError, OSError, ValueError):
        return {"status_code": None, "error": "HTTP connection/TLS/timeout failure"}


def service_health(target, url=""):
    data = inventory()
    candidates = select_target(data["services"], target)
    if len(candidates) != 1:
        return {"state": "ambiguous" if candidates else "not_found",
                "candidates": candidates[:20],
                "inaccessible_processes": data["inaccessible_processes"]}
    service = candidates[0]
    proc = psutil.Process(service["pid"])
    if not proc.is_running() or proc.create_time() != service["started_at"]:
        return {"state": "changed", "service": service}
    if service["status"] in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
        return {"state": "exited", "service": service}
    listeners = service["listeners"]
    verified_url = validate_health_url(url, listeners) if url else None
    checks = []
    for ip, port in (listeners or [])[:8]:
        address = "127.0.0.1" if ip == "0.0.0.0" else "::1" if ip == "::" else ip
        try:
            with socket.create_connection((address, port), timeout=1):
                connected = True
        except OSError:
            connected = False
        checks.append({"address": address, "port": port, "connected": connected})
    result = {"state": "observed", "service": service, "tcp_checks": checks,
              "omitted_ports": max(0, len(listeners or []) - 8)}
    if verified_url:
        result["http"] = http_health(verified_url)
        result["http"]["url"] = verified_url
    return result


def run(operation, args):
    if sys.platform != "linux":
        raise ValueError("Linux is required")
    if args.get("host", "localhost") not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("only localhost is supported; SSH is not configured")
    target = args.get("target", "")
    url = args.get("health_url", "")
    if not isinstance(target, str) or not isinstance(url, str):
        raise ValueError("target and health_url must be strings")
    if operation == "list_java_services":
        data = inventory()
        if target:
            data["services"] = select_target(data["services"], target)
        data["total"] = len(data["services"])
        data["services"] = data["services"][:50]
    elif operation == "check_cpu_usage":
        data = cpu_sample(target)
    elif operation == "check_service_health":
        if not target.strip():
            raise ValueError("target is required: Java PID, JAR or main class")
        data = service_health(target, url)
    else:
        raise ValueError("unknown operation")
    return {"returncode": 0, "probe": operation, "host": "localhost",
            "checked_at": time.time(), "data": data}


if __name__ == "__main__":
    try:
        result = run(sys.argv[1], json.loads(sys.argv[2]))
    except (ValueError, OSError, psutil.Error) as exc:
        result = {"returncode": 1, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=True))
