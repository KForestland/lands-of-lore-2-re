# Hive executioner: combat evidence checkpoint

This update promotes bounded reverse-engineering results and a portable verifier.
It does not establish full native combat parity or complete Classic Edition.

## Findings

The pinned Hive definition binds actor36 to EXEC. Action5 selects animation11 or12
according to the actor mask/mode. Their source resources704/771 contain18/17 frames.
Damage events occur at frame8 or frames7/11; event scaling is50 percent of actorA6.

The native timer subtracts a word delta and advances only when negative, refilling
by1024. Entering the forward final frame or reverse frame0 requests event3 and clamps
negative residual time. Native units have not yet been mapped to wall-clock seconds.

A matching nonlethal attacker callback sets B7 bit3. Positive loss with bit4 set
requests adjustment7 and clears bit4; zero loss retains it, so a later hit can request
adjustment8. Word7E and byteAD wrap. The adjustment helper applies30 signed changes
and clamps each byte to0..255; operation order matters.

The original tables are `global\ai\EXEC\effector.csv` and `stat.csv` in GLOBAL.MIX.
The local native CSV-parser replay matched58×30 effector bytes and32×1 stat bytes.
The actor constructor copies32 stat bytes into actor4C. Source stat bytes2/3 are50/50;
definition81 is30 and the loader computes minimum82=3. Native A1F2C returns15.
A3zero retains A6/A7=15/15; nonzero reduces both to12. Those initial values request
7 or6 damage at the50-percent events, before target mitigation. The A3 producer and
later recomputation remain open.

## Portable verification

Install Python3 and Capstone, then use your own matching game installation:

```sh
python3 -m pip install capstone
python3 tools/draracle/verify_executioner_arithmetic.py \
  --game-root /path/to/game \
  --out restoration-output/executioner-arithmetic.json
```

Required original files: `LOLG.DAT`, `GLOBAL.MIX`, `DAT/L5_HC.MIX`. The tool rejects
unsupported hashes and does not modify those files. No cached local extracts,
absolute workstation paths or game payloads are included.

The included verifier reads the source definition/CSVs, executes the native minimum
initializer and65,536 damage splits, checks all65,536 stat/delta pairs and512 cases
using the original adjustment rows. It also checks destination sentinels and stack
balance. Its source CSV parsing and runtime allocation are supplied Python boundaries;
MOVSX is explicitly modeled. It does not replay the entire constructor, CSV parser,
attack scheduler or target health handler. The fuller results above summarize the
local research pass and are deliberately distinguished from this portable coverage.

The supporting `extract_creature_states.py` and `verify_creature_states.py` preserve
the existing state/view analysis tools and the fail-closed instruction interpreter.
No generated game-derived fixtures are committed.

## Remaining dependencies

Live A3/AI producers, subsequent stat recomputation, native clock conversion,
mitigation/health composition, lethal continuation and event-queue effects remain
before scene integration. The companion Godot combat component is detached from the
live encounter. Functionality remains ahead of UI polish; Classic Edition precedes
LoL3 work.
