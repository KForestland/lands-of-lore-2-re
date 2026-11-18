# Movie scene ids

A level script plays a movie by number. Opcode 21 is six bytes. Byte 4 (the fifth byte) is an index into an 86-name table in the executable. The player turns that name into `name.vqa`, probes `outtakes\name.vqa`, and if that probe fails probes a directory plus the same filename. The Westwood MIX entry whose id is the hash of the winning path is the clip.

`tools/lol2_media_check.py --check` re-reads the table, the worked-example command and the two hashes. It writes nothing.

## Where the bytes live

`LOLG.DAT` in this note is the 1,977,007-byte image whose sha256 begins `b27a3534`. A code address in the instructions is a file offset minus `0x37000`. A data address in the instructions is a file offset minus `0x1C1024`. That second base is the one that lands the stem pointer `0x125F` on the text `ARENBAT1`.

The scene table is 86 little-endian dwords at file `0x1CF58C` (data `0xE568`). Each dword is the data offset of a short name. The limit dword at file `0x1CF764` (data `0xE740`) is 85. Ids 0 through 85 are accepted. The name at 85 is the placeholder `-----`.

The player is VA `0xCF2B4` (file `0x1062B4`). Its first argument is the scene id and its second argument is opcode 21's fifth byte. It rejects an id below 0 or above the limit dword. It then calls VA `0x15F4D6` with the name, the string `ss-` at data `0x2C84`, and the length 3. A zero return is the `ss-` path. Any other return builds `name.vqa` from the format at data `0x2C88` through VA `0x150158`, and calls the opener at VA `0xCF3C0` with that buffer and the fifth byte.

## The 86 names

CONFIRMED. Index is the scene id. Repeated names are stored twice.

| Id | Name | Id | Name | Id | Name |
| --- | --- | --- | --- | --- | --- |
| 0 | lolg | 29 | flood | 58 | bchm_apr |
| 1 | beli | 30 | gla_apr | 59 | e198e |
| 2 | sizzle | 31 | hv1-v-rl | 60 | drmrmapr |
| 3 | 0656001e | 32 | hvwm_apr | 61 | 0310919e |
| 4 | 1320516e | 33 | hw-brdge | 62 | 0311219e |
| 5 | 1372504e | 34 | larkvskn | 63 | 1380612e |
| 6 | 4025108e | 35 | liz-die | 64 | bc-vs-sb |
| 7 | a_cam | 36 | liz-die | 65 | bb_brth |
| 8 | arenaapr | 37 | ruin_app | 66 | ss-3e |
| 9 | b_cam | 38 | ss-10e | 67 | ss-8e |
| 10 | bst-die | 39 | ss-12e | 68 | ss-11e |
| 11 | bst-die | 40 | ss-1e | 69 | E232e |
| 12 | cem_apr | 41 | ss-2e | 70 | E233e |
| 13 | citadel | 42 | ss-4e | 71 | E242e |
| 14 | crazy | 43 | ss-5e | 72 | E243e |
| 15 | curse | 44 | ss-6e | 73 | E244e |
| 16 | door | 45 | ss-7e | 74 | luthrdie |
| 17 | dragon5 | 46 | ss-9e | 75 | 0656001e |
| 18 | dragon7 | 47 | stat_wlk | 76 | 1372504e |
| 19 | dragon8 | 48 | tavern | 77 | 0377804e |
| 20 | drgnflgt | 49 | tmpl_apr | 78 | 1386904e |
| 21 | e029e | 50 | tmplcr_e | 79 | 2730706e |
| 22 | e030e | 51 | tower_ap | 80 | 4025108e |
| 23 | e031e | 52 | voices | 81 | 1380612e |
| 24 | e032e | 53 | wrm_eat | 82 | 1320516e |
| 25 | e033e | 54 | wrm_stat | 83 | 0310919e |
| 26 | e125e | 55 | hut-fire | 84 | 0311219e |
| 27 | elevator | 56 | e068e | 85 | ----- |
| 28 | fishdeth | 57 | e069e |  |  |

## How opcode 21 reaches the player

CONFIRMED, two sites.

The high dispatcher compares the opcode at VA `0x649A9`. `cmp al, 0x15` / `jb` leaves opcodes below 21, and `jbe` enters VA `0x6486A` for opcode 21. That stub zero-extends byte 5, zero-extends byte 4, calls `0xCF2B4`, and returns 1. Bytes 1, 2 and 3 are not read.

Opcodes 1 through 24 also go through the low dispatcher at VA `0xB6B6E`. It decrements the opcode and jumps through `cs:[index*4 + 0x5C878]`. The dword `0x5C878` is not the file address of a pointer table. Adding `0x59024`, the same adjustment that turns the opcode 210 arm slots into code, lands on 24 dwords at VA `0xB589C`. Slot 20 (opcode 21) plus `0x59024` is VA `0xB5AB5`, and that code does the same push of byte 5, push of byte 4, and call to `0xCF2B4`.

Command stream 1 of `DAT/L12_CM.MIX` frames exactly when opcode 21 is 6 bytes long. The walk of that stream is the check, not a second reading of the length routine at VA `0x645E0`.

## Choosing the file

CONFIRMED up to the call that receives the name.

The opener keeps the filename in a stack buffer. Before the probes it calls VA `0x15C5CC` with the string `-NOWAITFULL` (data `0x2C91`) and clears one flag bit when that call returns nonzero. What the bit changes was not followed.

It then probes with VA `0x118934`:

1. Build `outtakes\%s` (data `0x2C9D`) and probe. A nonzero return keeps this name.
2. Otherwise build `%s\%s` (data `0x2CA9`). The first `%s` is the cstring at data `0x230C4`, which sits past the initialised image, so the file does not store it. The second `%s` is the filename. A nonzero probe keeps this name.
3. Otherwise write `outtakes\%s` (data `0x2CAF`) back into the buffer. There is no third probe.

VA `0xCF599` then calls VA `0x15DD84` with the buffer. At VA `0xCF5E1` the opener loads the fifth byte and branches on whether it is zero. The branch was not entered.

Names that start with `ss-` do not take this opener. The player copies the name from the fourth character, calls VA `0x153BB9` with that copy and the one-byte string `e` (data `0x2C8F`), then calls VA `0x1500D4` and VA `0x95E4C`. Both the `ss-` path and the `.vqa` path return through VA `0xCF36E`, which returns 0. The script stub has already decided to return 1.

## Worked example

CONFIRMED. `DAT/L12_CM.MIX` command stream 1, file offset 9823886:

```
15 03 78 00 0d 00
```

Opcode `0x15`, byte 1 is 3, bytes 2–3 are `0x0078`, byte 4 is 13, byte 5 is 0. Scene 13 is `citadel`, so the filename is `citadel.vqa`.

Both MIX hashes of `sphere2\l12_cm\citadel.vqa` are `0xA3C468EB`. That id is entry 21 of `DAT/L12_CMI.MIX`, 14,680,498 bytes. The entry begins `FORM` / `WVQA`. The `VQHD` chunk size is 42. Its first bytes are `02 00 01 00 4f 02 80 02 90 01 04 04 0f 08`: words 2, 1, 591, 640 and 400, then the bytes 4, 4, 15 and 8. [The VQA note](lol2-vqa-v2.md) reads those as version, a second word, frame count, width, height, 4×4 blocks, frame rate and the partial-codebook count. This pass re-read the bytes, not the header reader.

The same check on scene 0: the name is `lolg`, and the first probe builds `outtakes\lolg.vqa`. Both hashes are `0xB3593D3C`, entry 2 of `DAT/MOVIES.MIX`, 82,206,194 bytes, `VQHD` words 2, 3576, 640, 400. The bare name `lolg.vqa` is not an id in that archive. `MOVIES.MIX` has 29 entries. 28 begin with `FORM`. Entry 28 is 6,041 bytes and does not.

## What is still open

- Which instruction copies a level directory into data `0x230C4`. The citadel hash says the string that matches this install's archive is `sphere2\l12_cm`. It does not show the copy. What would settle it is a write of that address whose source is one of the `sphereN\l..\l..` strings.
- Which archives the probe at VA `0x118934` searches, and what VA `0x15DD84` does with the name.
- The `ss-` calls `0x153BB9`, `0x1500D4` and `0x95E4C`. The branch is measured. The value they produce is not.
- Opcode 21 byte 5 when it is not zero. The opener tests it at VA `0xCF5E1`. The worked example stores 0, and the other arm was not read.
