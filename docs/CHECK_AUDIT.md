# Check audit

The 19 November 2026 audit used reviewed commit `c1cc68e` and the English DOS 1.30 originals.
An untouched local clone passed the corpus checks and unit tests. In scratch clones
each case changed one value or deleted one file, ran the full `check_all.py`
and `python3 -m unittest`, then restored the file. The source installations
were read-only for the audit. The deliberate changes were never committed.

**Baseline result.** 11 of 20 changes failed at least one suite.
9 escaped both suites. Rows below describe the deliberate scratch errors.

| Case | Kind | File and deliberate change | Full corpus check that failed | Unit tests |
|---:|---|---|---|---|
| 01 | Generated page | `docs/NUMBERS.md`: first 45-tick item strike value to 46 | `lol2_numbers` | Passed |
| 02 | Generated page | `docs/NUMBERS.md`: first item record from +0x5B78E9 to +0x5B78EA | `lol2_numbers` | Passed |
| 03 | Generated page | `docs/NUMBERS.md`: descriptor order from disk order to reverse order | `lol2_numbers` | Passed |
| 04 | Reader | `tools/lol2_source_format.py`: MAP minimum header from 0x244 to 0x240 | Passed | Passed |
| 05 | Reader | `tools/lol2_source_format.py`: opcode 14 size from 8 to 7 | `lol2_level_writer`, `lol2_disassemble_scripts`, `lol2_event_browser`, `lol2_level_report`, `lol2_progression`, `lol2_plot_branches`, `lol2_media_check`, `lol2_level_notes`, `lol2_inspect`, `lol2_numbers` | Failed |
| 06 | Reader | `tools/lol2_hmi_midi.py`: HMI MIDI division from 120 to 119 | `lol2_hmi_midi` | Passed |
| 07 | Reader | `tools/lol2_level_writer.py`: swap timer reload field names min and max | Passed | Passed |
| 08 | Reader | `tools/lol2_level_writer.py`: expected command count from 42,594 to 42,593 | `lol2_level_writer` | Passed |
| 09 | Reader | `tools/lol2_text_tables.py`: empty automap rows from 285 to 284 | `lol2_text_tables` | Passed |
| 10 | Reader | `tools/lol2_save_writer.py`: save version stamps from 27 to 26 | `lol2_save_writer` | Failed |
| 11 | Reader | `tools/lol2_numbers.py`: spell schools table from 0x1CCB44 to 0x1CCB45 | `lol2_numbers` | Passed |
| 12 | Format documentation | `docs/formats/mix.md`: MIX directory start from +6 to +7 | Passed | Passed |
| 13 | Format documentation | `docs/lol2-level-script-format.md`: command stream 0 length from +0x84 to +0x85 | Passed | Passed |
| 14 | Format documentation | `docs/lol2-level-script-format.md`: region descriptor count from +0xAC to +0xAD | Passed | Passed |
| 15 | Format documentation | `docs/lol2-save-format.md`: global save directory start from +0x18E to +0x18F | Passed | Passed |
| 16 | Format documentation | `docs/lol2-music-2026-11.md`: HMI track directory pointer from +0xE8 to +0xE9 | Passed | Passed |
| 17 | Format documentation | `docs/lol2-item-format.md`: item flags word from +0x3D to +0x3E | Passed | Passed |
| 18 | Deleted target | `docs/formats/mix.md`: remove the MIX format page | `rating`, `doc_index`, `doc_links` | Passed |
| 19 | Deleted target | `docs/levels/README.md`: remove the level sheet index | `lol2_level_report`, `rating`, `doc_index`, `doc_links` | Passed |
| 20 | Narrative | `docs/HOW_THE_GAME_WORKS.md`: say both region events go to the previous region | Passed | Passed |

Escaped cases: 04, 07, 12, 13, 14, 15, 16, 17, 20.

## Checks added after the audit

- `doc_format_offsets.py --check` reads six sampled offsets from the format
  pages. The MIX row, save directory and HMI track-table pointer are probed
  through `parse_mix`, the slot header reader and `track_table`: the check
  builds a small synthetic file with a marker at the documented offset and
  asks the reader for the field. The two level-script rows are compared with
  the `STREAMS` and `REGION_DESCRIPTORS` constants that the script exporter
  reads with, and the item flags word with the field table that
  `lol2_inspect.py --item` prints. A wrong page offset, or a reader that moved
  the field, fails. The check reports the affected page and field and is part
  of `check_all.py`.
- Independent synthetic fixtures test the 0x244-byte MAP minimum and the two
  distinct stored timer parameters at record +6 and +7. Byte equality alone lets
  the same field naming mistake occur in both the reader and writer.

The focused checks rejected all 8 automatable escapes in a second
scratch pass (cases 04, 07, 12, 13, 14, 15, 16, 17).
Case 20 remains outside automated coverage. The sentence changes the meaning
of a description while leaving the bytes, generated tables and links valid.
A reviewer can compare that sentence with the evidence it cites. The offset
check covers the named rows only.
