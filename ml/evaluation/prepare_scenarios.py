"""Enrich existing fixtures and add only SSH/FTP/web scenarios, without fitting.

Run after build_scenarios if those original fixtures are regenerated.
Selection never uses model outputs. Exact training-feature matches are excluded
from new fixtures and disclosed for preserved legacy demonstration fixtures.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ml.evaluation.build_scenarios import _feature_dict
from ml.preprocessing.dataset import REPO_ID, REVISION, LoadConfig, load_split
from ml.preprocessing.preprocess import preprocess_frame
from ml.preprocessing.subset import load_dev_subset

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT/'data/scenarios'


def fingerprints(matrix):
    return [hashlib.sha256(row.astype('<f8').tobytes()).hexdigest() for row in matrix]


def select_rows(labels, hashes, train_hashes, wanted, limit=8):
    buckets = [[i for i, label in enumerate(labels) if label == name and hashes[i] not in train_hashes] for name in wanted]
    selected, seen = [], set()
    for offset in range(max(map(len, buckets), default=0)):
        for bucket in buckets:
            if offset < len(bucket):
                i = bucket[offset]
                if hashes[i] not in seen:
                    selected.append(i)
                    seen.add(hashes[i])
                    if len(selected) == limit:
                        return sorted(selected)
    return sorted(selected)


def main():
    raw = preprocess_frame(load_split(LoadConfig(config='random_3way', split='test')))
    hashes = fingerprints(raw.X)
    subset = ROOT/'data/processed/dev_random_train.parquet'
    train = preprocess_frame(load_dev_subset(str(subset)))
    train_hashes = set(fingerprints(train.X))
    training_digest = hashlib.sha256(subset.read_bytes()).hexdigest()
    lookup = defaultdict(list)
    for i, pair in enumerate(zip(raw.labels, hashes)):
        lookup[pair].append(i)
    # Preserve every legacy feature vector and side-car. Only add provenance.
    documents = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in SCENARIOS.glob('*.json')}
    new_types = {
        'ssh_bruteforce': ['SSH-Patator'],
        'ftp_bruteforce': ['FTP-Patator'],
        'web_attack': ['Web Attack - Brute Force', 'Web Attack - Sql Injection', 'Web Attack - XSS'],
    }
    availability = {}
    for number, (name, wanted) in enumerate(new_types.items(), 70):
        indices = select_rows(raw.labels, hashes, train_hashes, wanted)
        availability[name] = {label: sum(raw.labels[i] == label for i in indices) for label in wanted}
        if not indices:
            continue
        flows = [dict(seq=seq, source=f'10.0.0.{number}', destination='10.0.0.20',
                      service_port=int(raw.X[i, 0]), ground_truth_label=raw.labels[i],
                      features=_feature_dict(raw, i), source_row_index=i)
                 for seq, i in enumerate(indices)]
        documents[name] = {
            'schema':'scenario/v1', 'name':name,
            'description':f'{len(flows)} held-out {name.replace("_", " ")} records; selected without predictions',
            'logical_interval_seconds':1.0, 'flows':flows,
        }
    manifest = {'dataset':REPO_ID, 'revision':REVISION, 'new_scenario_label_support':availability, 'scenarios':{}}
    for name in sorted(documents):
        doc = documents[name]
        new = name in new_types
        doc['purpose'] = 'benign_control' if name == 'normal' else 'benign_anomaly_challenge' if name == 'unknown' else 'known_attack'
        doc['provenance'] = {
            'dataset':REPO_ID, 'revision':REVISION, 'config':'random_3way', 'split':'test',
            'feature_order':raw.columns,
            'training_subset_sha256':training_digest,
            'training_check':'exact canonical float64 feature match against deployed dev_random_train; not proof of semantic independence',
            'sampling':'prediction-independent round-robin labels, exclude train/repeated feature matches, up to eight' if new else
                       'preserved legacy demonstration selection; normal/unknown were selected using runtime verdicts',
            'sampling_seed':None, 'seed_note':'deterministic pinned row order; no random sampling',
            'synthetic_fields':['source','destination','service_port','seq','replay_time'],
            'unknown_attack_detection_established':False,
        }
        overlaps = 0
        for flow in doc['flows']:
            row = np.array([flow['features'][c] for c in raw.columns], dtype='float64')
            digest = fingerprints(row.reshape(1,-1))[0]
            matches = lookup[(flow['ground_truth_label'], digest)]
            if not matches:
                raise ValueError(f'{name} fixture has no matching pinned source row')
            index = flow.pop('source_row_index', matches[0])
            flow['provenance'] = {
                'source_row_index':index, 'feature_sha256':digest,
                'equivalent_source_rows':len(matches),
                'locator_basis':'selected partition row' if new else 'first equivalent row; original row ID was not recorded',
                'matches_deployed_training_features':digest in train_hashes,
            }
            overlaps += digest in train_hashes
        manifest['scenarios'][name] = {'flows':len(doc['flows']), 'training_feature_matches':overlaps,
                                       'truth_counts':dict(Counter(f['ground_truth_label'] for f in doc['flows']))}
        path = SCENARIOS/f'{name}.json'
        data = json.dumps(doc, indent=2).encode('utf-8')
        tmp = path.with_suffix('.json.tmp');tmp.write_bytes(data);tmp.replace(path)
        assert json.loads(path.read_text(encoding='utf-8')) == doc
    out = ROOT/'data/processed/scenario_provenance.json'
    out.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
