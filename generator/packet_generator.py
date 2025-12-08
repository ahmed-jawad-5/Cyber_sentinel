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
# 2. DoS Attack (UNSW-NB15 style: HTTP DoS + SYN Flood mix)
# =================================================================
def make_dos_attack():
    packets = []
    src_port = 6666

    # 50–150 rapid packets: some SYN, some with huge payload (like Slowloris + Hulk)
    for i in range(random.randint(60, 120)):
        if random.random() < 0.4:
            # Pure SYN (classic SYN flood)
            p = IP(dst=TARGET_IP, src=RandIP())/TCP(sport=RandShort(), dport=TARGET_PORT, flags="S")
        else:
            # Large/fake HTTP requests (Hulk-style DoS)
            fake_url = random.choice([b"/admin.php", b"/login", b"/?id=999999", b"/search?q=" + b"A"*200])
            payload = b"GET " + fake_url + b" HTTP/1.1\r\nUser-Agent: Mozilla\r\n\r\n"
            p = IP(dst=TARGET_IP)/TCP(sport=src_port, dport=TARGET_PORT, flags="PA", seq=i*1000)/Raw(payload)

        packets.append(p)

    return packets, "dos"

# =================================================================
# 3. Fuzzers Attack (Malformed/random data to crash services)
# =================================================================
def make_fuzzers_attack():
    packets = []
    src_port = 31337

    for i in range(random.randint(15, 40)):
        # Totally random garbage payload + weird flags
        garbage = random.randbytes(random.randint(50, 2000))
        weird_flags = random.choice(["S", "F", "R", "P", "PA", "FA", "SA", "RA", "U"])

        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([TARGET_PORT, 22, 21, 3306, 445, 3389]),  # random service port
            flags=weird_flags,
            seq=random.randint(1, 999999),
            ack=random.randint(1, 999999)
        )/Raw(garbage)

        packets.append(p)
        time.sleep(0.02)  # fast but not too fast

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
# 9. Shellcode (binary payloads, NOP sled-like content)
# =================================================================
def make_shellcode_attack():
    packets = []
    src_port = random.randint(20000, 60000)

    for i in range(random.randint(5, 20)):
        nop_sled = b"\x90" * random.randint(50, 200)
        shell_bytes = random.randbytes(random.randint(50, 200))
        payload = nop_sled + shell_bytes
        p = IP(dst=TARGET_IP)/TCP(
            sport=src_port,
            dport=random.choice([TARGET_PORT, 4444, 31337]),
            flags="PA",
            seq=5000 + i * 50,
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
def generate_traffic(total_flows=100):
    print(f"Starting UNSW-NB15 traffic generation → {TARGET_IP}:{TARGET_PORT}")
    print("Traffic mix: ~10% per attack label (analysis, backdoor, backdoors, dos, exploits, fuzzers, generic, reconnaissance, shellcode, worms) + remaining normal\n")

    # Define attack labels and their generators
    attack_generators = {
        "analysis": make_analysis_flow,
        "backdoor": make_backdoor_attack,
        "backdoors": make_backdoors_attack,
        "dos": make_dos_attack,
        "exploits": make_exploits_attack,
        "fuzzers": make_fuzzers_attack,
        "generic": make_generic_attack,
        "reconnaissance": make_reconnaissance_attack,
        "shellcode": make_shellcode_attack,
        "worms": make_worms_attack,
    }

    attack_labels = list(attack_generators.keys())

    # Desired mix: 20% normal, remaining 80% split equally across all attacks
    normal_prob = 0.20
    attack_prob_each = (1.0 - normal_prob) / len(attack_labels)
    total_attack_prob = attack_prob_each * len(attack_labels)

    # Build cumulative distribution
    choices = []  # (threshold, label)
    cum = 0.0
    if normal_prob > 0:
        cum += normal_prob
        choices.append((cum, "normal"))
    for lbl in attack_labels:
        cum += attack_prob_each
        choices.append((cum, lbl))

    for i in range(1, total_flows + 1):
        r = random.random()
        chosen = None
        for threshold, lbl in choices:
            if r <= threshold:
                chosen = lbl
                break
        if chosen is None:
            chosen = "normal"

        if chosen == "normal":
            pkts, label = make_normal_flow()
            if i % 15 == 0:
                print(f"[{i}] normal flow")
        else:
            pkts, label = attack_generators[chosen]()
            print(f"[{i}] Sending {label} attack ({len(pkts)} packets)")

        # Send all packets
        for p in pkts:
            send(p, iface=INTERFACE, verbose=False)
            time.sleep(0.03 if label == "normal" else 0.005)

        # Delay before next flow
        time.sleep(random.uniform(0.5, 3.0) if label == "normal" else 0.1)

    print("\nFinished! Traffic generation complete.")

# =================================================================
if __name__ == "__main__":
    random.seed(123)  # reproducible
    generate_traffic(total_flows=150)   # generates ~30 attacks