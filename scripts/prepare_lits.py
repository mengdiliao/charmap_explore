#!/usr/bin/env python3
"""Import an author's LITS text dataset and run the published LITS+ YCSB-C routines.
The published 2024 original real-data query generator has not been located.
LITS+ is the later author implementation, not an exact 2024 reproduction.
"""
import argparse, hashlib, json, os, shutil, subprocess, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PIN="ce211d7c0aa15f833eaba5e342951ed49c3b81ba"
BASE="https://raw.githubusercontent.com/schencoding/lits/"+PIN+"/LITS+/LIT+/microbench/"
NAMES={"reddit":(26000000,3,26),"geonames":(7000000,2,152),"us_addresses":(34000000,4,133)}

def sha(p):
    with p.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("dataset",choices=NAMES)
    a.add_argument("source",type=Path,help="Author's extracted one-key-per-line text file")
    a.add_argument("--acknowledge-litsplus",action="store_true",help="Use later official generator, not exact LITS 2024 workload")
    args=a.parse_args()
    if not args.acknowledge_litsplus:
        a.error("LITS+ is not the exact 2024 generator; pass --acknowledge-litsplus explicitly.")
    out=ROOT/"data"/args.dataset
    out.mkdir(parents=True,exist_ok=True)
    # Do not clean, deduplicate, sort or sample the imported stored keys.
    target=out/"dataset.txt"
    count=0
    _, lo, hi=NAMES[args.dataset]
    with args.source.open("rb") as f:
        for line in f:
            key=line.removesuffix(b"\n").removesuffix(b"\r")
            if not (lo<=len(key)<=hi and key.isascii() and b"\0" not in key and b"\r" not in key):
                raise ValueError(f"Unexpected key at row {count+1}: confirm this is the author's prepared text file")
            count+=1
    approx=NAMES[args.dataset][0]
    if not 0.8*approx <= count <= 1.2*approx:
        raise ValueError(f"{count} rows differs substantially from paper's approximate {approx}")
    if args.source.resolve()!=target.resolve():
        shutil.copyfile(args.source,target)
    work=ROOT/".upstream"/"litsplus"
    work.mkdir(parents=True,exist_ok=True)
    for name in ("bench.cpp","utils.hpp"):
        p=work/name
        if not p.exists():
            with urllib.request.urlopen(BASE+name,timeout=120) as f: p.write_bytes(f.read())
    src=(work/"bench.cpp").read_text()
    # Reuse the exact official query-building functions, replacing only index
    # dependencies with a minimal Entry adapter and exporting the generated queue.
    begin=src.index("typedef enum")
    end=src.index("void runBenchmarkLITSP")
    body=src[begin:end]
    pre=r'''#include <algorithm>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#include <cstdint>
#include <cmath>
#include "utils.hpp"
using namespace std;
#define COUT_VAR(v) (void)(v)
struct Entry {
    std::string s;
    static Entry* create(const std::string& s, int) {return new Entry{s};}
    const char* key() const {return s.c_str();}
};
'''
    post=r'''
int main(int argc,char** argv) {
    if(argc!=4) return 2;
    // Read same keys as author's readKeys. Normalize CRLF as line delimiters,
    // never trim spaces or change the key bytes.
    std::ifstream in(argv[1]);
    if(!in) return 3;
    std::string line;
    while(std::getline(in,line)) {
        if(!line.empty() && line.back()=='\r') line.pop_back();
        all_records.push_back(Entry::create(line,1));
    }
    basicPartition(YCSB_C); // original author code sorts the temporary rank list
    if(std::string(argv[2])=="zipf") generateQueriesZipf_YCSB_C();
    else generateQueries(YCSB_C);
    std::ofstream out(argv[3], std::ios::binary);
    if(!out) return 4;
    for(const auto& q:query_queue) {
        if(q.first!=QueryType::Lookup) return 5;
        out<<q.second<<'\n';
    }
    return !out;
}
'''
    (work/"export.cpp").write_text(pre+body+post)
    subprocess.run([os.environ.get("CXX","g++"),"-std=c++17","-O2","export.cpp","-o","export"],cwd=work,check=True)
    manifest={"upstream_commit":PIN,"source":str(args.source),"dataset_sha256":sha(target),"stored_rows":count,
              "workload_provenance":"LITS+ official generator, not identical to 2024 LITS","workloads":{}}
    for mode in ("uniform_cycle","zipf"):
        path=out/("queries_litsplus_"+mode+".txt")
        subprocess.run([str(work/"export"),str(target),mode,str(path)],check=True)
        with path.open("rb") as f: q=sum(1 for _ in f)
        if q!=20000000: raise ValueError(f"Unexpected query count {q}")
        manifest["workloads"][mode]={"queries":q,"global_positive":q,"global_negative":0,"sha256":sha(path)}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__": main()
