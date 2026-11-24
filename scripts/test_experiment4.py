"""Offline regression tests for Experiment 4 (stdlib unittest)."""
import argparse
import csv
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_generate_arms_and_validate(self):
        dest = self.root/"generated"
        e4.prepare(self.args("zipf",dest))
        combos = [[0,1,2,i] for i in range(3,11)] + [[1,2],[1,2,3],[1,2,3,4,5],[1,2,3,4,5,6]]
        raw = {"model":"fixture-model","stop_reason":"end_turn",
               "usage":{"input_tokens":100,"output_tokens":200},
               "content":[{"type":"text","text":json.dumps({"candidates":[
                   {"positions":p,"reason":"Fixture"} for p in combos]})}]}
        requests = []
        def fake(req, timeout):
            requests.append(json.loads(req.data))
            return io.BytesIO(json.dumps(raw).encode())
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY":"fixture-key"}), patch.object(e4,"urlopen",side_effect=fake):
            for arm in ("profiled","control"):
                args = argparse.Namespace(out=dest,arm=arm,call=1,model="fixture-model",allow_unpinned=True)
                e4.generate(args)
                run = dest/"ai"/arm/"call_1"
                self.assertEqual(len(json.loads((run/"validated_candidates.json").read_text())["candidates"]),12)
                meta = json.loads((run/"generation.json").read_text())
                self.assertEqual(meta["returned_model"],"fixture-model")
                self.assertEqual(meta["usage"]["input_tokens"],100)
                self.assertEqual(meta["response_sha256"],e4.digest(run/"response.json"))
                self.assertNotIn("fixture-key",(run/"request.json").read_text())
                with self.assertRaises(FileExistsError):
                    e4.generate(args)
            self.assertEqual(len(requests),2)
            for body,arm in zip(requests,("profiled","control")):
                self.assertEqual(body["messages"][0]["content"],(dest/e4.ARMS[arm]).read_text())
            (dest/"prompt.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError,"Prepared artifact changed"):
                e4.generate(argparse.Namespace(out=dest,arm="profiled",call=2,model=None,allow_unpinned=True))
            self.assertEqual(len(requests),2)

    def test_profiled_only_evaluation(self):
        dest = self.root/"eval_run"
        e4.prepare(self.args("zipf",dest))
        combos = [[0,1,2,i] for i in range(3,11)] + [[1,2],[1,2,3],[1,2,3,4,5],[1,2,3,4,5,6]]
        response = {"candidates":[{"positions":p,"reason":"Fixture"} for p in combos]}
        raw = {"model":"fixture","stop_reason":"end_turn","usage":{},
               "content":[{"type":"text","text":json.dumps(response)}]}
        with patch.dict("os.environ",{"ANTHROPIC_API_KEY":"fixture"}), patch.object(
                e4,"urlopen",return_value=io.BytesIO(json.dumps(raw).encode())):
            e4.generate(argparse.Namespace(out=dest,arm="profiled",call=1,model="fixture",allow_unpinned=True))
        cfg = e4.prepared_config(dest)
        old = self.root/"historical"
        old.mkdir()
        e4.save(old/"config.json",{
            "partition_size":8000,"budget":512,"partition_seed":55,
            "input_sha256":{"dataset.txt":e4.digest(self.data),"queries_zipf.txt":e4.digest(self.zipf)}
        })
        e4.save(old/"runtime.json",{"hash_version":cfg["hash_version"]})
        fields = ["workload","group","proposal_id","positions","reason","partition_size","budget_bytes",
                  "queries","false_negatives","pruning_pct","dataset_rows","partitions","global_positive","retained"]
        rows = [
            ["zipf","AI","A1_01","0;1;-5;-1","old",8000,512,10,0,20,7,1,8,8],
            ["zipf","AI","A1_02","0;2","old",8000,512,10,0,10,7,1,8,9],
            ["zipf","Random","R1_01","0;3","",8000,512,10,0,99,7,1,8,8],
            ["uniform","AI","A1_03","0;4","",8000,512,10,0,99,7,1,8,8],
        ]
        with (old/"proposal_results.csv").open("w",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(fields)
            writer.writerows(rows)
        args=argparse.Namespace(out=dest,call=1,historical_run=old,dataset_file=None,
                                query_file=None,eval_out=None,heap="4g")
        frozen=e4.frozen_candidates(dest,cfg,1,old)
        self.assertEqual(frozen["designs"][0]["proposal_id"],"A1_01")
        self.assertEqual(len(frozen["designs"]),13)
        def mock_evaluator(command,cwd,check):
            self.assertIn("-Pworkload=zipf",command)
            self.assertIn("-PqueryFile="+str(self.zipf.resolve()),command)
            out=Path(next(x.split("=",1)[1] for x in command if x.startswith("-PoutputDir=")))
            out.mkdir()
            result_fields=["workload","algorithm","positions","partition_size","budget_bytes","queries",
                           "false_negatives","pruning_pct","dataset_rows","partitions","global_positive","retained"]
            with (out/"results.csv").open("w",newline="") as f:
                writer=csv.writer(f)
                writer.writerow(result_fields)
                writer.writerows([["zipf","Oracle","",8000,512,10,0,20,7,1,8,8],
                                  ["zipf","OptimizedBloom","",8000,512,10,0,10,7,1,8,9]])
                for d in frozen["designs"]:
                    writer.writerow(["zipf",d["algorithm"],";".join(map(str,d["positions"])),
                                     8000,512,10,0,20,7,1,8,8])
        with patch.object(e4.subprocess,"run",side_effect=mock_evaluator):
            e4.evaluate(args)
        result=dest/"evaluation/profiled/call_1"
        with (result/"results.csv").open(newline="") as f:
            report=list(csv.DictReader(f))
        self.assertEqual(len(report),15)
        self.assertEqual(e4.Counter(r["group"] for r in report),
                         {"Oracle":1,"OptimizedBloom":1,"Experiment3BestAI":1,"Experiment4ProfiledAI":12})
        self.assertFalse((dest/"ai/control").exists())
        self.assertEqual(json.loads((result/"summary.json").read_text())["experiment4_candidate_count"],12)
        # The input provenance check must reject changed query data before running Gradle.
        self.zipf.write_text("different.com\n")
        with self.assertRaisesRegex(ValueError,"Input differs"):
            e4.evaluate(args)

    def test_bucket_boundaries_and_ties(self):
        keys = e4.Counter({4:1,7:1,8:1,11:1,12:1,15:1,16:1,19:1,20:1,23:1,24:1,31:1,32:1,124:1})
        self.assertEqual([v["count"] for v in e4.lengths(keys,4).values()],[2]*7)
        self.assertEqual(e4.length_summary(e4.Counter({4:1,8:1}))["median"],6)
        self.assertEqual(e4.top_entries(e4.Counter({"b":1,"a":1}),1,2,"key")[0]["key"],"a")


if __name__ == "__main__":
    unittest.main()
