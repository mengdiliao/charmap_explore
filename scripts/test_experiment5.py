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
            self.assertEqual(cfg["dataset_count"], 5)
            self.assertEqual(cfg["input_layout"], e.INPUT_LAYOUT)
            self.assertEqual(set(p.name for p in out.iterdir()), {"config.json", "prompt_call1.txt"})
            self.assertEqual(data.read_text(), "a\nb\nc\nd\ne\n")
            self.assertIn("original file order", (out/"prompt_call1.txt").read_text())
            prompt = (out/"prompt_call1.txt").read_text()
            self.assertIn("No precomputed partition layout is provided or required", prompt)
            self.assertIn("label the results as estimates", prompt)
            for forbidden in ("shuffle", "mt19937", "libstdc++", "partition_seed", "seed: 55"):
                self.assertNotIn(forbidden, prompt.lower())
            # Old prepared runs must not silently use the revised input semantics.
            old_cfg = dict(cfg)
            old_cfg.pop("input_layout")
            e.save(out/"config.json", old_cfg)
            with self.assertRaisesRegex(ValueError, "Old shuffled-input run"):
                e.config(out, True)
            e.save(out/"config.json", cfg)
            fake = {"stop_reason": "end_turn", "content": [{"type":"text","text":"print('fixture')\n"}],
                    "model": "fixture", "usage": {"input_tokens": 10, "output_tokens": 5}}
            args = argparse.Namespace(out=out, allow_unpinned=True, model=None, call=1)
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY":"test"}), patch.object(e,"urlopen") as api:
                api.return_value.__enter__.return_value.read.return_value = json.dumps(fake)
                data.write_text("changed\n")
                with self.assertRaisesRegex(ValueError, "Input changed: dataset"):
                    e.generate(args)
                api.assert_not_called()
                data.write_text("a\nb\nc\nd\ne\n")
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
                                          dataset_file=None, query_file=None, timeout=600, image="python:3.12-slim")
            with patch.object(e.subprocess,"run") as proc:
                with self.assertRaises(ValueError):
                    e.run(run_args)
                proc.assert_not_called()
                run_args.approve_sha = e.digest(source)
                data.write_text("changed\n")
                with self.assertRaisesRegex(ValueError, "Input changed: dataset"):
                    e.run(run_args)
                proc.assert_not_called()
                data.write_text("a\nb\nc\nd\ne\n")

                def fake_docker(cmd, **kwargs):
                    self.assertIn("--network=none", cmd)
                    self.assertIn("--read-only", cmd)
                    self.assertIn(f"type=bind,src={data.resolve()},dst=/dataset.txt,readonly", cmd)
                    self.assertIn(f"type=bind,src={query.resolve()},dst=/queries.txt,readonly", cmd)
                    self.assertNotIn("partitioned_dataset.txt", " ".join(cmd))
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
