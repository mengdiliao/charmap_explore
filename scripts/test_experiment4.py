"""Offline regression tests for Experiment 4 (stdlib unittest)."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

import experiment4 as e4

PSL = """// ===BEGIN ICANN DOMAINS===
com
uk
co.uk
ck
*.ck
!www.ck
// ===END ICANN DOMAINS===
// ===BEGIN PRIVATE DOMAINS===
blogspot.com
// ===END PRIVATE DOMAINS===
"""


class Experiment4Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.psl_path = self.root/"psl.dat"
        self.psl_path.write_text(PSL)
        self.psl = e4.PublicSuffixList(self.psl_path)
        self.keys = ["1.2.3.4","example.com","www.example.com","blog.example.com",
                     "www.blog.example.com","example.co.uk","odd/path"]
        self.data = self.root/"dataset.txt"
        self.data.write_text("\n".join(self.keys)+"\n",encoding="ascii")
        self.examples = self.root/"examples.json"
        self.examples.write_text(json.dumps({"plain":self.keys[1]}))
        self.uniform = self.root/"uniform.txt"
        self.zipf = self.root/"zipf.txt"
        self.uniform.write_text("example.com\nwww.example.com\n1.2.3.4\nnew.com\n")
        self.zipf.write_text("example.com\n"*7+"missing.com\n"*2+"odd/path\n")

    def test_category_partition(self):
        self.assertEqual([self.psl.category(k) for k in self.keys],
                         ["ipv4","plain_domain","www_domain","subdomain_without_www",
                          "subdomain_with_www","plain_domain","other"])
        for key, expected in [
            ("example.co.uk","plain_domain"),("www.example.co.uk","www_domain"),
            ("www.blog.example.co.uk","subdomain_with_www"),
            ("a.b.ck","plain_domain"),("www.ck","plain_domain"),
            ("www.www.ck","www_domain"),("blog.blogspot.com","subdomain_without_www"),
            ("www.com","plain_domain"),("999.2.3.4","other"),
            ("WWW.Example.COM.","www_domain"),("co.uk","other"),
            ("foo.www.example.com","subdomain_without_www")]:
            self.assertEqual(self.psl.category(key),expected,key)

    def test_profile_counts(self):
        keys, lens, dp = e4.dataset_profile(self.data,self.psl)
        self.assertEqual(sum(v["count"] for v in dp["category_distribution"].values()),7)
        self.assertEqual(dp["category_distribution"]["plain_domain"]["count"],2)
        self.assertEqual(dp["top5_prefixes"][0]["prefix"],"www")
        self.assertEqual(dp["top5_suffixes"][0]["suffix"],"com")
        self.assertEqual(sum(v["count"] for v in e4.lengths(lens,4).values()),7)
        q = e4.Counter({"example.com":7,"missing.com":2,"odd/path":1})
        ql, wp = e4.workload_profile(q,keys,self.psl)
        self.assertEqual(wp["global_positive_pct"],80)
        self.assertEqual(wp["positive_rate_by_category"]["plain_domain"]["pct"],77.7778)
        self.assertIsNone(wp["positive_rate_by_category"]["ipv4"]["pct"])
        self.assertEqual(wp["top10_frequent_keys"][0],
                         {"key":"example.com","count":7,"pct":70.0,"positive":True})
        self.assertEqual(sum(v["count"] for v in e4.lengths(ql,4).values()),10)

    def args(self, name, dest, fraction=0):
        return argparse.Namespace(dataset_file=self.data, data=self.root,
            query_file=self.uniform if name=="uniform" else self.zipf,
            workload=name, psl=self.psl_path, examples=self.examples, out=dest,
            allow_unpinned=True, holdout_fraction=fraction, split_seed=155,
            first_length_bucket=4)

    def test_independent_prompts_and_manifest(self):
        for name in ("uniform","zipf"):
            dest = self.root/name
            args = self.args(name,dest)
            e4.prepare(args)
            cfg = json.loads((dest/"config.json").read_text())
            self.assertEqual(cfg["workload"],name)
            self.assertFalse(cfg["official_input_hashes_match"])
            for filename,sha in cfg["output_sha256"].items():
                self.assertEqual(e4.digest(dest/filename),sha)
            profile = json.loads((dest/"prompt_profile.json").read_text())
            prompt = (dest/"prompt.md").read_text()
            control = (dest/"prompt_control.md").read_text()
            self.assertIn("Simple statistical profile",prompt)
            self.assertNotIn("Simple statistical profile",control)
            self.assertIn("exactly 12 unique",prompt)
            self.assertEqual(profile["workload"]["top10_frequent_keys"][0]["pct"],
                             25.0 if name=="uniform" else 70.0)
            self.assertNotIn("missing.com",control)
            if name=="uniform":
                self.assertNotIn("missing.com",prompt)
            self.assertEqual((dest/"queries_holdout.txt").read_text(),"")
            with self.assertRaises(FileExistsError):
                e4.prepare(args)
        self.assertEqual((self.root/"uniform/dataset_profile.json").read_text(),
                         (self.root/"zipf/dataset_profile.json").read_text())

    def test_occurrence_split_reproducible(self):
        src = self.root/"repeat.txt"
        src.write_text("example.com\n"*100+"new.com\n"*100)
        a,b = self.root/"a",self.root/"b"
        for dest in (a,b):
            dest.mkdir()
            freq,n = e4.split_queries(src,dest,.2,155)
            self.assertEqual(sum(freq.values())+n,200)
            self.assertGreater(n,0)
            self.assertGreater(freq["example.com"],0)
        for name in ("queries_train.txt","queries_holdout.txt"):
            self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())

    def test_bucket_boundaries_and_ties(self):
        keys = e4.Counter({4:1,7:1,8:1,11:1,12:1,15:1,16:1,19:1,20:1,23:1,24:1,31:1,32:1,124:1})
        self.assertEqual([v["count"] for v in e4.lengths(keys,4).values()],[2]*7)
        self.assertEqual(e4.length_summary(e4.Counter({4:1,8:1}))["median"],6)
        self.assertEqual(e4.top_entries(e4.Counter({"b":1,"a":1}),1,2,"key")[0]["key"],"a")


if __name__ == "__main__":
    unittest.main()
