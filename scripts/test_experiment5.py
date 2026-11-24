import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import experiment5 as e


def profile():
    return {g: [{"name": f"{g}-{i}", "description": "fixture", "values": i}
                for i in range(4)]
            for g in ("dataset_characteristics", "workload_characteristics")}


class StageOneTests(unittest.TestCase):
    def test_shuffle_gcc_reference(self):
        # Generated independently with GCC std::shuffle / mt19937_64(55).
        for expected in ([0], [1,0], [3,0,4,2,1], [2,5,4,0,1,3],
                         [12,13,18,17,1,15,14,0,7,4,2,6,19,5,8,16,3,11,9,10]):
            keys = list(range(len(expected)))
            e.shuffle(keys)
            self.assertEqual(keys, expected)

    def test_profile_contract(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"profile.json"
            good = profile()
            p.write_text(json.dumps(good))
            self.assertEqual(e.validate_profile(p, 16384), good)
            with self.assertRaises(ValueError):
                e.validate_profile(p, 1)
            good["dataset_characteristics"].pop()
            p.write_text(json.dumps(good))
            with self.assertRaises(ValueError):
                e.validate_profile(p, 16384)
            bad = profile()
            bad["workload_characteristics"][0]["values"] = float("nan")
            p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                e.validate_profile(p, 16384)
            bad = profile()
            bad["workload_characteristics"][0]["name"] = bad["dataset_characteristics"][0]["name"]
            p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                e.validate_profile(p, 16384)

    def test_prepare_generate_review_run(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data, query, out = root/"data.txt", root/"query.txt", root/"run"
            data.write_text("a\nb\nc\nd\ne\n", encoding="ascii")
            query.write_text("a\na\nx\n", encoding="ascii")
            e.prepare(argparse.Namespace(dataset_file=data, query_file=query, data=root,
                                         workload="uniform", out=out, allow_unpinned=True,
                                         max_profile_bytes=16384))
            cfg = e.config(out, True)
            self.assertEqual(cfg["query_count"], 3)
            self.assertEqual(list(e.read_keys(out/"partitioned_dataset.txt")), list("daecb"))
            self.assertIn("already shuffled", (out/"prompt_call1.txt").read_text())
            fake = {"stop_reason": "end_turn", "content": [{"type":"text","text":"print('fixture')\n"}],
                    "model": "fixture", "usage": {"input_tokens": 10, "output_tokens": 5}}
            args = argparse.Namespace(out=out, allow_unpinned=True, model=None, call=1)
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY":"test"}), patch.object(e,"urlopen") as api:
                api.return_value.__enter__.return_value.read.return_value = json.dumps(fake)
                e.generate(args)
                api.assert_called_once()
                with self.assertRaises(FileExistsError):
                    e.generate(args)
                api.assert_called_once()
            dest = out/"ai/call_1"
            source = dest/"extract_characteristics.py"
            self.assertFalse((dest/"execution_1").exists())
            run_args = argparse.Namespace(out=out, allow_unpinned=True, call=1,
                                          execution=1, approve_sha="wrong",
                                          query_file=None, timeout=600, image="python:3.12-slim")
            with patch.object(e.subprocess,"run") as proc:
                with self.assertRaises(ValueError):
                    e.run(run_args)
                proc.assert_not_called()
                run_args.approve_sha = e.digest(source)

                def fake_docker(cmd, **kwargs):
                    self.assertIn("--network=none", cmd)
                    self.assertIn("--read-only", cmd)
                    self.assertNotIn("ANTHROPIC_API_KEY", " ".join(cmd))
                    (dest/"execution_1/characteristics.json").write_text(json.dumps(profile()))

                proc.side_effect = fake_docker
                e.run(run_args)
                proc.assert_called_once()
            meta = json.loads((dest/"execution_1.json").read_text())
            self.assertEqual(meta["status"], "schema_validated")
            self.assertEqual(meta["profile_sha256"], e.digest(dest/"execution_1/characteristics.json"))


if __name__ == "__main__":
    unittest.main()
