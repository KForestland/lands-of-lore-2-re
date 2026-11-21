# How we rate this repository

The README and [STATUS](STATUS.md) carry five counted lines instead of a
single percentage. `python3 tools/rating.py --data <DAT>` prints them from
your copy of the game and the pages; `--check` (part of `check_all.py`)
fails when the README or STATUS lines differ from the counts.

## The five lines

**Files read.** How many files in the game's `DAT` folder a reader in this
repository accounts for to the last byte, by count and by size. For a MIX
archive that means the body-size field matches the file and the entries
tile the body from offset 0 to the end with no gap or overlap.
`AUTOPLAY.WAV` counts when its RIFF chunks tile the file, and `SETUP.EXE`
counts when its NE tables, segments and resources tile the file, with
zero bytes between objects counted as padding (`tools/lol2_loose.py`).
Its first 41,584 bytes are a separate DOS program (290 relocations); it
is counted by the length its MZ header gives, and its content is not read. Which part of the game reads these two files is still unknown. It
does **not** mean that every entry inside is decoded or understood; the
[STATUS](STATUS.md) table says how far each format is read. Only files directly in the `DAT` folder are counted, not its subfolders.
A file the game writes there while it runs (a cache or a save) is counted
like any other: it adds to the total, and it counts as read only when it
is a MIX archive whose entries tile it or a loose file `lol2_loose.py`
accounts for. So a copy that has been played can show a larger total.

**Rules traced.** How many statements on the current pages carry the
evidence label CONFIRMED (backed by a program address or a file offset
that was checked) and how many carry UNCONFIRMED (a reading, with the test
that would settle it). Older pages use PROVEN and UNKNOWN for the same two labels, and they are counted with them. Pages marked as history are left out. The glossary defines the label words; its labels are not counted. It counts
labels, not importance: one CONFIRMED may cover a whole table and one
UNCONFIRMED a single byte. It does **not** claim that unlabelled text is
wrong or that labelled text is complete.
Two samples of 30 CONFIRMED statements, taken by different rules, were re-derived from the bytes ([samples](CONFIRMED_SAMPLE.md)). First sample: 25 held, 3 held in part, 2 wrong (both corrected). Second sample: 21 held, 8 held in part, 1 overstated (corrected). Four statements first picked for both lists were replaced in the second, so 60 different statements were checked.

**Seen in the running game.** Of the probes on
[NEEDS_A_RUNNING_GAME.md](NEEDS_A_RUNNING_GAME.md) (tests that the files
and the program text cannot settle alone), how many were answered by
running the original game. It counts probe headings under "Answered
probes" and "Remaining probes", not numbered questions: a question can
have more than one probe, and a probe need not belong to a numbered
question. Each answer holds for the setup it names (one
display, one renderer, one save). Most documented facts were never
observed in a running game; they are proved from the program and the files
instead, and this line does **not** count them.

The same line says how many answered probes rest on edited saves only.
An edited save is a copy of a game-written save with a few bytes
changed by hand; [edited saves](EDITED_SAVES.md) lists each such run.
An answered probe counts here when its section says "edited-save run"
and none of its bold labels says "answered" without "edited-save". A
label like that marks a run on a save the game wrote itself. A probe
that is still open is not counted, even when an edited-save run added
evidence to it. Probes listed under "Probes not yet run" are not counted
in either number.

**Open questions.** The state words of the At-a-glance table in
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md): answered, mostly answered, partly
answered. *Answered*: nothing is left to settle from the files or the program. *Mostly answered*: the main question is settled; named details remain. *Partly answered*: part is settled; the main point is open. A row that says 'answered for' a setup (one renderer, one device) counts as answered for that setup only.

**Page facts.** The scanner counts offsets, names and numbers in passages
marked as proved, in measured examples, and at the registry's explicit anchors.
Registered witnesses independently read the named original files. Run
`python3 tools/page_facts.py --check --data DAT` to compare those values or
`python3 tools/page_facts.py --list` to see the prose-only claims and their reason.
The prose inventory flags changes for review. Its fingerprints do not establish
what the bytes say. After verifying a documentation change, review the output
of `python3 tools/page_facts.py --inventory` before recording the revised inventory.

## What the rating does not say

It is not a measure of completeness and cannot be turned into one: the
five lines count different things and none of them has a known total for
"everything the game does". Older notes in this repository that gave a
percentage are kept as history and are marked so.
