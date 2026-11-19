#!/usr/bin/env python3
"""Run every LoL2 tool that has a --check against a game DAT folder; one line each.

  check_all.py --data /path/to/LoL2/DAT     # or set $LOL2_DAT
Exit code 0 when all pass. Tools that read DOSBox traces run a self-test instead.
"""
import argparse
import os
import subprocess
import sys

TOOLS = ["repo_guard", "lol2_mix_parser", "lol2_source_format", "lol2_disassemble_scripts", "lol2_westwood_hash", "lol2_decompress_westwood",
         "lol2_decompress_sphere", "lol2_cross_level_witnesses", "lol2_entity_field_analyzer", "lol2_l9dr_census",
         "lol2_analyze_disarm_rearm", "lol2_guest_trace_summary", "lol2_aud_decode", "lol2_vqa_v2_decode",
         "lol2_level_report", "lol2_level_map", "lol2_media_check", "lol2_level_notes", "lol2_text_tables",
         "lol2_hmi_midi", "lol2_item_labels", "rating", "example_images", "lol2_save_native", "lol2_cache_seed", "lol2_speech_names"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.environ.get("LOL2_DAT"), required=os.environ.get("LOL2_DAT") is None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    failed = []
    for t in TOOLS:
        p = subprocess.run([sys.executable, os.path.join(here, t + ".py"), "--check", "--data", a.data],
                           capture_output=True, text=True)
        out = (p.stdout or p.stderr).strip().splitlines()
        print(out[-1] if out else f"{t}: no output")
        if p.returncode:
            failed.append(t)
    print(f"ALL {len(TOOLS)} CHECKS PASSED" if not failed else f"{len(failed)} of {len(TOOLS)} checks FAILED: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
