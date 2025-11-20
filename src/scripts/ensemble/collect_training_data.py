#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path('data')
training_dir = data_dir / 'ensemble_training'
training_dir.mkdir(exist_ok=True, parents=True)

print("\nCollecting ensemble training data...")

files = list(data_dir.glob('*_analysis_all_players_*.csv'))
if not files:
    print("No files found")
    exit(1)

print(f"Found {len(files)} files\n")

base = pd.read_csv(files[0])[['player_name']].drop_duplicates().reset_index(drop=True)

for i, f in enumerate(files, 1):
    factor = f.name.split('_analysis_')[0]
    try:
        df = pd.read_csv(f)
        if df.empty:
            print(f"[{i}/{len(files)}] ⚠️  {factor} (empty)")
            continue
        score_col = [c for c in df.columns if 'score' in c.lower()]
        if score_col:
            temp = df[['player_name', score_col[0]]].copy()
            temp.columns = ['player_name', f'{factor}_score']
            temp = temp.groupby('player_name').mean().reset_index()
            base = base.merge(temp, on='player_name', how='left')
            print(f"[{i}/{len(files)}] ✓ {factor}")
    except Exception as e:
        print(f"[{i}/{len(files)}] ✗ {factor}: {e}")

base['fantasy_points'] = np.nan
output = training_dir / 'training_data.csv'
base.to_csv(output, index=False)
print(f"\n✓ Saved: {output} ({len(base)} players, {len(base.columns)} features)")
print("\n✅ Training data ready! Now integrate with daily workflow...")
