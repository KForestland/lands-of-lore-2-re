# Per-level script notes

These notes describe the 15 original DOS level archives in game order. The
numeric archive IDs have gaps. Each page in this folder is a summary: counts,
the matcher table and a few traced command sites. One worked excerpt shows the
per-group lines ([L1_DC](L1_DC.excerpt.md)).

The full per-group lines and the two JSON Lines indexes described below are a
transformed copy of the game's scripts, so they are not in the repository. Make
them from your own game files:

```bash
python3 tools/lol2_level_notes.py --data /path/to/DAT --out /path/outside/the/repo        # all levels
python3 tools/lol2_level_notes.py --data /path/to/DAT --out /path/outside/the/repo L1_DC  # one level
```

A large index continues in `-2.jsonl` and subsequent numbered parts.
The rows can be read one at a time with `json.loads(line)`. All offsets and
identifiers in JSON are integers in decimal. MIX offsets refer to the level
archive named by the filename. Instruction addresses use the 1.30
[executable convention](../../lol2-executable-tables.md).

## Rows

- `<level>.groups.jsonl` has one group per line with `stream`, its stream-relative
  `group` ID, absolute MIX `offset`, `triggers` (direct event MIX offsets), and
  `commands`. Each command array has eight fields in order: absolute MIX
  offset, opcode, command byte +1, command u16 +2, target or null, one-line
  effect, analysis VA and evidence status. A target is `[scope, ID, selector VA]`.
  A null ID can denote the player or the runtime-bound object. Level transitions
  and item grants record the destination or item definition as the primary target.
- `<level>.events.jsonl` has `placement`, `list`, and `event` rows ordered by
  type. Placement IDs are zero-based within the named actor, prop, control or
  movable table. `list_offset` joins to a list row's `offset`. A region list
  instead carries its `descriptors`, which are zero-based in the descriptor
  table. Each list keeps its event offsets in record order, including predicate
  trailers. List and event offsets are absolute MIX addresses.
- An event row has its number `kind`, a native `matcher` VA if known, decoded
  `operands`, and a `[stream, group]` join if its record kind carries one.
  `predicate` is `[index, trailer MIX offset, predicate entry MIX offset]` when
  a trailer follows. On region kinds 11 and 12, `selector` is the u16 at +4.
  Region-kind 15's byte +7 chooses the source of the comparison operand.

## Evidence

**CONFIRMED.** The group runner `0x646EC` is the common framing and queue
entry. A direct reference uses the word at event +2 and the stream for that
kind, as shown by `0xAD89E–0xAD8AD` and `0xF2E98–0xF2EAC`. The
[native event matchers](../../lol2-script-events.md#event-records) establish
operand widths, comparisons and predicate checks. The [opcode reference](../../lol2-script-opcodes.md)
establishes operand reads and dispatch. The [geometry header](../../lol2-level-script-format.md#header-fields-proven-by-consistent-reading-on-all-15-levels)
holds the placement and event-table offsets. An event can be shared by several
lists or placements. The event index stores its absolute offset once.

Movie names next to opcode 21 are read through the original scene pointer
table at `LOLG.DAT+0x1CF58C`. See the [scene player](../../lol2-movie-scenes.md).

**CONFIRMED** on a command concerns what its cited arm does when admitted.
It does not assert that the guard passes in a particular game state. A confirmed
matcher identifies the native comparison. It does not establish every gameplay
producer of the event ID. **UNCONFIRMED** rows show the available dispatch or
file evidence and leave the underlying effect open. The indexes contain IDs,
operand values and newly written descriptions. They contain no dialogue or
verbatim command streams.

For example, join `group=1194`, `stream=0` in `L1_DC.groups.jsonl` to its
trigger at `L1_DC.MIX+0x6FDC4B`. Its kind-12 row targets L1 region 1190
and carries predicate 179. The group's command at `+0x6FD59F` requests
level 3, arrival 1. That operand split is read at `0xD8797–0xD87C5`.

```bash
python3 tools/lol2_level_notes.py --data DAT --out /tmp/level-notes L1_DC
python3 tools/lol2_level_notes.py --data DAT --check
```

In the Markdown, the first offset on each line is the group start in the
MIX. Use the JSON indexes for individual event and command offsets. The
`When` clause names the selector role for kinds 12 and 15 and for object hosts, and the condition read by the matcher; for kinds 10 and 11 it still prints the raw selector (kind 11's selector is the record's own region index, per `0xF2FC0`).
For kind 12, the region and event come from +4 and +6 and the gate comes
from `0xF2DB7–0xF2E16`. Event 2 has a confirmed player-entry caller at
`0xD39BB` and event 3 has a departure caller at `0xD383C`. Other callers
may send the same ID. The [shared predicates](../../lol2-shared-predicates.md) page maps the
shared-array caps to indexes (the [opcode reference](../../lol2-script-opcodes.md) gives them by cell address), and the
[music settings](../../lol2-music-selection.md) page describes command 210.

The level-sheet tool can group effect rows by target scope, render exits,
and follow `triggers` through the event and list indexes to the associated
placement IDs. No runtime state is required for these joins.
