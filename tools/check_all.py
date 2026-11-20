#!/usr/bin/env python3
"""Read an original LoL2 DAT folder and run the repository checks.

  check_all.py --data /path/to/LoL2/DAT     # or set $LOL2_DAT
Exit code 0 when all pass. Tools that read DOSBox traces run a self-test instead.
"""
from cli_errors import ReaderArgumentParser, run_cli
import argparse
import os
import subprocess
import sys
from time import monotonic

TOOLS = ["repo_guard", "lol2_mix_parser", "lol2_mix_writer", "lol2_level_writer", "lol2_text_writer", "lol2_source_format", "lol2_disassemble_scripts", "lol2_event_browser",
         "lol2_westwood_hash", "lol2_decompress_westwood", "lol2_westwood_writer",
         "lol2_decompress_sphere", "lol2_cross_level_witnesses", "lol2_entity_field_analyzer", "lol2_l9dr_census",
         "lol2_analyze_disarm_rearm", "lol2_guest_trace_summary", "lol2_aud_decode", "lol2_vqa_v2_decode",
         "lol2_level_report", "lol2_progression", "lol2_plot_branches", "lol2_instance_field", "lol2_level_map", "lol2_level_schematic", "lol2_media_check", "lol2_level_notes", "lol2_text_tables",
         "lol2_hmi_midi", "lol2_hmi_writer", "lol2_xmi_reader", "lol2_item_labels", "rating", "example_images", "lol2_save_native", "lol2_save_inspect", "lol2_save_writer",
         "lol2_cache_seed", "lol2_speech_names", "lol2_loose", "lol2_parse_le", "lol2_inspect", "lol2_numbers", "doc_index", "doc_links", "doc_format_offsets", "modkit"]

QUICK_SKIP = {"lol2_instance_field", "lol2_aud_decode", "lol2_mix_writer", "lol2_vqa_v2_decode"}


def main():
    ap = ReaderArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.environ.get("LOL2_DAT"), required=os.environ.get("LOL2_DAT") is None)
    ap.add_argument("--check", action="store_true", help="run all checks (the default)")
    ap.add_argument("--quick", action="store_true", help="skip the slow corpus checks and list each skip")
    a = ap.parse_args()
    started = monotonic()
    quick_skipped = QUICK_SKIP if a.quick else set()
    here = os.path.dirname(os.path.abspath(__file__))
    failed = []
    for t in TOOLS:
        if t in quick_skipped:
            print(f"SKIP {t}: quick mode")
            continue
        before = monotonic()
        p = subprocess.run([sys.executable, os.path.join(here, t + ".py"), "--check", "--data", a.data],
                           capture_output=True, text=True)
        out = (p.stdout or p.stderr).strip().splitlines()
        print(f"{out[-1] if out else t + ': no output'} [{monotonic() - before:.2f}s]")
        if p.returncode:
            failed.append(t)
    print(f"Total elapsed: {monotonic() - started:.2f}s")
    attempted = len(TOOLS) - len(quick_skipped)
    if failed:
        print(f"{len(failed)} of {attempted} attempted checks FAILED: {', '.join(failed)}")
    elif quick_skipped:
        print(f"{attempted} CHECKS PASSED, {len(quick_skipped)} SKIPPED (quick mode)")
    else:
        print(f"ALL {len(TOOLS)} CHECKS PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
