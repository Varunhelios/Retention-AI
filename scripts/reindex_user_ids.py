# Reindex all user IDs across datasets and outputs to a compact, sequential range.
# - Builds a stable mapping from old -> new IDs based on sorted old IDs
# - Starts from 2000 (configurable)
# - Updates CSVs in `datasets/` and JSON/PNG files in `outputs/`
# - Writes timestamped backups before modifying files

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

import pandas as pd


BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / 'datasets'
OUTPUTS_DIR = BASE_DIR / 'outputs'

START_ID = 2000  # change if you prefer a different base


DATASET_FILES: List[Path] = [
    DATASET_DIR / 'main-dataset.csv',
    DATASET_DIR / 'model_a_train.csv',
    DATASET_DIR / 'model_b_train.csv',
    DATASET_DIR / 'churn_prediction.csv',
    DATASET_DIR / 'model_a_predictions.csv',
    DATASET_DIR / 'model_b_predictions.csv',
    DATASET_DIR / 'sentiment_analysis.csv',
]

EXPLAIN_DIR = OUTPUTS_DIR / 'explanations'
CHART_DIR = OUTPUTS_DIR / 'charts'


def backup_paths(paths: List[Path], backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    for p in paths:
        if p.exists() and p.is_file():
            target = backup_root / p.name
            shutil.copy2(str(p), str(target))


def build_id_map() -> Dict[int, int]:
    main_path = DATASET_DIR / 'main-dataset.csv'
    if not main_path.exists():
        raise FileNotFoundError(f"Missing {main_path}")
    df = pd.read_csv(main_path)
    if 'userid' not in df.columns:
        raise ValueError("'userid' column not found in main-dataset.csv")
    old_ids = sorted(pd.to_numeric(df['userid'], errors='coerce').dropna().astype(int).unique().tolist())
    id_map: Dict[int, int] = {}
    next_id = START_ID
    for oid in old_ids:
        id_map[oid] = next_id
        next_id += 1
    return id_map


def remap_csv(path: Path, id_map: Dict[int, int]) -> None:
    if not path.exists() or os.path.getsize(path) == 0:
        return
    df = pd.read_csv(path)
    if 'userid' in df.columns:
        df['userid'] = pd.to_numeric(df['userid'], errors='coerce')
        df['userid'] = df['userid'].map(lambda x: id_map.get(int(x), x) if pd.notna(x) else x)
    df.to_csv(path, index=False)


def remap_explanations(explain_dir: Path, id_map: Dict[int, int]) -> None:
    if not explain_dir.exists():
        return
    for p in explain_dir.glob('user_*.json'):
        try:
            with open(p, 'r') as f:
                data = json.load(f)
            uid = int(str(data.get('user_id')))
            new_id = id_map.get(uid)
            if new_id is None:
                continue
            data['user_id'] = new_id
            out_tmp = p.with_suffix('.json.tmp')
            with open(out_tmp, 'w') as f:
                json.dump(data, f, indent=2)
            out_tmp.replace(p)
            # rename file name
            new_name = p.with_name(f'user_{new_id}.json')
            if new_name != p:
                if new_name.exists():
                    new_name.unlink()
                p.rename(new_name)
        except Exception:
            continue


def remap_charts(chart_dir: Path, id_map: Dict[int, int]) -> None:
    if not chart_dir.exists():
        return
    for p in chart_dir.glob('user_*.png'):
        try:
            stem = p.stem  # user_<id>
            old_id = int(stem.split('_')[1])
            new_id = id_map.get(old_id)
            if new_id is None:
                continue
            new_name = p.with_name(f'user_{new_id}.png')
            if new_name != p:
                if new_name.exists():
                    new_name.unlink()
                p.rename(new_name)
        except Exception:
            continue


def main() -> None:
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_root = DATASET_DIR / 'backups' / f'reindex_{ts}'
    backup_paths(DATASET_FILES, backup_root)

    id_map = build_id_map()

    # Remap CSVs
    for path in DATASET_FILES:
        remap_csv(path, id_map)

    # Remap explanations and charts
    out_backup = OUTPUTS_DIR / 'backups' / f'reindex_{ts}'
    backup_paths(list(EXPLAIN_DIR.glob('*.json')), out_backup)
    backup_paths(list(CHART_DIR.glob('*.png')), out_backup)
    remap_explanations(EXPLAIN_DIR, id_map)
    remap_charts(CHART_DIR, id_map)

    print(f"[OK] Reindexed {len(id_map)} users starting at {START_ID}")
    print(f"[OK] Backups saved to {backup_root} and {out_backup}")


if __name__ == '__main__':
    main()




