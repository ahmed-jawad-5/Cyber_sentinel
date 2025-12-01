import joblib
import numpy as np

class AnomalyDetector:
    def __init__(self, model_path="models/XGBoost_model.pkl", scaler_path="models/scalar.pkl"):
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path) if scaler_path else None
        self.selected_features = ['proto', 'state', 'sbytes', 'dbytes', 'sttl', 'dttl', 
                                  'sloss', 'service', 'Sload', 'swin', 'dwin', 'stcpb', 
                                  'dtcpb', 'smeansz', 'dmeansz', 'res_bdy_len', 'Sjit', 
                                  'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat', 
                                  'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd', 
                                  'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst', 
                                  'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm', 
                                  'ct_dst_sport_ltm', 'ct_dst_src_ltm']

    def predict(self, flow_dict):
        features = [flow_dict[f] for f in self.selected_features]
        X = np.array(features).reshape(1, -1)
        if self.scaler:
            X = self.scaler.transform(X)
        label = self.model.predict(X)[0]
        return "anomaly" if label == 1 else "normal"
