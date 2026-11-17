#!/usr/bin/env python3
"""Download pinned Shalla artifact, run the authors' C generator, export lossless text."""
import csv, hashlib, json, os, subprocess, sys, tarfile, urllib.request
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PIN = "c970c3436465355e8b13c6d525bcc0dc72620312"
BASE = "https://raw.githubusercontent.com/saltsystemslab/How-to-Train-Your-Filter/" + PIN
N, POS, Q = 3905928, 2926705, 10000000
WORK = ROOT / ".upstream" / "shalla"
OUT = ROOT / "data" / "shalla"

def download(rel, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        tmp = target.with_suffix(target.suffix + ".part")
        with urllib.request.urlopen(BASE + "/" + rel, timeout=120) as src, tmp.open("wb") as out:
            import shutil
            shutil.copyfileobj(src, out)
        tmp.replace(target)
    return target

def digest(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = download("data/compressed/shalla.tar.gz", WORK / "data" / "shalla.tar.gz")
    # Verify pinned Git blob content, not a mirror or a freshly generated dataset.
    with archive.open("rb") as f:
        h = hashlib.sha1(("blob " + str(archive.stat().st_size) + "\0").encode())
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    if h.hexdigest() != "b1747b1229a5bc4041b7c28b829b0cb05182257a":
        raise ValueError("Archive Git blob hash mismatch")
    source = WORK / "data" / "shalla_combined.csv"
    if not source.exists():
        with tarfile.open(archive) as t:
            members = [m for m in t.getmembers() if Path(m.name).name == source.name and m.isfile()]
            if len(members) != 1:
                raise ValueError("Expected exactly one Shalla CSV in archive")
            with t.extractfile(members[0]) as f, source.open("wb") as g:
                import shutil
                shutil.copyfileobj(f,g)
    keys, labels = [], bytearray()
    with source.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not {"url", "label"}.issubset(reader.fieldnames or []):
            raise ValueError(reader.fieldnames)
        for row in reader:
            k = row["url"]
            if not k or "\n" in k or "\r" in k or "\0" in k or row["label"] not in ("0","1"):
                raise ValueError("Unsupported or invalid CSV row")
            keys.append(k)
            labels.append(int(row["label"]))
    if len(keys) != N or sum(labels) != POS:
        raise ValueError((len(keys), sum(labels)))
    stored = {k for k,l in zip(keys,labels) if l}
    if any(k in stored for k,l in zip(keys,labels) if not l):
        raise ValueError("Negative key also appears in stored keys")
    del stored
    with (OUT/"dataset.txt").open("w",encoding="utf-8",newline="\n") as f:
        for k,l in zip(keys,labels):
            if l: f.write(k+"\n")
    src = WORK / "adaptiveqf"
    for rel in ("test/write_queries.c","src/rand_util.c","include/rand_util.h"):
        download("adaptiveqf/"+rel,src/rel)
    subprocess.run([os.environ.get("CC","gcc"), "-std=gnu11","-O2","-I.", "test/write_queries.c","src/rand_util.c","-lm","-o","write_queries"],cwd=src,check=True)
    for extra in ([],["1.5"]):
        subprocess.run(["./write_queries",str(Q),"shalla",str(N),*extra],cwd=src,check=True)
    # Same rank-to-row mapping as upstream convert_query_binaries.py.
    perm = np.random.default_rng(0).permutation(N)
    manifest = {"upstream_commit":PIN,"archive_sha256":digest(archive),"source_csv_sha256":digest(source),
                "stored_rows":POS,"candidate_rows":N,"numpy_version":np.__version__,"workloads":{}}
    for name, stem in (("uniform","unif"),("zipf","zipf")):
        binary = WORK/"data"/(stem+"_10M_shalla.bin")
        ranks = np.fromfile(binary, dtype=np.int32)
        if len(ranks)!=Q or ranks.min() < (1 if name=="zipf" else 0) or ranks.max() > (N if name=="zipf" else N-1):
            raise ValueError("Invalid query index binary")
        indices = perm[ranks.astype(np.int64)-1] if name=="zipf" else ranks
        path = OUT/("queries_"+name+".txt")
        positives=0
        with path.open("w", encoding="utf-8", newline="\n") as f:
            for i in indices:
                j=int(i)
                f.write(keys[j]+"\n")
                positives+=labels[j]
        np.save(OUT/("indices_"+name+".npy"),indices)
        manifest["workloads"][name]={"queries":Q,"global_positive":positives,"global_negative":Q-positives,
                                    "sha256":digest(path),"generator_binary_sha256":digest(binary)}
    manifest["dataset_sha256"]=digest(OUT/"dataset.txt")
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))

if __name__ == "__main__":
    main()
