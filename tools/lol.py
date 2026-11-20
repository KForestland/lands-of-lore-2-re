#!/usr/bin/env python3
"""Find and run an original Lands of Lore file tool."""
from argparse import RawDescriptionHelpFormatter
from pathlib import Path
from importlib import import_module
from runpy import run_path
import sys

import cli_errors
from cli_errors import ReaderArgumentParser, run_cli

JOBS = {
    "level": ("level_viewer.py", (), "Look at an interactive level plan"),
    "text": ("lol2_inspect.py", (), "Read original game text"),
    "translate": ("translate.py", (), "Export, build and verify translations"),
    "music": ("lol2_hmi_midi.py", (), "Inspect original game music (convert HMI to MIDI)"),
    "movie": ("media_convert.py", (), "Convert a movie to MKV"),
    "sound": ("media_convert.py", (), "Convert a sound to WAV"),
    "save": ("save_edit.py", (), "Edit a copy of a saved game"),
    "patch": ("patch.py", (), "Make or apply a patch and its undo"),
    "mod": ("modkit.py", (), "Unpack or build an editable workspace"),
}

JOB_HANDLERS = {
    "text": ("text_job", ()),
    "movie": ("main", ("movie",)),
    "sound": ("main", ("sound",)),
}


def main():
    menu = "\n".join(f"  {name:7} {spec[2]}" for name, spec in JOBS.items())
    parser = ReaderArgumentParser(
        prog="lol.py",
        description="Choose a job for your copy of the original game.",
        usage="python tools/lol.py JOB [OPTIONS]",
        epilog="Jobs\n" + menu + "\n\nUse python tools/lol.py JOB --help for the job's options.",
        formatter_class=RawDescriptionHelpFormatter,
    )
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        parser.print_help()
        return 0
    if args[0] not in JOBS:
        parser.error(f"Unknown job {args[0]}. Run python tools/lol.py to see the choices.")
    job, options = args[0], args[1:]
    script, prefix, label = JOBS[job]
    if not options or options[-1] in ("-h", "--help"):
        print(f"{label}.", flush=True)
    program = Path(__file__).resolve().with_name(script)
    old_argv, old_name = sys.argv, cli_errors.JOB_NAME
    try:
        sys.argv = [str(program), *prefix, *(options or ["--help"])]
        cli_errors.JOB_NAME = f"lol.py {job}"
        handler = JOB_HANDLERS.get(job)
        if handler:
            name, arguments = handler
            return run_cli(getattr(import_module(program.stem), name), *arguments)
        run_path(str(program), run_name="__main__")
    finally:
        sys.argv, cli_errors.JOB_NAME = old_argv, old_name


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
