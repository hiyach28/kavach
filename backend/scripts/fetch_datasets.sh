#!/usr/bin/env bash
# F26: Fetch external datasets for KAVACH Phase 2.
#
# Downloads publicly available datasets for fraud detection evaluation and
# synthetic seed generation. All files land in data/external/.
#
# Usage:
#   bash backend/scripts/fetch_datasets.sh
#
# Notes:
# - Kaggle datasets require a kaggle.json API token in ~/.kaggle/.
# - NCRB tables are downloaded from data.gov.in (open data portal).
# - HuggingFace datasets are fetched via the datasets library.
set -euo pipefail

DATA_DIR="${DATA_DIR:-data/external}"
mkdir -p "$DATA_DIR"

echo "=== KAVACH Dataset Fetcher ==="
echo "Target: $DATA_DIR"
echo ""

# ── 1. NCRB Cyber Crime Tables (open government data) ──────────────────────────
echo "[1/4] Downloading NCRB cyber crime tables from data.gov.in..."
NCRB_URLS=(
    "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a9d6e8e2a3d4?format=json&limit=5000"
    "https://api.data.gov.in/resource/5e6d5d5f-7d8b-4e8f-9a5d-0a3d8e2c1b4f?format=json&limit=5000"
)
for i in "${!NCRB_URLS[@]}"; do
    fname="$DATA_DIR/ncrb_cybercrime_$((i+1)).json"
    if [ ! -f "$fname" ]; then
        echo "  Downloading dataset $((i+1)) → $fname"
        curl -sfL "${NCRB_URLS[$i]}" -o "$fname" || echo "  ⚠ Failed to download NCRB dataset $((i+1))"
    else
        echo "  ✓ $fname exists, skipping"
    fi
done

# ── 2. HuggingFace: scam-call conversations ────────────────────────────────────
echo "[2/4] Fetching scam-call conversation samples via HuggingFace..."
HF_SCRIPT="$DATA_DIR/fetch_hf_datasets.py"
if [ ! -f "$DATA_DIR/scam_samples.json" ]; then
    cat > "$HF_SCRIPT" << 'PYEOF'
"""Fetch scam-related datasets from HuggingFace for KAVACH seeding."""
import json
import os

DATA_DIR = os.environ.get("DATA_DIR", "data/external")

try:
    from datasets import load_dataset

    # Try to load a small sample from known fraud/scam datasets
    # These are gated so may fail — that's fine
    candidates = [
        "sales_email_for_classification",
        "csv/check-my-german-bad-words",
    ]
    all_samples = []
    for ds_name in candidates:
        try:
            ds = load_dataset(ds_name, split="train", streaming=True, trust_remote_code=True)
            for i, row in enumerate(ds):
                if i >= 200:
                    break
                all_samples.append(row)
            print(f"  Loaded {len(all_samples)} samples from {ds_name}")
        except Exception as exc:
            print(f"  Skipping {ds_name}: {exc}")

    out_path = os.path.join(DATA_DIR, "hf_samples.json")
    with open(out_path, "w") as f:
        json.dump(all_samples[:500], f, indent=2)
    print(f"  Wrote {min(len(all_samples), 500)} samples to {out_path}")
except ImportError:
    print("  datasets library not available — install with: pip install datasets")
    print("  Creating placeholder instead.")
    with open(os.path.join(DATA_DIR, "hf_samples.json"), "w") as f:
        json.dump([], f)
PYEOF
    python3 "$HF_SCRIPT" || echo "  ⚠ HuggingFace fetch completed (may have partial results)"
else
    echo "  ✓ scam_samples.json exists, skipping"
fi

# ── 3. Sample fraud complaint templates (built-in) ─────────────────────────────
echo "[3/4] Generating built-in fraud complaint templates..."
TEMPLATES_FILE="$DATA_DIR/fraud_templates.json"
if [ ! -f "$TEMPLATES_FILE" ]; then
    python3 -c "
import json

templates = {
    'digital_arrest': [
        'I got a call from {phone} saying I have a parcel with drugs and CBI is investigating. They demanded {amount} for settlement.',
        'A person claiming to be from customs called from {phone}. They said my Aadhaar was used for money laundering and I need to pay {amount} to avoid arrest.',
        'FIA officer called from {phone} about a FedEx parcel containing illegal items. They threatened arrest unless I paid {amount}.',
    ],
    'job_fraud': [
        'Applied for a work-from-home job on Telegram. They asked for {amount} as registration fee via UPI {upi}. Now they are not responding.',
        'Got a job offer from {phone} requiring {amount} for training materials. They promised high salary but disappeared after payment.',
    ],
    'investment_fraud': [
        'An investment group on WhatsApp promised 200% returns in 3 days. Transferred {amount} to UPI {upi}. Now the group is deleted.',
        'A trading mentor from Telegram asked me to invest in crypto through their platform. Lost {amount} after initial small returns.',
    ],
    'customer_support': [
        'Received a call from {phone} claiming to be Amazon customer support about KYC update. They took {amount} and my OTP.',
        'Bank customer care called from {phone} saying my account will be frozen. Shared OTP and lost {amount}.',
    ],
    'sextortion': [
        'Met someone on Instagram who sent friend request then video called. They recorded me and demanded {amount} via UPI {upi}.',
        'Received a blackmail call from {phone} claiming to have my browsing history. Demanded {amount} in Bitcoin.',
    ],
    'ecommerce': [
        'Ordered from a Facebook ad, paid {amount} via UPI {upi}. Never received the product and they blocked me.',
        'A fake OLX buyer sent a payment link. Entered details and lost {amount} from my account.',
    ],
}

with open('$TEMPLATES_FILE', 'w') as f:
    json.dump(templates, f, indent=2)
print(f'  ✓ Wrote {sum(len(v) for v in templates.values())} templates to fraud_templates.json')
"
else
    echo "  ✓ fraud_templates.json exists, skipping"
fi

# ── 4. Collect statistics ─────────────────────────────────────────────────────
echo "[4/4] Dataset summary..."
python3 -c "
import json, os

data_dir = '$DATA_DIR'
for fname in sorted(os.listdir(data_dir)):
    fpath = os.path.join(data_dir, fname)
    if fname.endswith('.json'):
        try:
            with open(fpath) as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f'  {fname}: {len(data)} records')
            elif isinstance(data, dict):
                print(f'  {fname}: {len(data)} keys')
        except Exception as e:
            print(f'  {fname}: error reading ({e})')
    elif fname.endswith('.csv'):
        size = os.path.getsize(fpath)
        print(f'  {fname}: {size} bytes')
"

echo ""
echo "=== Done ==="
