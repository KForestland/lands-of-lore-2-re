# How we rate this repository

The README and [STATUS](STATUS.md) carry four counted lines instead of a
single percentage. `python3 tools/rating.py --data <DAT>` prints them from
your copy of the game and the pages; `--check` (part of `check_all.py`)
fails when the README or STATUS lines differ from the counts.

## The four lines

**Files read.** How many files in the game's `DAT` folder a reader in this
repository accounts for to the last byte, by count and by size. For a MIX
archive that means the body-size field matches the file and the entries
tile the body from offset 0 to the end with no gap or overlap.
`AUTOPLAY.WAV` counts when its RIFF chunks tile the file, and `SETUP.EXE`
counts when its NE tables, segments and resources tile the file, with
zero bytes between objects counted as padding (`tools/lol2_loose.py`).
Its first 41,584 bytes are a separate DOS program (290 relocations); it
is counted by the length its MZ header gives, and its content is not read. What opens either file stays open. It
does **not** mean that every entry inside is decoded or understood; the
[STATUS](STATUS.md) table says how far each format is read. Only the `DAT` folder is counted; files the game writes while it runs
(caches, saves) change the count on a copy that has been played.

**Rules traced.** How many statements on the current pages carry the
evidence label CONFIRMED (backed by a program address or a file offset
that was checked) and how many carry UNCONFIRMED (a reading, with the test
that would settle it). Older pages use PROVEN and UNKNOWN for the same two labels, and they are counted with them. Pages marked as history are left out. It counts
labels, not importance: one CONFIRMED may cover a whole table and one
UNCONFIRMED a single byte. It does **not** claim that unlabelled text is
wrong or that labelled text is complete.

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

**Open questions.** The state words of the At-a-glance table in
[OPEN_QUESTIONS.md](OPEN_QUESTIONS.md): answered, mostly answered, partly
answered. A question may be answered for one setup only; the table says so.

## What the rating does not say

It is not a measure of completeness and cannot be turned into one: the
four lines count different things and none of them has a known total for
"everything the game does". Older notes in this repository that gave a
percentage are kept as history and are marked so.
