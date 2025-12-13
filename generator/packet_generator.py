import time
import random
from scapy.all import IP, TCP, send, Raw, RandIP, RandShort

TARGET_IP = "192.168.1.2"      # Your receiver / victim
TARGET_PORT = 80               # Common for HTTP (DoS + Fuzzers)
INTERFACE = None               # None = default route

# =================================================================
# 1. Normal Flow (Realistic HTTP session)
# =================================================================
def make_normal_flow():
    src_port = random.randint(20000, 60000)
    payload = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"

    syn = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="S", seq=1000)
    data = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="PA", seq=1001, ack=1)/Raw(payload)
    fin = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="FA", seq=1001+len(payload))

    return [syn, data, fin], "normal"

# =================================================================
# 2. DoS Attack (extreme volume, very high rate)
# =================================================================
def make_dos_attack():
    """Extreme DoS: hundreds of packets in a very short time.

    This should create flows with:
      - very large sbytes
      - tiny duration
      - extremely high Sload and very small Sintpkt
    """
    packets = []
    src_port = 6666

    # 300–800 rapid packets: SYN flood + huge HTTP-like payloads
    for i in range(random.randint(300, 800)):
        if random.random() < 0.5:
            # Pure SYN (classic SYN flood) from many spoofed IPs
            p = IP(dst=TARGET_IP, src=RandIP())/TCP(
                sport=RandShort(),
                dport=TARGET_PORT,
                flags="S",
                seq=random.randint(1, 10_000_000),
            )
        else:
            # Oversized/fake HTTP requests
            fake_url = random.choice([
                b"/admin.php",
                b"/login",
                b"/api/v1/resource/" + b"A" * random.randint(500, 4000),
            ])
            payload = b"GET " + fake_url + b" HTTP/1.1\r\nUser-Agent: DoS-Tool\r\n\r\n"
            p = IP(dst=TARGET_IP)/TCP(
                sport=src_port,
                dport=TARGET_PORT,
                flags="PA",
                seq=i * 4096,
                ack=1,
            )/Raw(payload)

        packets.append(p)

    # No sleep here: send as fast as possible from caller
    return packets, "dos"

# =================================================================
# 3. Fuzzers Attack (very large malformed payloads, strange flags)
# =================================================================
def make_fuzzers_attack():
    """Extreme fuzzing: huge random payloads and odd TCP flag combos.

    This should push smeansz high and create unusual flag patterns
    compared to generic HTTP.
    """
    packets = []
    src_port = 31337

    for i in range(random.randint(30, 80)):
        # Very large random garbage payload + weird flags
        garbage = random.randbytes(random.randint(2000, 8000))
        weird_flags = random.choice(["F", "R", "U", "SF", "SR", "FPU", "PA", "FA"])

        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([TARGET_PORT, 22, 21, 3306, 445, 3389]),  # random service port
            flags=weird_flags,
            seq=random.randint(1, 9_999_999),
            ack=random.randint(1, 9_999_999),
        )/Raw(garbage)

        packets.append(p)
        # much tighter timing than normal traffic
        time.sleep(0.001)

    return packets, "fuzzers"

# =================================================================
# 4. Generic Attack (mixed suspicious HTTP / TCP patterns)
# =================================================================
def make_generic_attack():
    packets = []
    src_port = random.randint(20000, 60000)

    for i in range(random.randint(20, 60)):
        # mix of short and long suspicious HTTP-like payloads
        payload = random.choice([
            b"GET /admin HTTP/1.1\r\nHost: victim\r\n\r\n",
            b"POST /login HTTP/1.1\r\nContent-Length: 0\r\n\r\n",
            b"GET /?id=" + b"A" * random.randint(50, 500) + b" HTTP/1.1\r\n\r\n",
        ])
        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([TARGET_PORT, 8080]),
            flags="PA",
            seq=1000 + i * 100,
            ack=1,
        )/Raw(payload)
        packets.append(p)

    return packets, "generic"

# =================================================================
# 5. Exploits Attack (attempts with exploit-like payloads)
# =================================================================
def make_exploits_attack():
    packets = []
    src_port = random.randint(20000, 60000)
    exploit_strings = [
        b"/bin/sh",
        b"cmd.exe",
        b"../../../../etc/passwd",
        b"UNION SELECT username, password FROM users",
        b"exec xp_cmdshell 'dir'",
    ]

    for i in range(random.randint(10, 30)):
        payload = b"GET " + random.choice(exploit_strings) + b" HTTP/1.1\r\nHost: victim\r\n\r\n"
        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([80, 8080, 443]),
            flags="PA",
            seq=10000 + i * 50,
            ack=1,
        )/Raw(payload)
        packets.append(p)

    return packets, "exploits"

# =================================================================
# 6. Reconnaissance (port scanning / probing)
# =================================================================
def make_reconnaissance_attack():
    packets = []
    src_ip = RandIP()
    for dport in random.sample([21, 22, 23, 25, 53, 80, 110, 139, 443, 445, 3306, 8080], k=10):
        p = IP(dst=TARGET_IP, src=src_ip)/TCP(sport=RandShort(), dport=dport, flags="S")
        packets.append(p)
    return packets, "reconnaissance"

# =================================================================
# 7. Backdoor / Backdoors (connections to uncommon high ports)
# =================================================================
def make_backdoor_attack():
    packets = []
    dst_port = random.choice([4444, 5555, 8081, 1337])
    src_port = random.randint(20000, 60000)

    # simple reverse-shell style session
    syn = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=dst_port, flags="S", seq=1000)
    ack = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=dst_port, flags="SA", seq=1001, ack=1)
    data = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=dst_port, flags="PA", seq=1002, ack=1)/Raw(b"/bin/sh -i")

    packets.extend([syn, ack, data])
    return packets, "backdoor"


def make_backdoors_attack():
    packets, _ = make_backdoor_attack()
    return packets, "backdoors"

# =================================================================
# 8. Analysis (suspicious but low-volume probing/inspection)
# =================================================================
def make_analysis_flow():
    packets = []
    src_ip = RandIP()
    for i in range(random.randint(5, 15)):
        p = IP(dst=TARGET_IP, src=src_ip)/TCP(
            sport=RandShort(),
            dport=random.choice([80, 443, 8080]),
            flags=random.choice(["S", "SA", "PA"]),
            seq=1000 + i * 10,
        )
        packets.append(p)
    return packets, "analysis"

# =================================================================
# 9. Shellcode (binary payloads, long NOP sleds)
# =================================================================
def make_shellcode_attack():
    """Extreme shellcode-style payloads.

    Long NOP sleds + random bytes, making very large payload sizes
    that should stand out strongly from generic HTTP.
    """
    packets = []
    src_port = random.randint(20000, 60000)

    for i in range(random.randint(10, 40)):
        nop_sled = b"\x90" * random.randint(500, 3000)
        shell_bytes = random.randbytes(random.randint(500, 3000))
        payload = nop_sled + shell_bytes
        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([TARGET_PORT, 4444, 31337]),
            flags="PA",
            seq=5000 + i * 4096,
            ack=1,
        )/Raw(payload)
        packets.append(p)

    return packets, "shellcode"

# =================================================================
# 10. Worms (rapid connections to many hosts/ports)
# =================================================================
def make_worms_attack():
    packets = []
    for i in range(random.randint(20, 60)):
        dst_ip = RandIP()
        dst_port = random.choice([135, 139, 445, 1433, 4444])
        payload = b"WORM" + random.randbytes(random.randint(20, 200))
        p = IP(dst=dst_ip)/TCP(
            sport=RandShort(),
            dport=dst_port,
            flags="S",
            seq=random.randint(1, 999999),
        )/Raw(payload)
        packets.append(p)
    return packets, "worms"

# =================================================================
# Main Generator: ~10% per attack type, remaining Normal (if any)
# =================================================================
# =================================================================
# Main Generator: 50% Normal, 50% Anomalous traffic
# =================================================================
def generate_traffic(total_flows=100):
    print(f"Starting traffic generation → {TARGET_IP}:{TARGET_PORT}")
    print("Traffic mix: 50% normal, 50% anomaly\n")

    # List of anomaly generators
    anomaly_generators = [
        make_dos_attack,
        make_fuzzers_attack,
        make_generic_attack,
        make_exploits_attack,
        make_reconnaissance_attack,
        make_backdoors_attack,
        make_analysis_flow,
        make_shellcode_attack,
        make_worms_attack,
    ]

    for i in range(1, total_flows + 1):
        if i <= total_flows // 2:
            # First half → normal traffic
            pkts, label = make_normal_flow()
        else:
            # Second half → anomalous traffic (random attack type)
            generator = random.choice(anomaly_generators)
            pkts, label = generator()

        if i % 5 == 0:
            print(f"[Flow {i}] Type: {label.upper()} ({len(pkts)} packets)")

        # Send all packets
        for p in pkts:
            send(p, iface=INTERFACE, verbose=False)
            time.sleep(0.03)  # inter-packet delay

        # Delay before next flow
        time.sleep(random.uniform(0.5, 3.0))

    print("\nFinished traffic generation! 50% normal, 50% anomaly.")


# =================================================================
if __name__ == "__main__":
    random.seed(123)  # reproducible
    generate_traffic(total_flows=150)   # generates 75 normal + 75 anomaly flows

    print(f"Starting NORMAL traffic generation → {TARGET_IP}:{TARGET_PORT}")
    print("Traffic mix: 100% normal flows\n")

    for i in range(1, total_flows + 1):

        # Always generate a normal flow
        pkts, label = make_generic_attack()

        if i % 10 == 0:
            print(f"[{i}] normal flow ({len(pkts)} packets)")

        # Send all packets
        for p in pkts:
            send(p, iface=INTERFACE, verbose=False)
            time.sleep(0.03)

        # Delay before next flow
        time.sleep(random.uniform(0.5, 3.0))

    print("\nFinished! dos traffic generation complete.")
#=================================================================
if __name__ == "__main__":
    random.seed(123)  # reproducible
    generate_traffic(total_flows=150)   # generates ~30 attacks