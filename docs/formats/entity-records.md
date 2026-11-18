# 147-byte entity records

**What:** fixed 147-byte records, each a 135-byte body followed by a 12-byte NUL-padded name tag (`B_HUMAN`, `WORM`, `Roach`, …), in every level archive. Field notes: [lol2-entity-object-map.md](../lol2-entity-object-map.md) and the docstring of `tools/lol2_entity_field_analyzer.py`.

**Read:** all 15 level archives. Tools: `tools/lol2_entity_field_analyzer.py` (all records), `tools/lol2_cross_level_witnesses.py` (B_HUMAN and WORM).

## Where they are

The tools find the records by searching for known name tags and stepping 147 bytes back and forth; no header field pointing at them is known yet. They lie in a different entry from the [level data entry](level-data.md): for L1_DC, file bytes 7,417,243-7,418,860 inside entry 0 (from its byte 27,723); for L9_DR inside entry 0 (from byte 59,142); for L20_BB inside entry 1 (from byte 13,847). CONFIRMED (offsets), structure of that entry UNCONFIRMED ([Q19](../OPEN_QUESTIONS.md)).

## Confirmed

128 records of 62 types in all 15 level archives, every tag printable ASCII (`lol2_entity_field_analyzer.py --check`); 25 B_HUMAN and 4 WORM records in 12 levels (`lol2_cross_level_witnesses.py --check`). Body field meanings are in the analyser's field map (UNCONFIRMED until traced to the program).

`tools/lol2_l9dr_census.py` reads all of `L9_DR.MIX` as 147-byte slots from offset 0; it is exploratory and does not locate these records.
