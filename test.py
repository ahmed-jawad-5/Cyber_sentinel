import joblib
from generator.captures.feature_schema import FEATURE_ORDER

SCALER_PATH = "models/scaler.save"

print("\n=== LOADING SCALER ===")
scaler = joblib.load(SCALER_PATH)

print("\n=== FEATURE ORDER FROM CODE (receiver) ===")
print(FEATURE_ORDER)
print(f"Count: {len(FEATURE_ORDER)}")

print("\n=== FEATURE NAMES FROM SCALER (training time) ===")
if hasattr(scaler, "feature_names_in_"):
    print(list(scaler.feature_names_in_))
    print(f"Count: {len(scaler.feature_names_in_)}")
else:
    print("Scaler does NOT have feature_names_in_ (probably trained without DataFrame)")
    print(f"Scaler expects n_features_in_ = {scaler.n_features_in_}")
    exit()

print("\n=== CHECKING NAME MISMATCHES ===")
scaler_names = list(scaler.feature_names_in_)
code_names = FEATURE_ORDER

# Check feature names differences (ignoring order first)
missing_in_code = [f for f in scaler_names if f not in code_names]
extra_in_code = [f for f in code_names if f not in scaler_names]

if not missing_in_code and not extra_in_code:
    print("✔ No name mismatches!")
else:
    print("❌ Name mismatches found:")
    if missing_in_code:
        print(" - Missing in FEATURE_ORDER:", missing_in_code)
    if extra_in_code:
        print(" - Extra in FEATURE_ORDER:", extra_in_code)

print("\n=== CHECKING ORDER MISMATCHES ===")
order_mismatches = []
for i, (s, c) in enumerate(zip(scaler_names, code_names)):
    if s != c:
        order_mismatches.append((i, s, c))

if not order_mismatches:
    print("✔ No ordering mismatches! Order is correct.")
else:
    print("❌ Ordering mismatches:")
    for idx, s, c in order_mismatches:
        print(f" - Position {idx}: scaler expects '{s}', but receiver uses '{c}'")

print("\n=== DONE ===\n")
