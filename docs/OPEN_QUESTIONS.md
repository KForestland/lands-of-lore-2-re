# Open questions

Numbered so the pages and [`STATUS.md`](STATUS.md) can point at them. Each is something not yet known about the ORIGINAL game's files or rules. When one is answered, its page is updated and the entry says so. Sources: the repo's own "still open" lists ([understanding](lol2-understanding-2026-11.md#still-open), [script engine facts](lol2-script-engine-facts-2026-10.md#still-open)). Each question links the page that holds its evidence.

## At a glance

For each open question, the table gives what was tried and what would settle it. The evidence and addresses are in [Remaining evidence and settling tests](#remaining-evidence-and-settling-tests).

| ID | State | What would settle the rest |
|---|---|---|
| Q1 | Mostly answered | Traced the level stem into the texture opener and matched all 15 banks. Identify the file opened by the type-4 reader and where the two shape readers get their buffers. |
| Q2 | Answered | The original options UI reader starts at byte +10 of the true shape header, or +12 from the former section start. |
| Q3 | Mostly answered | Checked the room-name table, constructor calls and level stems. Find a second opener that receives the exact name `ARENA.MIX`. |
| Q4 | Mostly answered | Traced drift, reversal, selector handlers and the player and creature motion calls. Match the other object receivers to their first geometry rejection. |
| Q5 | Mostly answered | Traced attenuation and the two render paths. Match L10_DC actor 4 to its rendered primitive and first shade value. |
| Q6 | Mostly answered | Classified 289 non-exit branches and traced the slot-37 event. Observe the original L9 interaction and the first later branch that tests the flag it sets. |
| Q7 | Answered | Traced the writer (indexed stores at `0xE0C5C`/`0xE0C82`/`0xE0CD2` from the 480 Hz clock); first countdown after save-load and menu resume measured in the original game |
| Q8 | Mostly answered | Traced the item handlers and the zero checks on instance byte +5. Compare the item use and following clear in normal play, and observe the hit packet's effect. |
| Q9 | Mostly answered | Traced all 35 spell payloads and found when the message timer expires. Identify the first action that sets the timer and observe the effect of the remaining spell callbacks. |
| Q10 | Mostly answered | Traced the mode branches and watched one player-target comparison in L8_SJ. Match the observation values and the requested and installed actions in a named encounter. |
| Q11 | Mostly answered | Mapped the slot reader, the preview flag and two pickup saves. Identify the reader of header +0x94 and match remaining payload fields to known changes. |
| Q12 | Mostly answered | Indexed the movie streams and compared the two exceptional shipped frames. Match their active codebooks and final displayed frames to original playback. |
| Q13 | Partly answered | Direct uses of the cue-table pointer call the sound player or the cleanup call, compare the word with voice +4, test the pointer, or store zero. The 47 room modules' 3134 indirect calls resolve to 63 host functions, and none of those calls the text loader directly. Still open: a text reader that uses the cue after it is stored on the voice. |
| Q14 | Mostly answered | Mapped the texture encoding readers and joined the vector books. Compare the underfilled book with the native decode and observe the original `0x02AC` mip selection. |
| Q15 | Answered | All 33 HMI scores framed and named. `0x1305A4F0` is `MUSIC\CREDITS.HMI`. |
| Q16 | Mostly answered | Traced the Huline Temple connector geometry and descriptor selection. Match the quads that survive screen clipping to the UVs passed to the sampler. |
| Q17 | Mostly answered | Traced the picker and observed both controls from edited placements. Repeat both picks from normally reached saves and compare a click with an item in hand. |
| Q18 | Answered | Every script group has a serialized reference; an empty-hand left click reached L1 placed-item group 0x3648 in the original game |
| Q19 | Answered | — |
| Q20 | Mostly answered | Mapped cache creation and compared all 15 installer lengths to the shipped banks. Compare the 12 mismatches with the same named banks and seed rows in an earlier original edition. |

## Questions

| ID | Question | Page |
|----|----------|------|
| Q1 | Westwood LZ77 with a mode byte. **Mostly answered:** decoder and input/output buffers for all eleven calls, including five VQA calls. The byte at data `0x223D6` selects `global\global.tex` or `c:\leved\-global.tex` (and the paired object and spell names), and the same byte selects the sounds file. **UNCONFIRMED:** the pointer opened by `0x15C9DA` and the pointers passed into the shape arms. The [level texture stem](formats/compression.md#level-texture-filename) joins all 15 shipped banks. Use the Q1 filename test below. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Caller table](formats/compression.md#direct-calls-and-their-buffers) |
| Q2 | `LOCAL.MIX` entry 1. **Answered:** this is `options.shp` (key `0x8248262E`). Native directory lookup adds 2 to each offset. Payload at true header +10 accounts for all bytes in both stored shapes and all 37 compressed shapes. | [Options shape format and native reads](formats/room-sections.md) |
| Q3 | Room archives, 45 versus 47. **Mostly answered.** Both numbers are right. 47 archives carry `WOMS\<ROOM>_.WOM`. 46 of those names are the dword table at file `0x1CFA90`, and `ARENA` is the extra archive. **Still open:** how `ARENA.MIX` is opened. There is no `ARENA.MIX` or `arena_` string, and `ww_hash_v1("ARENA.MIX")` is not stored as a dword. The movie stem `arenaapr` is at file `0x1C3D1A`. Running-game test run once (2026-11-20), still open: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [lol2-level-graph.md](lol2-level-graph.md) |
| Q4 | What do the remaining subcommands and virtual continuations do? **Mostly answered.** The opcode 18 updater, player and creature continuations, and opcode 196 admission, reversal and post-call stores are mapped. Selector handlers are in [the subcommand table](lol2-script-opcodes.md#subcommand-handlers). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Opcode table](lol2-script-opcodes.md), [motion](lol2-script-motion.md) |
| Q5 | **Mostly answered.** The kind-1 inner distance, fade width and accumulation flag have native render readers. Named kind-5, kind-6 and region producers are listed in the event-source table. Running-game test not yet run: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Event producers](lol2-event-producers.md) |
| Q6 | **Mostly answered.** Type 7 has zero rows in the DOS corpus. Slot 52 is the only shared byte in the 72 directly linked exit predicates. Slot 37 reaches a player clear of player bytes +0x1B6–+0x1C1. The 289 other plot branches are classified by level, slot and linked command; their on-screen result remains open. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Shared predicates](lol2-shared-predicates.md) |
| Q7 | What writes each live elapsed cell from the registered clock? **Answered:** the frame update at `0xE0BDD` writes all three cells from a four-sample ring of the 480 Hz clock ([live write](lol2-timer-clock.md#live-write-and-conversion)); a running-game probe saw the stores. Section 67 restore and menu reanchor are traced. In both trials the first countdown consumed the existing elapsed cell before a fresh sample. | [Timer clocks](lol2-timer-clock.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q7-which-live-writer-supplies-the-timer-service) |
| Q8 | What do the remaining item-use handlers do? **Mostly answered:** all 108 indexes have a native mode and effect ([handlers](lol2-item-handlers.md#remaining-modes-and-effects)), including the twelve movie items. The [replacement definitions](lol2-item-handlers.md#replacement-definitions) come from the executable's 74-label table (all 74 join a definition; `lol2_item_labels.py --check`), and each [`0xF7030` projectile variant](lol2-item-handlers.md#projectile-variants-at-0xf7030) is traced to the hit packet it sends to the target's +0x80. The sixteen readers and writers of instance byte +5 are listed ([instance byte +5](lol2-item-handlers.md#instance-byte-5)). **Still open:** what that byte means in play, and game-facing names of the packet bits and several player flags. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Native item handlers](lol2-item-handlers.md) |
| Q9 | What are the downstream spell effects and quest inputs to each lesson? **Mostly answered:** one downstream payload for each of the 35 player-dispatch IDs, and the level grants that feed each lesson item ([spell dispatch](lol2-spell-dispatch.md#payloads-of-the-35-player-slots)). The [effect-17 callbacks](lol2-spell-dispatch.md#effect-17-callbacks) trace the contact and incoming-hit branches. **Still open:** their visible result, the controller-channel names, the message-0x26 producer, (the entry of L1 group 13584 is now traced through placed item 2, [Q18](#q18)). Running-game test run once with a live edit (2026-11-20), still open: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Player spell dispatch](lol2-spell-dispatch.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q9-what-starts-the-timed-message-0x26) |
| Q10 | **Mostly answered.** Paired observation fields, several mode branches, the mode-3 item transfer and the first uses of placement flag masks `0x10` and `0x20` are mapped. Running-game test run once outside a named encounter (2026-11-20), still open: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Creature observation](lol2-creature-observation.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q10-which-observation-path-a-live-mode-2-creature-takes) |
| Q11 | **Mostly answered.** Controlled L20_BB and L1_DC pickups in the original game identify the placed row and recipient-pool occupancy bit. The L1_DC pickup also changes the new player element. The writer and restore routes identify the source and frame state of the L26 surface and L27 texture animation rows. Residual header and payload field meanings remain open. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Native save section descriptors](lol2-save-sections.md#original-opening-cave-pickup-in-l1_dc), [field witnesses](lol2-save-field-witnesses.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q11-which-saved-rows-change-on-a-known-pickup) |
| Q12 | Movies. **Mostly answered.** Pointer tables: 1,109 movies pass every frame, including 4×2 blocks, byte-13 value 0 (10 stage `CBPZ`, 120 are a single `CBFZ`) and the raw chunks in `POOL.MIX` entry 4. 1,109 + 837 streams + 2 open frames = 1,948 ([formats/vqa.md](formats/vqa.md)). **CONFIRMED:** the indexed [pointer-stream commands](lol2-vqa-v2.md#pointer-streams). **Still open:** the destination history of two relative copies inside absolute-mode LCW (`L20_BBI.MIX` entry 25 frame 115, bytes `00 00` at input 23,847; `SPKSTON2.MIX` entry 4 frame 492, bytes `22 a2`, distance 674 with 564 bytes written). Scene ids are the 86-name table ([lol2-movie-scenes.md](lol2-movie-scenes.md)). Running-game test for frame 115 run on an edited copy (2026-11-20), still blocked: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The [packet extent check](formats/vqa.md#structure-of-the-two-exceptional-packets) finds 21 copies in frame 492 from offsets the packet has not written, and its first terminator after 1,059 of 32,000 bytes. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [lol2-vqa-v2.md](lol2-vqa-v2.md), [formats/vqa.md](formats/vqa.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q12-which-history-do-two-exceptional-vqa-frames-read) |
| Q13 | Text: where the dialogue and message tables are stored, and their format. **Partly answered.** The message tables (help, options, automap, credits, error text) are settled; character dialogue is still open. Message tables: five TRR names, one reader, record layout in [lol2-text-tables.md](lol2-text-tables.md). `TEXT.MIX` and `TCEL.MIX` are room archives. The `WOMS` line path is an `.aud` name. The TRR mode-1 open prefers a successfully opened loose file. Spoken-name path: [lol2-speech.md](lol2-speech.md). Running-game test run once in L8_SJ (2026-11-20), still open: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [lol2-text-tables.md](lol2-text-tables.md), [lol2-speech.md](lol2-speech.md) |
| Q14 | **Mostly answered.** Native readers mapped for raw, row-span, run-length column and `0x1246` vector-coded mips. 27,889 vector records join 400 codebooks. The `0x02AC` native path and some companion bytes remain open. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Texture container](lol2-level-texture-container.md#vector-coded-rows-flag-0x1246) |
| Q15 | HMI-MIDI music. **Answered:** 33 `HMI-MIDISONG` entries, the event stream, and a standard-MIDI converter. The direct builder (`0xCA8E0`) names `0x1305A4F0` as `MUSIC\CREDITS.HMI`. The 33 `FORM` entries in `LOCAL.MIX` are XMIDI scores under the same stems. | [Music](lol2-music-2026-11.md), [selection](lol2-music-selection.md#the-direct-credits-path), [XMIDI](formats/xmi.md) |
| Q16 | Wall-span geometry, UVs and special openings beyond the traced span; the Huline Temple interior portals. **Mostly answered** ([formats/walls.md](formats/walls.md)): ordinary upper and lower classes, both connector endpoints of the Huline Temple example, and the fractional geometry of bit-4 rows. Remaining work is screen-space clipping and sampler setup. Running-game test not yet run: [test](NEEDS_A_RUNNING_GAME.md#probes-not-yet-run). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [lol2-wall-material-provenance.md](lol2-wall-material-provenance.md), [draracle-restoration.md](draracle-restoration.md) |
| Q17 | L8 controls 69 and 114. **Mostly answered.** Direct events, motion, link and unlink commands mapped. The input path to the control slot is traced (picker to `0x110ACD`); both visible pick surfaces and groups were observed in [edited-save runs](lol2-l8-controls.md#empty-hand-clicks-from-edited-placements). The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [L8 controls](lol2-l8-controls.md), [running-game test](NEEDS_A_RUNNING_GAME.md#q17-what-on-screen-action-reaches-these-records) |
| <a id="q18"></a>Q18 | **Answered.** The placed-item table leads to 57 groups outside the earlier four-table join. The static join ties L1 stream-1 group 13584 to the placed item 2 empty-hand interaction. After this join no group of the 13,197 in the 15 levels is left without a serialized reference (review count over both streams, the four event tables, the region lists and the placed items). An empty-hand left click on L1 item 16 reached group 0x3648 in the original game. | [Placed-item event lists](lol2-event-producers.md#placed-item-event-lists), [per-level notes](levels/notes/README.md) |
| Q19 | **Answered.** The level ODF entry stores the 147-byte definitions at header u32 +0x10 with count at +0x48, verified in all 15 level archives and in the native reader | [formats/entity-records.md](formats/entity-records.md) |
| Q20 | The texture cache. The installer ships `CACHEBAK.MIX` (131 bytes) and `CDCACHE.LS_` (4,008 bytes, 15 records, every state -1). **Mostly answered:** the native seed copy, the marker at 66, the 200-row allocator at 70 and the shutdown writeback are mapped in [lol2-cache-initializer.md](lol2-cache-initializer.md). **CONFIRMED:** three older list lengths match shipped banks, twelve differ and only L1 has a finite list position. This copy's executable reads `DOS 1.30` at `LOLG.DAT+0x1C4714` and `Dec 03 1997` / `17:51:02` at `+0x1C4749`. Each shipped bank's first decoded block names an art folder and a leved folder under `PROJECTS\LOL_2`; `L3_DH` art is `SPHERE1\L2&3`. The seed's only printable strings are the 15 names. **Still open:** which build supplied the differing sizes. A run's written `CDCACHE.MIX`/`.LST` is one run's state, not the format. The close-out on the detail page gives what was measured, what was tried, and what would settle it. | [Native cache initializer](lol2-cache-initializer.md), [MIX layout](formats/mix.md) |

## Remaining evidence and settling tests

Static checks use the original files or executable. A runtime witness
uses one game action to bind an indirect producer or player-facing result. See [Needs a running game](NEEDS_A_RUNNING_GAME.md) for debugger procedures.

| ID | Status | What was measured, tried, and what would settle the rest |
|---|---|---|
| Q1 | Mostly answered | **CONFIRMED** each direct call to `0x158D58` and its source, destination and capacity. **CONFIRMED** the byte at `0x223D6` selects the two texture-name triples and the sounds file ([compression](formats/compression.md), [sound cues](lol2-sound-cues.md)). **CONFIRMED** the stem at `0x9C35E` comes from the [native level-name table](formats/compression.md#level-texture-filename) and joins all 15 shipped texture members. **UNCONFIRMED** the first argument of `0x15C9DA` and the shape pointers. **Test:** Identify that argument and follow the pointers passed to `0x151F0A` and `0x15A2A0`. The WSA branches `0x15BEE1`/`0x15C50D` already have 21 named witnesses ([named WSA deltas](formats/compression.md)). [Caller table](formats/compression.md#direct-calls-and-their-buffers) |
| Q2 | Answered | **CONFIRMED** `0x15A22D` adds entry +2 to the directory value. `0x15A475` advances by 10 from that header. Stored headers at `LOCAL.MIX+0x19311D1` and `+0x1935AF2` frame all 16,384 and 11,960 payload bytes. |
| Q3 | Mostly answered | **CONFIRMED** all three direct room-builder calls use the 46-entry table. A missed name selects index 0. The two dynamic archive calls also have no `arena` leaf among the native level stems. **UNCONFIRMED** a separate retail opener for `ARENA.MIX`. Trace an indirect host wrapper into constructor `0x11C654` with that exact name. **CONFIRMED, running game** a load into L20_BB opens `l20_bb.MIX`, `l20_bbI.MIX` and `CDCACHE.MIX` through it, and no call named ARENA followed the opening movie in that run. [Direct constructor census and external module witnesses](lol2-room-archives.md#the-extra-arena-archive). |
| Q4 | Mostly answered | **CONFIRMED** opcode 18 drift and direct sequence calculation, and opcode 196's post-call state and transform writes. **CONFIRMED** player and creature +0x18 receivers, vertical projection and the opcode-196 signed reversal. **UNCONFIRMED** other dynamic receivers and which geometry case obstructs each class. Selector handlers for opcodes 2, 6, 9 and 15 are in [the subcommand table](lol2-script-opcodes.md#subcommand-handlers). Match the opcode-196 handler at `0x64DDC` and record the first geometry rejection before the candidate transform is written. [Native motion branches](lol2-script-motion.md). |
| Q5 | Mostly answered | **CONFIRMED** kind-1 attenuation and named event producers, including region kind-12 events 0 and 5. **UNCONFIRMED** the first shade value for L10_DC actor 4 despite the row's zero contribution. **Test:** Match a primitive to that actor at `0x129C23` (scalar, 256-byte shade row) or `0x13C845` (three packed channels). |
| Q6 | Mostly answered | **CONFIRMED** type 7 (arm `0x66B5C` of the evaluator at `0x66AB0`), both exit guards using slot 52, and the slot-37-guarded event's clears through `0xD0138`. Outside the exits, 289 event records branch on 28 shared slots, and each record's level, slots and linked commands are in that table ([census](lol2-shared-predicates.md#shared-predicates-outside-exits)). **UNCONFIRMED** how the latter changes the original L9 interaction. **Test:** Find the first of the eight tests of mask `0x80` reached after the subcommand-`0x26` handler returns (its own arm and direct callees do not read +0x228), and the on-screen result in L9. The gate at `0xD01C5` copies player +0x229 and does not read +0x228. |
| Q7 | Answered | **CONFIRMED** in code and in one run: indexed stores at `0xE0C5C`/`0xE0C82`/`0xE0CD2` ([live write](lol2-timer-clock.md#live-write-and-conversion)). **CONFIRMED** section 67 restore at `0xE751D–0xE7559` and normal menu resume at `0xA031A–0xA034A`. **CONFIRMED** the first countdown and first frame sample after both [save-load and menu resume](lol2-timer-clock.md#first-countdown-after-save-load-and-menu-pause). |
| Q8 | Mostly answered | **CONFIRMED** all 108 handler slots, including the 12 movie-item routes; the four replacement reads resolve to definitions 58, 56, 67 and 98 through the label table at `0xC610` and its builder `0x623D4`; the projectile contact slot `0xF7774` sends one packet per variant to the target's +0x80. **UNCONFIRMED** instance +5 in play and the on-screen meaning of the packet bits. A re-read of the four loads shows each is followed by `test` of that register against zero (`0x7E482`, `0x8CA4E`, `0x9B5C5`, `0xD25F9`), not a compare with 5, and the store at `0x9B5E9` is the bytes `C6 40 05 05`. **Test:** watch the held instance byte +5 and `[0x2260B]` across one use of handler 102 and the next opcode 2 selector 0 or 38 that clears them. For the packet bits, follow the receiver called at `0xF7774` before and after that contact. |
| Q9 | Mostly answered | **CONFIRMED** all 35 player payloads and original lesson-grant inputs. **CONFIRMED** effect 17's stage and link writes. **CONFIRMED** effect 15's stage-dependent hit packets and effect 32/33's single contact packet to the target's +0x80. **UNCONFIRMED** their visible result and timed message 0x26's producer. **Test:** A runtime watch on player +0x185 distinguishes the first nonzero store from its observed expiration at `0xD2E57`. **CONFIRMED, live edit** the absent-ID-4 lesson reached the 0x23 push at `0x86229`; the low byte of +0x185 did not change in a few seconds, which does not settle it ([live edit](lol2-spell-dispatch.md#absent-id-lesson-branch-live-edit)). |
| Q10 | Mostly answered | **CONFIRMED** observation pairs, mode-3 item transfer, selected placement flags, the mode-3 +0x64 writes, the mode-4/5 definition thresholds and two writers of +0xA3. **UNCONFIRMED** the remaining masks and encounter inputs. **Test:** Capture observation +0x9E and both update bytes for mode 8 at `0xA2C63`, then compare the requested action at `0xA2E84` with the install at `0xA7DC4`. **CONFIRMED, running game** an L8_SJ actor with +0xB4 bit 0x20 set and the player as target reached the compare at `0xA32B4`; the branch after it was not watched ([live entry](lol2-creature-observation.md#live-entry-to-the-player-target-branch)). |
| Q11 | Mostly answered | **CONFIRMED** save header, section descriptors and controlled L20_BB and L1_DC pickups. **CONFIRMED** the global and level payload routes (`0xE7931/0xE69D1`, `0xE8125/0xE7418`). **UNCONFIRMED** residual header and payload field names. **CONFIRMED** header +0x98 is the preview flag: the writer stores the constant 1 (`0xE78A0`, `0xE78B1`), and the reader `0xE61F4` tests it at `0xE62D2` before it reads the preview width, height and offset (+0x9C, +0xA0, +0xA4). **Test:** The writer stores zero at +0x94. Four reads copy the 0x25A-byte header (`0xE6168`, `0xE6283`, `0xE687E` and `0xEB7AE`) and pass it to `0xEB82C`, which does not address +0x94; none of the four reading functions addresses it either. A reader in a callee that receives a pointer into the header would name it ([save witnesses](lol2-save-field-witnesses.md)). |
| Q12 | Mostly answered | **CONFIRMED** 1,109 pointer-table passes, 837 pointer-stream (`VPRZ`/`VPTR`) movies whose 52,187 indexed frames expand to full-size buffers in memory, each with a mask of pixels that still depend on the initial destination, and two single-frame exceptions (115 and 492). The [original trigger routes](formats/vqa.md#original-trigger-routes-for-the-two-frames) map the scripts and the clip item. **CONFIRMED, edited-save run** frame 492 reads five zero bytes from before the decoded span. **CONFIRMED** frame 492's packet (`SPKSTON2.MIX+0x17695E8`) has 21 copies from offsets it has not written and its first terminator ends the plane after 1,059 of 32,000 bytes ([structure](formats/vqa.md#structure-of-the-two-exceptional-packets)). A measure-only parse of the two payloads finds one out-of-range command in frame 115 (input 23,847, length 3, distance 0, after 30,400 bytes; the stream then ends at 32,010 output bytes) and splits frame 492's 21 copies into 11 reads from before the output (59 bytes, the first of them the known 5 bytes at -110) and 10 absolute copies from past the bytes written so far (279 bytes). **UNCONFIRMED** the frame-115 history and both active codebooks. At `0x158D58`, capture the destination buffer before either short relative copy, and match the codebook selected at the frame callback to the indexed source. **BLOCKED, edited-save run with a live edit** setting prop 87 +0x25 to 13 did not start `bb_brth`; group `0x02E8` must send its value-20 event. |
| Q13 | Partly answered | **CONFIRMED** TRR offsets and the indexed global EFX cue lookup. The mode-1 open via `0x118440` tests the loose file at `0x11845E` before the archive lookup at `0x1184AA`. Spoken-name path: [lol2-speech.md](lol2-speech.md). The eight arms pass a cue id from the table at `0x269CC` to `0xE3924` and do not reach the `.aud` append. **CONFIRMED** the initializer `0xE363C` and 404-word read at `0xE3742` from `LOCALLNG.MIX+0x1B17198`. **CONFIRMED** the 533 direct uses of that pointer: 499 pass the word to `0xE3924`, 11 call `0xE4004`, 21 compare the word with voice +4, one tests the pointer for zero at `0x14EA84`, and one stores zero at `0x14EA9C`. **UNCONFIRMED** a text reader that uses the cue after it is stored on the voice. **Test:** The 47 room modules make 3134 absolute indirect calls, all resolved to 63 host functions. None of those functions, walked to every return, calls `0xCF014` directly; host +0xC4 (`0xEE540`) reaches it four calls deep in the options menu `0xB9204`. 763 calls from 37 modules enter `0xEE784`. Host +0x13C is `0xF16D8` (31 calls): it indexes the cue words at `0x269CC` and calls `0xE4004`. A text reader outside these 63 functions, or a second container, would settle it. [Post-call consumers](lol2-speech.md#cue-consumers-after-playback-starts). **CONFIRMED, running game** in L8_SJ four category words held their file values and were not read in a short stand and walk; that level does not load the documented caller ([observation](lol2-speech.md#running-game-observation-in-l8_sj)). |
| Q14 | Mostly answered | **CONFIRMED** vector rows at `0x12607C`, companion lookup at `0x132835`, column runs at `0x12621C` and packed spans at `0x126000`. **UNCONFIRMED** vector tail, one underfilled book and `0x02AC` rendering. **Test:** Compare the native book output at `0x67052` to the affected L20_BB read at `0x12616C`; capture the `0x02AC` mip entering `0x125FC4`. |
| Q15 | Answered | **CONFIRMED** loader, events and 32 indexed stem joins. Direct path at `0xCA8E0` names the last HMI key `0x1305A4F0`; its digital counterpart is `0x22F7A4EB`. |
| Q16 | Mostly answered | **CONFIRMED** the wall constructors, the normal at `0x1322A4`, descriptor selection before `0x11496D`, and UV offsets at `0x12759C`. **UNCONFIRMED** final clipping and sampler UVs for the Huline opening. **Test:** Follow each L14_HT quad through the callback at `0x11496D` and compare surviving data at `0x133FF4` with the span setup. |
| Q17 | Mostly answered | **CONFIRMED** the live controls 69 and 114 have vtable `0x5484`. Its handler `0x5DA48` calls `0xB5000` at `0x5DAAD`. **CONFIRMED** the pointer-to-control path (`0x75D98` → `0x110F0C` → picker `0xE1050` → `0x110ACD`). **CONFIRMED, edited-save run** both visible picks selected the expected groups. **UNCONFIRMED** replay from normally reached native saves. [Click coordinates and dispatch](lol2-l8-controls.md#empty-hand-clicks-from-edited-placements). |
| Q18 | Answered | **CONFIRMED** the group directories, the 663 placed-item rows and 57 additional serialized references. The static L1 group 13584 join comes from placed item 2 at `L1_DC.MIX+0x6FBDC8`, through the handler `0x95200`. **CONFIRMED** an empty-hand left click on L1 row 16 went through `0x95218` to group `0x3648` at `0x646EC`. All 57 additional serialized references join to groups. |
| Q19 | Answered | **CONFIRMED** header +0x10/+0x48 gives the ODF definition offset and count in all 15 archives. The native reader consumes 147-byte records. |
| Q20 | Mostly answered | **CONFIRMED** seed copy, marker at 66, 200 allocator rows at 70, and the first payload boundary at 5,070. The shutdown route writes the 256-byte active row via `0x119F62` and installs the rebuilt directory. **CONFIRMED** the 15-way seed comparison via the native header read at `0x11931D`. **CONFIRMED** the version and date strings `DOS 1.30` at `LOLG.DAT+0x1C4714` (read at `0xB9BD0`) and `Dec 03 1997` / `17:51:02` at `+0x1C4749` (read at `0x60AD5`/`0x60B80`); the VQA library carries `Sep 05 1997 13:11:59` and DOS/4G `Apr 03 1996`; the seed's 15 name strings and no date, and the art and leved folder in each bank's first decoded block. **UNCONFIRMED** provenance of the 12 differing lengths. The version and date strings and the folder names do not name the older build. A byte search finds each of those twelve sizes only in its own installer seed record (+0xDC and the duplicate +0xE0) and nowhere in `LOLG.DAT` or `LOLG.EXE`. **Test:** compare the same named first dwords in an earlier original edition. |

## Memory watch questions

These tests need the code-object base and a matching save or action. [Debugger setup attempts](NEEDS_A_RUNNING_GAME.md#21-november-slot-and-watch-status)

| Probe | Reason this pass did not settle it |
|---|---|
| Timed message `0x26` | The previous slot reached `0x23`. It needs the full four-byte watch through the end of that message. |
| Movie frame 115 | The relocated late slot was already past the scene. The earlier level-20 slot `25ab2119ec3d` has prop 87 state zero. A relocation from it can approach the prop 242 event that starts the timer chain. The chain still needs to be observed. |
| `ARENA.MIX` | The watch must cover startup and room changes through a hub. An ordinary level-4 slot is sufficient. |
| Cue words | The earlier trace used L8_SJ and never opened MCEL. An original L4_HJ slot exists and permits a separate approach to movable 76, which owns the MCEL opener. |
| Cemetery wall shade | The level-10 slots named below are available. No draw with the evaluator and the resulting shade row together was captured. |
| Named encounters | Two copies of the same original level-8 slot can approach live actors 45 and 76 separately. The target, flag and action reads across the portal are outstanding. |
| Nonpositive hits | The actor-45 setup gives an encounter. No hit with a zero or negative working value has been caught. |
| `0x02AC` mip | The L16_CA slot is available. The two descriptor IDs did not join to a stored wall material selector, so a wall-facing relocation has no verified target. The first live lookup can identify the drawn surface or object. |
| Short block | A slot is available. The missing observation is the first write to the stack header before `0xE83D9`. |

- **Timed message 0x26 (run once 2026-11-20, open).** Settles the producer in
  [Q9](#questions). Full test:
  [Q9](NEEDS_A_RUNNING_GAME.md#q9-what-starts-the-timed-message-0x26). Setup: the late
  game-written level-20 slot used for the
  [lesson control](lol2-spell-dispatch.md#controlled-use-of-the-level-20-lesson).
  Watch: a write watch on player +0x185 (player pointer from
  `0xD2E30`), and breaks at `0x86230` (message 0x23) and `0xD2E57`
  (the clear before message 0x26). Play: use the lesson item for an
  acquisition ID the player does not have yet, then let the character
  change form (player +0x1AB). Result: a nonzero write to +0x185 that
  reaches `0xD2E57` on the same object names the producer. Only zero
  values repeat the known controls. Run 2026-11-20 (live edit: learned
  count 5 → 0): the 0x23 push was fetched, the low byte of +0x185 did
  not change and 0x26 was not sent in a few seconds. Next: watch all
  four bytes until the 0x23 message ends ([Q9](NEEDS_A_RUNNING_GAME.md#q9-what-starts-the-timed-message-0x26)).
- **Movie frame 115 of `bb_brth` (run once 2026-11-20, blocked).** Settles the frame-115
  history in [Q12](#questions). Full test:
  [Q12](NEEDS_A_RUNNING_GAME.md#q12-which-history-do-two-exceptional-vqa-frames-read).
  Setup: a level-20 slot from before timer slot 12 expires, so prop 87
  is not yet in state 14; the
  [edited L20_BB copy](formats/vqa.md#scene-probes-from-edited-copies)
  had already played the scene. Watch: `0x172838` (pointer LCW) and
  `0x158DB2` (the short copy). Play: let prop 87 play scene 65
  (`L20_BBI.MIX` entry 25). Result: on frame 115 log the copy's
  source, destination, capacity and the bytes already there. A short
  self-copy from the current destination matches the static reading;
  anything else is the original history. Log the active codebook too.
  Run 2026-11-20 on the relocated copy with prop 87 +0x25 set 14 → 13
  in memory: no movie, so no frame 115. Setting the state does not send
  the value-20 event; group `0x02E8` must run
  ([Q12](NEEDS_A_RUNNING_GAME.md#q12-which-history-do-two-exceptional-vqa-frames-read)).
- **How `ARENA.MIX` is opened (run once 2026-11-20, open).** Settles the open part of
  [Q3](#questions). Setup: any game-written slot; no room is
  known to lead to the Arena, so there is no edited-placement recipe.
  Watch: the archive constructor `0x11C654`, logging the name it is
  given, and the name-driven room opener (`0xEDFAF–0xEDFB6`, room
  import `0xEF558`). Play: the start, each hub room change and the
  movies. Result: a constructor call with the name `ARENA.MIX` (any
  letter case) gives its caller, which is the route. No such call over
  the stated play means that play does not open it. Details:
  [the extra ARENA archive](lol2-room-archives.md#the-extra-arena-archive).
  Run 2026-11-20 in two DOS sessions, watch armed after startup (in the
  second, during the opening movie): each load into L20_BB made three
  constructor calls, `l20_bb.MIX` (return `0x9BFB1`), `l20_bbI.MIX`
  (`0x9C030`) and `CDCACHE.MIX` (`0x119C53`), and none named ARENA.
  Startup before the watch and hub room changes were not covered. Next:
  arm at program start and change rooms through a hub
  ([room archives](lol2-room-archives.md#the-extra-arena-archive)).
- **Who reads the 404 cue words (run once 2026-11-20, open).** Settles the text side of
  [Q13](#questions). Setup: any game-written slot. Watch: after
  the loader's read at `0xE3742`, take the table pointer stored at data
  `0x269CC` and set read watches on the cue words, at least on the
  eight category words (table index 161, 162, 167, 168, 174, 197, 198
  and 199, two bytes each). Play: a scene that plays one of those
  cues, such as the MCEL room callbacks. Result: the known readers are
  the category arm (`0xEEAC2–0xEEAF9`), the voice loops
  (`0xEEB39–0xEEBD3`) and the cleanup at `0xF0B98–0xF0C29`. A read
  from any other address, followed into text, is the text reader.
  Only known readers bound the scenes played. Details:
  [cue consumers](lol2-speech.md#cue-consumers-after-playback-starts).
  Run 2026-11-20 on the game-written L8_SJ slot `9a46a2bdecb4`: the
  pointer was set and the flag byte at data `0x269C4` was 0. Read
  watches on indexes 161, 167, 174 and 197 (words 298, 276, 286 and
  323, as in the file) saw no read in about six seconds of standing
  and a few seconds of walking; 162, 168, 198 and 199 were not watched
  (four hardware watch slots). No room scene, dialogue or combat ran.
  The documented way into these eight indexes is the category switch
  `0xF133C`, called from a room module (the MCEL room of L4_HJ); L8_SJ
  does not load MCEL, so this run could not show a known read either
  ([observation](lol2-speech.md#running-game-observation-in-l8_sj)).
  Next: a game-written L4_HJ slot, two sessions of four watches, and
  enter the MCEL room.
- **Shade index on one L10_DC wall (watch unarmed).** Two
  game-written slots have active level 10 (slot +0x17C), SHA-256
  prefixes `0b7d5498dc88` and `7eac342b547a`. The 2026-11-20 session
  skipped it, saying no such slot was available. Settles the open step
  of [Q5](#questions). Setup: a game-written slot in L10_DC.
  Watch: the return of the evaluator `0x1319B4` (the two sums, the
  clamp at `0x131D16–0x131D4D`), then the scalar caller at `0x129C23`
  (row offset `(S >> 8) & 0xFF00` at `0x129C28–0x129C33`) and the
  lookup at `0x12AA89–0x12AAA8`. For a wall drawn per vertex, follow
  the callers `0x126E82`, `0x127BD6` or `0x1288DA` through clipping
  (`0x133C68`, `0x133FF4`) to the span setup. Play: stand in view of
  one wall and do not move. Result: for one primitive, log both sums,
  `S` and the shade row it uses. Row `S >> 16` reaching the lookup
  unchanged settles the scalar path; a different row shows the span
  interpolation. Details:
  [shade row](lol2-event-producers.md#scalar-shade-row-and-packed-colour).
- **Two mode decisions in named encounters (run once 2026-11-20, open).** Settles more
  of [Q10](#questions). Full test:
  [Q10](NEEDS_A_RUNNING_GAME.md#q10-which-observation-path-a-live-mode-2-creature-takes).
  Setup: two edited copies with the party placed near one named
  creature each (level, actor number), by the
  [position recipe](lol2-save-format.md#editing-a-copy-of-an-original-slot).
  Watch: `0xA32B4` for one actor whose target +0x34 is the player.
  Play: approach in sight, then step behind a portal edge. Result: with
  +0x9D mask 0x05 clear and 0x0A set, action 1 or action 9 shows the
  remembered bit; a change to another mode needs a trace of that
  actor's mode store. Run 2026-11-20 on the unedited L8_SJ slot, with
  no edited placement and no named creature: one actor with target
  the player reached `0xA32B4` with +0x9D `0x82`, +0xB4 `0x24` and
  +0xB9 `0`; the branch after the compare was not watched
  ([Q10](NEEDS_A_RUNNING_GAME.md#q10-which-observation-path-a-live-mode-2-creature-takes)).
  Next: the two edited placements, with breaks after the compare.
- **Nonpositive hit contributions (not run).** Settles the open
  nonpositive and descriptor-flag cases on the
  [combat page](lol2-combat-ai.md#hit-context-and-reduction); no
  numbered question holds them. Setup: an edited copy with the party
  placed near one creature, by the
  [position recipe](lol2-save-format.md#editing-a-copy-of-an-original-slot).
  Watch: `0x62EB9` (the rounding `sar(fixed + 0xFFFF, 16)`) and the
  descriptor switch at `0x62E6B`. Play: trade blows until a hit
  arrives with a zero or negative working contribution. Result: log the
  fixed value before the rounding, the switch arm taken for each flag
  and the health the receiver sets at `0xA6CC8–0xA6CDF`.
- **The `0x02AC` mip path (not run).** Settles the live `0x02AC`
  branch of [Q14](#questions). Setup: a game-written slot in
  L16_CA, in view of a surface that uses descriptor 7320 or 7322 (rows
  1507 and 1508). Watch: the selector `0x125FC4` and the book output
  at `0x67052`. Play: stand still facing that surface. Result: the mip
  pointer entering `0x125FC4` and the branch it takes on the record's
  `0x20` bit, compared with the
  [static read](lol2-level-texture-container.md#run-length-columns-and-raw-fallback-mips).
- **The short-block dword `0xFF00FFFF` (not run).** Settles one
  residual header field of [Q11](#questions). Setup: any
  game-written slot. Watch: the stack address passed at `0xE83D9` plus
  0xD4, from before `0xE7F68`. Play: save the game, so that the writer
  produces a short level block. Result: the instruction that leaves
  `0xFF00FFFF` at that address is the producer. Details:
  [short snapshot status](lol2-save-field-witnesses.md#short-snapshot-status).
