python scripts/acquire_apc.py --rows 100000 --out backend/data/raw/ac_transit_apc.csv
python -m backend.app.train
