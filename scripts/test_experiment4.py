"""Offline regression tests for Experiment 4 (stdlib unittest)."""
import argparse
import json
from pathlib import Path
import tempfile
import unittest

import experiment4 as e4

class Experiment4Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
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
        self.assertEqual([e4.category(k) for k in self.keys],
                         ["ipv4","non_www_single_dot","www_simple","non_www_multiple_dots",
                          "www_complex","non_www_multiple_dots","other"])
        for key, expected in [
            ("example.co.uk","non_www_multiple_dots"),("blog.example.com","non_www_multiple_dots"),
            ("www.example.co.uk","www_complex"),("www.blog.example.com","www_complex"),
            ("www.com","www_simple"),("co.uk","non_www_single_dot"),
            ("999.2.3.4","other"),("192.0.2.1","ipv4"),
            ("WWW.Example.COM","non_www_multiple_dots"),("www.example.com.","other"),
            ("foo.www.example.com","non_www_multiple_dots"),("localhost","other"),
            ("www..example.com","other"),("https://example.com","other"),
            ("a_b.com","other"),("2001:db8::1","other")]:
            self.assertEqual(e4.category(key),expected,key)

    def test_profile_counts(self):
        keys, lens, dp = e4.dataset_profile(self.data)
        self.assertEqual(sum(v["count"] for v in dp["category_distribution"].values()),7)
        self.assertEqual(dp["category_distribution"]["non_www_single_dot"]["count"],1)
        self.assertEqual(dp["category_distribution"]["non_www_multiple_dots"]["count"],2)
        self.assertEqual([row["prefix"] for row in dp["top5_prefixes"][:2]],["exa","www"])
        self.assertEqual([row["count"] for row in dp["top5_prefixes"][:2]],[2,2])
        self.assertEqual(dp["top5_suffixes"][0]["suffix"],"com")
        self.assertEqual(sum(v["count"] for v in e4.lengths(lens,4).values()),7)
        q = e4.Counter({"example.com":7,"missing.com":2,"odd/path":1})
        ql, wp = e4.workload_profile(q,keys)
        self.assertEqual(wp["global_positive_pct"],80)
        self.assertEqual(wp["positive_rate_by_category"]["non_www_single_dot"]["pct"],77.7778)
        self.assertIsNone(wp["positive_rate_by_category"]["ipv4"]["pct"])
        self.assertEqual(wp["top10_frequent_keys"][0],
                         {"key":"example.com","count":7,"pct":70.0,"positive":True})
        self.assertEqual(sum(v["count"] for v in e4.lengths(ql,4).values()),10)

    def args(self, name, dest):
        return argparse.Namespace(dataset_file=self.data, data=self.root,
            query_file=self.uniform if name=="uniform" else self.zipf,
            workload=name, examples=self.examples, out=dest,
            allow_unpinned=True,
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
            self.assertEqual(cfg["query_occurrences"],4 if name=="uniform" else 10)
            self.assertEqual(cfg["evaluation_scope"],"full_selected_workload_in_sample")
            self.assertEqual(cfg["category_version"],"raw-www-dot-count-v1")
            self.assertEqual(set(p.name for p in dest.iterdir()), {
                "dataset_profile.json","workload_profile.json","prompt_profile.json",
                "examples.json","prompt.md","prompt_control.md","config.json"})
            self.assertIn("full workload has",prompt)
            self.assertIn("non_www_multiple_dots",prompt)
            self.assertNotIn("non_www_multiple_dots",control)
            self.assertNotIn("training",prompt)
            self.assertNotIn("public suffix",prompt)
            self.assertEqual(sum(row["count"] for row in json.loads(
                (dest/"workload_profile.json").read_text())["category_distribution"].values()),
                cfg["query_occurrences"])
            with self.assertRaises(FileExistsError):
                e4.prepare(args)
        self.assertEqual((self.root/"uniform/dataset_profile.json").read_text(),
                         (self.root/"zipf/dataset_profile.json").read_text())

    def test_full_occurrences_and_empty_workload(self):
        src = self.root/"repeat.txt"
        src.write_text("example.com\n"*100+"new.com\n"*100)
        before = e4.digest(src)
        self.assertEqual(e4.query_frequencies(src),{"example.com":100,"new.com":100})
        self.assertEqual(e4.digest(src),before)
        empty = self.root/"empty.txt"
        empty.touch()
        with self.assertRaisesRegex(ValueError,"Empty workload"):
            e4.query_frequencies(empty)

    def test_bucket_boundaries_and_ties(self):
        keys = e4.Counter({4:1,7:1,8:1,11:1,12:1,15:1,16:1,19:1,20:1,23:1,24:1,31:1,32:1,124:1})
        self.assertEqual([v["count"] for v in e4.lengths(keys,4).values()],[2]*7)
        self.assertEqual(e4.length_summary(e4.Counter({4:1,8:1}))["median"],6)
        self.assertEqual(e4.top_entries(e4.Counter({"b":1,"a":1}),1,2,"key")[0]["key"],"a")


if __name__ == "__main__":
    unittest.main()
