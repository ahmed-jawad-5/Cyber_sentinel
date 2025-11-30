# run_sniffer.py
from capture.flow_sniffer import FlowSniffer
from capture.feature_extractor import extract_features
from capture.utils_capture import init_csv_files
from capture.feature_extractor import extract_features

# 34 feature column names
FEATURE_COLUMNS = [
    'proto', 'state', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'service',
    'Sload', 'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 'res_bdy_len',
    'Sjit', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports',
    'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src',
    'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm',
    'ct_dst_src_ltm'
]

def main():
    # Initialize CSV file
    init_csv_files(FEATURE_COLUMNS)

    # Start sniffer
    sniffer = FlowSniffer()
    try:
        sniffer.start()
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Stopping sniffer...")
        sniffer.stop()

if __name__ == "__main__":
    main()
