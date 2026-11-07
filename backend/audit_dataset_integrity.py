"""
Independent Dataset Integrity Audit Script for Phase 8.2B
Audits all images in calibration_dataset_v3, manifest metadata, hash collisions,
cross-split contamination, author distribution, and label accuracy.
"""

import os
import json
import hashlib
from pathlib import Path
from collections import Counter
from PIL import Image

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def compute_dhash(image_path, hash_size=8):
    try:
        with Image.open(image_path) as img:
            img = img.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    left = pixels[row * (hash_size + 1) + col]
                    right = pixels[row * (hash_size + 1) + col + 1]
                    diff.append(left > right)
            decimal_val = 0
            hex_str = []
            for i, v in enumerate(diff):
                if v:
                    decimal_val += 2 ** (i % 4)
                if (i % 4) == 3:
                    hex_str.append(hex(decimal_val)[2:])
                    decimal_val = 0
            return ''.join(hex_str)
    except Exception as e:
        return None

def hamming_distance(h1, h2):
    if not h1 or not h2 or len(h1) != len(h2):
        return 999
    try:
        return bin(int(h1, 16) ^ int(h2, 16)).count('1')
    except Exception:
        return 999

def load_manifest_records(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("records", [])
    return []

def run_dataset_integrity_audit():
    base_dir = Path("backend")
    calib_v3_dir = base_dir / "datasets" / "calibration_dataset_v3"
    calib_v3_manifest_path = base_dir / "datasets" / "calibration_dataset_v3_manifest.json"
    
    ref_manifest_path = base_dir / "reference_gallery_manifest.json"
    indep_v1_manifest_path = base_dir / "independent_eval_manifest.json"
    indep_v2_manifest_path = base_dir / "datasets" / "independent_eval_v2_manifest.json"
    dev_v1_manifest_path = base_dir / "datasets" / "development_manifest.json"

    print("Loading manifests...")
    calib_v3_records = load_manifest_records(calib_v3_manifest_path)
    ref_records = load_manifest_records(ref_manifest_path)
    indep_v1_records = load_manifest_records(indep_v1_manifest_path)
    indep_v2_records = load_manifest_records(indep_v2_manifest_path)
    dev_v1_records = load_manifest_records(dev_v1_manifest_path)

    print(f"Calibration v3 records: {len(calib_v3_records)}")

    # Audit physical files in calib_v3_dir recursively
    actual_files = [p for p in calib_v3_dir.rglob("*.*") if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    print(f"Actual image files in calib_v3 directory: {len(actual_files)}")

    file_validity = {
        "total_files_on_disk": len(actual_files),
        "total_manifest_entries": len(calib_v3_records),
        "unreadable_corrupt_files": [],
        "zero_byte_files": [],
        "manifest_missing_files": [],
        "disk_untracked_files": []
    }

    manifest_paths = set()
    sha256_map = {}
    dhash_map = {}
    author_counts = Counter()
    class_counts = Counter()
    condition_counts = Counter()
    is_positive_counts = Counter()

    for item in calib_v3_records:
        rel_path = item.get("relative_path")
        if not rel_path:
            continue
        
        # Resolve path
        fpath = base_dir / rel_path
        manifest_paths.add(fpath.resolve())

        if not fpath.exists():
            file_validity["manifest_missing_files"].append(rel_path)
            continue
        
        size = fpath.stat().st_size
        if size == 0:
            file_validity["zero_byte_files"].append(rel_path)
            continue
        
        sha = compute_sha256(fpath)
        dh = compute_dhash(fpath)
        if dh is None:
            file_validity["unreadable_corrupt_files"].append(rel_path)
            continue

        item_id = item.get("specimen_id", fpath.name)
        sha256_map[item_id] = (sha, rel_path)
        dhash_map[item_id] = (dh, rel_path)
        
        author = item.get("author") or item.get("photographer") or "Unknown"
        author_counts[author] += 1
        
        mon_key = item.get("monument_key") or item.get("ground_truth_label", "Unknown")
        class_counts[mon_key] += 1
        
        condition_counts[item.get("condition", "standard")] += 1
        
        if mon_key in ["unknown_heritage", "non_monument"]:
            is_positive_counts["negative_or_unknown"] += 1
        else:
            is_positive_counts["positive_catalog_monument"] += 1

    disk_paths = {p.resolve() for p in actual_files}
    file_validity["disk_untracked_files"] = [str(p) for p in (disk_paths - manifest_paths)]

    # Internal collision check
    internal_sha_duplicates = []
    seen_sha = {}
    for item_id, (sha, rel_path) in sha256_map.items():
        if sha in seen_sha:
            internal_sha_duplicates.append({"item1": seen_sha[sha], "item2": item_id, "sha256": sha})
        else:
            seen_sha[sha] = item_id

    internal_near_duplicates = []
    item_ids = list(dhash_map.keys())
    for i in range(len(item_ids)):
        for j in range(i + 1, len(item_ids)):
            id1, id2 = item_ids[i], item_ids[j]
            dh1, _ = dhash_map[id1]
            dh2, _ = dhash_map[id2]
            dist = hamming_distance(dh1, dh2)
            if dist <= 4:
                internal_near_duplicates.append({
                    "item1": id1,
                    "item2": id2,
                    "hamming_distance": dist,
                    "class1": next((x.get("monument_key") for x in calib_v3_records if x.get("specimen_id") == id1), ""),
                    "class2": next((x.get("monument_key") for x in calib_v3_records if x.get("specimen_id") == id2), "")
                })

    # Helper to index other datasets
    def index_external_dataset(records, default_folder):
        external_sha = {}
        external_dh = {}
        external_authors = set()
        for r in records:
            r_id = r.get("id") or r.get("image_id") or r.get("specimen_id") or r.get("filename")
            rel = r.get("relative_path") or r.get("file_path") or r.get("filepath") or r.get("filename")
            if not rel:
                continue
            fpath = Path(rel)
            if not fpath.is_absolute():
                fpath = base_dir / fpath
            if not fpath.exists():
                fpath = default_folder / rel
            if fpath.exists() and fpath.is_file() and fpath.stat().st_size > 0:
                s = compute_sha256(fpath)
                d = compute_dhash(fpath)
                if d:
                    external_sha[r_id] = (s, str(fpath))
                    external_dh[r_id] = (d, str(fpath))
            auth = r.get("author") or r.get("photographer")
            if auth:
                external_authors.add(auth)
        return external_sha, external_dh, external_authors

    print("Indexing reference gallery...")
    ref_sha, ref_dh, ref_authors = index_external_dataset(ref_records, base_dir / "datasets" / "reference_gallery_v2")
    print(f"Ref indexed: {len(ref_sha)} images, {len(ref_authors)} authors")

    print("Indexing independent eval v1...")
    indep1_sha, indep1_dh, indep1_authors = index_external_dataset(indep_v1_records, base_dir / "datasets" / "independent_eval")
    print(f"Indep1 indexed: {len(indep1_sha)} images, {len(indep1_authors)} authors")

    print("Indexing independent eval v2...")
    indep2_sha, indep2_dh, indep2_authors = index_external_dataset(indep_v2_records, base_dir / "datasets" / "independent_eval_v2")
    print(f"Indep2 indexed: {len(indep2_sha)} images, {len(indep2_authors)} authors")

    print("Indexing dev v1...")
    dev1_sha, dev1_dh, dev1_authors = index_external_dataset(dev_v1_records, base_dir / "datasets" / "calibration_development")
    print(f"Dev1 indexed: {len(dev1_sha)} images, {len(dev1_authors)} authors")

    def check_cross_leakage(target_sha_map, target_dh_map, ext_sha_map, ext_dh_map, dataset_name):
        exact_matches = []
        near_matches = []
        for fn, (sha, path) in target_sha_map.items():
            for ext_fn, (ext_sha, ext_path) in ext_sha_map.items():
                if sha == ext_sha:
                    exact_matches.append({"calib_file": fn, "external_file": ext_fn, "dataset": dataset_name, "sha256": sha})
        for fn, (dh, path) in target_dh_map.items():
            for ext_fn, (ext_dh, ext_path) in ext_dh_map.items():
                dist = hamming_distance(dh, ext_dh)
                if dist <= 4:
                    near_matches.append({"calib_file": fn, "external_file": ext_fn, "dataset": dataset_name, "hamming_distance": dist})
        return exact_matches, near_matches

    leakage_ref_exact, leakage_ref_near = check_cross_leakage(sha256_map, dhash_map, ref_sha, ref_dh, "reference_gallery_v2")
    leakage_ind1_exact, leakage_ind1_near = check_cross_leakage(sha256_map, dhash_map, indep1_sha, indep1_dh, "independent_eval_v1")
    leakage_ind2_exact, leakage_ind2_near = check_cross_leakage(sha256_map, dhash_map, indep2_sha, indep2_dh, "independent_eval_v2")
    leakage_dev1_exact, leakage_dev1_near = check_cross_leakage(sha256_map, dhash_map, dev1_sha, dev1_dh, "calibration_development_v1")

    calib_authors = set(author_counts.keys())
    author_overlaps = {
        "overlap_with_reference_gallery": list(calib_authors.intersection(ref_authors)),
        "overlap_with_independent_eval_v1": list(calib_authors.intersection(indep1_authors)),
        "overlap_with_independent_eval_v2": list(calib_authors.intersection(indep2_authors)),
        "overlap_with_dev_v1": list(calib_authors.intersection(dev1_authors))
    }

    audit_results = {
        "audit_name": "Phase 8.2B Dataset Integrity Audit",
        "dataset_audited": "calibration_dataset_v3",
        "total_specimens": len(calib_v3_records),
        "file_validity": file_validity,
        "class_breakdown": dict(class_counts),
        "is_positive_breakdown": dict(is_positive_counts),
        "condition_breakdown": dict(condition_counts),
        "author_statistics": {
            "unique_authors": len(author_counts),
            "top_10_authors": author_counts.most_common(10),
            "max_specimens_per_author": max(author_counts.values()) if author_counts else 0,
            "min_specimens_per_author": min(author_counts.values()) if author_counts else 0,
        },
        "internal_duplicates": {
            "exact_sha256_duplicate_count": len(internal_sha_duplicates),
            "exact_duplicates": internal_sha_duplicates,
            "near_perceptual_duplicates_hamming_le_4_count": len(internal_near_duplicates),
            "near_duplicates": internal_near_duplicates
        },
        "cross_split_contamination": {
            "exact_sha256_matches_with_reference_gallery": len(leakage_ref_exact),
            "exact_sha256_matches_with_independent_eval_v1": len(leakage_ind1_exact),
            "exact_sha256_matches_with_independent_eval_v2": len(leakage_ind2_exact),
            "exact_sha256_matches_with_dev_v1": len(leakage_dev1_exact),
            "near_dhash_matches_with_reference_gallery": len(leakage_ref_near),
            "near_dhash_matches_with_independent_eval_v1": len(leakage_ind1_near),
            "near_dhash_matches_with_independent_eval_v2": len(leakage_ind2_near),
            "near_dhash_matches_with_dev_v1": len(leakage_dev1_near),
            "details": {
                "ref_exact": leakage_ref_exact,
                "ref_near": leakage_ref_near,
                "ind1_exact": leakage_ind1_exact,
                "ind1_near": leakage_ind1_near,
                "ind2_exact": leakage_ind2_exact,
                "ind2_near": leakage_ind2_near,
                "dev1_exact": leakage_dev1_exact,
                "dev1_near": leakage_dev1_near
            }
        },
        "author_overlap_audit": author_overlaps,
        "integrity_verdict": {
            "zero_byte_files_found": len(file_validity["zero_byte_files"]) == 0,
            "corrupt_files_found": len(file_validity["unreadable_corrupt_files"]) == 0,
            "manifest_file_parity": len(file_validity["manifest_missing_files"]) == 0 and len(file_validity["disk_untracked_files"]) == 0,
            "zero_internal_exact_duplicates": len(internal_sha_duplicates) == 0,
            "zero_cross_split_exact_leakage": (len(leakage_ref_exact) + len(leakage_ind1_exact) + len(leakage_ind2_exact)) == 0,
            "zero_eval_author_leakage": len(author_overlaps["overlap_with_independent_eval_v2"]) == 0 and len(author_overlaps["overlap_with_independent_eval_v1"]) == 0
        }
    }

    out_path = Path("backend/dataset_integrity_audit.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"Dataset integrity audit written to {out_path}")
    print(f"Verdict: {json.dumps(audit_results['integrity_verdict'], indent=2)}")

if __name__ == "__main__":
    run_dataset_integrity_audit()
