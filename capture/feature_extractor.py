# capture/feature_extractor.py
class FeatureExtractor:
    def extract(self, flow):
        """
        Given a raw flow (list of packets or dict), extract 34 features.
        Must return a dict with keys matching selected_features.
        """
        features = {
            'proto': flow.get('proto', 6),
            'state': flow.get('state', 1),
            'sbytes': flow.get('sbytes', 0),
            'dbytes': flow.get('dbytes', 0),
            'sttl': flow.get('sttl', 64),
            'dttl': flow.get('dttl', 64),
            'sloss': flow.get('sloss', 0),
            'service': flow.get('service', 0),
            'Sload': flow.get('Sload', 0),
            'swin': flow.get('swin', 0),
            'dwin': flow.get('dwin', 0),
            'stcpb': flow.get('stcpb', 0),
            'dtcpb': flow.get('dtcpb', 0),
            'smeansz': flow.get('smeansz', 0),
            'dmeansz': flow.get('dmeansz', 0),
            'res_bdy_len': flow.get('res_bdy_len', 0),
            'Sjit': flow.get('Sjit', 0),
            'Sintpkt': flow.get('Sintpkt', 0),
            'Dintpkt': flow.get('Dintpkt', 0),
            'tcprtt': flow.get('tcprtt', 0),
            'synack': flow.get('synack', 0),
            'ackdat': flow.get('ackdat', 0),
            'is_sm_ips_ports': flow.get('is_sm_ips_ports', 0),
            'ct_state_ttl': flow.get('ct_state_ttl', 0),
            'ct_flw_http_mthd': flow.get('ct_flw_http_mthd', 0),
            'is_ftp_login': flow.get('is_ftp_login', 0),
            'ct_ftp_cmd': flow.get('ct_ftp_cmd', 0),
            'ct_srv_src': flow.get('ct_srv_src', 0),
            'ct_srv_dst': flow.get('ct_srv_dst', 0),
            'ct_dst_ltm': flow.get('ct_dst_ltm', 0),
            'ct_src_ltm': flow.get('ct_src_ltm', 0),
            'ct_src_dport_ltm': flow.get('ct_src_dport_ltm', 0),
            'ct_dst_sport_ltm': flow.get('ct_dst_sport_ltm', 0),
            'ct_dst_src_ltm': flow.get('ct_dst_src_ltm', 0)
        }
        return features
