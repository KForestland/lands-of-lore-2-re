#!/usr/bin/env python3
"""Generate the LoL2 numeric reference from the retail program and MIX archives."""
from hashlib import sha256
from pathlib import Path
from struct import unpack_from

from cli_errors import run_cli, game_path
import lol2_cli
from lol2_entity_field_analyzer import LEVEL_FILES, RECORD_SIZE, locate_entity_table
from lol2_export_scripts import export
from lol2_item_labels import STRIDE, item_layout

PAGE = Path(__file__).resolve().parents[1] / "docs" / "NUMBERS.md"
SCHOOLS = 0x1CCB44
EFFECTS = 0x1CC980
CODE_BIAS = 0x37000
# (one-shot action, kept action), arm entry, form pushed (site of `push imm8`) or a description
FORM_ARMS = (((0x04, 0x3C), 0xD7F58, "0 when +5 is 0; otherwise `0xD6D2C`"),
             ((0x13, 0x3D), 0xD7FB7, "0–2 drawn; equal to form +0x1AB steps by one (2 wraps to 0), again while equal to +0x1AC"),
             ((0x15, 0x3F), 0xD803F, 0xD806C), ((0x16, 0x40), 0xD808F, 0xD80BC), ((0x17, 0x41), 0xD80DF, 0xD810B))
FORM_ACTIONS = {action for pair, _, _ in FORM_ARMS for action in pair}


def table(columns, rows):
    return "\n".join(["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
                     + ["| " + " | ".join(map(str, row)) + " |" for row in rows])


def native(image):
    if not sha256(image).hexdigest().startswith("b27a35341c6e877e"):
        raise ValueError("the report requires the documented English retail LOLG.DAT")
    schools, effects = [], []
    effect_rows = [image[EFFECTS + 4*i:EFFECTS + 4*i + 4] for i in range(113)]
    if EFFECTS + 4*113 != SCHOOLS:
        raise ValueError("effect records do not end at the school rows")
    reaches = []
    for i in range(15):
        at = SCHOOLS + 2*i
        first, count = image[at:at + 2]
        reaches.extend(range(first, first + count))
        costs = [effect_rows[j][0] for j in range(first, first + count)]
        schools.append((i, f"`+0x{at:X}`", first, count, ", ".join(map(str, costs)) or "—"))
    if reaches != list(range(113)):
        raise ValueError("spell school bytes do not cover effects 0–112")
    for i, (cost, xp, _, _) in enumerate(effect_rows):
        effects.append((i, f"`+0x{EFFECTS+4*i:X}`", cost, cost // 2, xp))
    selectors = []
    for (one_shot, kept), entry, form in FORM_ARMS:
        code = image[entry + CODE_BIAS:entry + CODE_BIAS + 12]
        if code != bytes.fromhex("BF01000000F6832802000010"):
            raise ValueError(f"form arm prologue missing at {entry:#x}")
        if isinstance(form, int):
            at = form + CODE_BIAS
            if image[at] != 0x6A:
                raise ValueError(f"form immediate missing at {form:#x}")
            form = f"{image[at + 1]} (`{form:#x}`)"
        for action, start, after in ((one_shot, entry, "cleared"), (kept, entry + 5, "kept")):
            if action_target(image, action) != start:
                raise ValueError(f"action {action:#x} does not enter {start:#x}")
            selectors.append((f"`{action:#04x}`", f"`{start:#x}`", form, after))
    return schools, effects, selectors


def action_target(image, action):
    """Follow the opcode 2 compare tree (`cmp ah, imm8` and conditional jumps) from 0xD84DF."""
    at, delta = 0xD84DF, None
    for _ in range(64):
        code = image[at + CODE_BIAS:at + CODE_BIAS + 6]
        if code[:2] == b"\x80\xFC":
            delta, at = action - code[2], at + 3
            continue
        if code[0] in (0x72, 0x74, 0x76, 0xEB):
            kind, size, target = code[0] & 0xF, 2, at + 2 + (code[1] ^ 0x80) - 0x80
        elif code[0] == 0x0F and code[1] in (0x82, 0x84, 0x86):
            kind, size, target = code[1] & 0xF, 6, at + 6 + int.from_bytes(code[2:6], "little", signed=True)
        elif code[0] == 0xE9:
            kind, size, target = 0xB, 5, at + 5 + int.from_bytes(code[1:5], "little", signed=True)
        else:
            return at
        taken = {2: delta < 0, 4: delta == 0, 6: delta <= 0, 0xB: True}[kind]
        at = target if taken else at + size
    raise ValueError("opcode 2 compare tree did not end")


def render(data):
    schools, effects, selectors = native(game_path(data.parent, "LOLG.DAT").read_bytes())
    begin, rows = item_layout(data)
    if len(rows) != 170:
        raise ValueError("expected 170 item records")
    items = []
    for index, row in enumerate(rows):
        descriptors = []
        for selector, a, b in (unpack_from("<BHH", row, 0x47 + 5*i) for i in range(4)):
            if selector or a or b:
                descriptors.append(f"{selector:02X}/{a:04X}/{b:04X}")
        items.append((index, f"`+0x{begin+STRIDE*index:X}`", f"`{unpack_from('<I', row, 0x18)[0]:08X}`",
                      f"`{row[0x3F]:02X}`", row[0x42], f"`{unpack_from('<H',row,0x3B)[0]:04X}`",
                      f"`{unpack_from('<H',row,0x3D)[0]:04X}`", row[0x44], " · ".join(descriptors) or "—"))
    creatures, form_calls = [], []
    for name in LEVEL_FILES:
        path = game_path(data, name)
        image = path.read_bytes()
        _, start, count = locate_entity_table(image, path.stem.upper())
        for slot in range(count):
            at = start + RECORD_SIZE * slot
            hp, = unpack_from("<H", image, at + 0x63)
            attack = image[at + 0x81]
            creatures.append((path.stem.upper(), slot, f"`+0x{at:X}`", hp, attack, max(1, attack // 10)))
        parsed = export(path)
        if parsed["unsupported"]:
            raise ValueError(f"{name}: unframed script bytes")
        for group in parsed["groups"]:
            for command in group["commands"]:
                if command["opcode"] != 2:
                    continue
                selector, operand = bytes.fromhex(command["raw_hex"])[4:6]
                if selector not in FORM_ACTIONS:
                    continue
                low, high = operand & 15, operand >> 4
                if selector in (0x04, 0x3C):
                    duration = "0" if operand == 0 else "`0xD6D2C` arm"
                else:
                    duration = f"{15*low}–{15*(low+high)}" if high else str(15*low)
                form_calls.append((path.stem.upper(), f"`+0x{command['file_offset']:X}`",
                                   f"`{selector:#04x}`", f"`{operand:#04x}`", duration))
    return "\n\n".join([
        "# LoL2 numbers at a glance",
        "Generated by `tools/lol2_numbers.py` from English retail files. Archive offsets are absolute. Code addresses use the executable page's analysis convention. [Address conventions](lol2-executable-tables.md)",
        "## Item combat inputs",
        "The 170 item rows of 91 bytes come from `GLOBAL.MIX` key `0xED7EC08D`: table offset at entry +4, count at +0x34. The mask and flags words at +0x3B and +0x3D reach the hit context through `0x89045–0x8916D`. Class, handler and strike countdown are bytes +0x3F, +0x42 and +0x44. The descriptor cells show nonzero +0x47 entries as hex triples in disk order. [Item format](lol2-item-format.md)\n\n**UNCONFIRMED.** A single armour or damage value per item cannot be assigned from these fields. The ordinary weapon path assembles the amount from player cells, and it uses difficulty and the target response. Trace each descriptor through the selection at `0x62E6B` to separate the contributions. [Item format and damage path](lol2-item-format.md#weapon-damage-path-vertical-slice-proven-where-marked)",
        table(("Row", "GLOBAL.MIX", "Identity +18", "Class", "Handler", "Hit mask", "Hit flags", "Strike ticks", "Nonzero descriptors"), items),
        "## Cast schools and effect costs",
        "There are 113 effect records: 64 costed levels in schools 0–12 and 49 zero-cost records in rows 13–14. The effect records at `LOLG.DAT+0x1CC980` end where the school rows at `LOLG.DAT+0x1CCB44` begin. A school row gives its first effect, and adding the zero-based charge selects the four-byte effect record. Byte +0 is the stored cost and +1 is the damage-feedback XP input. [Cast rules](lol2-spells.md#cast-tables-and-resource-costs)\n\n**UNCONFIRMED.** The +1 school byte is shown as stored; its use as a general charge bound is not proved. Trace the menu selection before `0xD0F4D` to check whether the picked row's +1 is read.",
        table(("School", "School row", "First effect", "School +1", "Stored costs"), schools),
        "The two debit columns show the stored cost and the form-2 halving at `0xD10D3–0xD10EB` if the cast reaches debit without equipment discounts. Admission, discounts and the debit flag have separate tests. [Mana debit and experience](lol2-spells.md)",
        table(("Effect", "LOLG.DAT", "Stored cost", "Form 2 debit", "XP input"), effects),
        "## Creature numbers by level",
        "The level ODF header supplies the offset at +0x10 and count at +0x48. Definitions have stride 147. The constructor reads +0x63 as the health cap (`0xA2197–0xA21A0`, `0xA7B8C`). Byte +0x81 is the attack input B, with `max(1, B/10)` computed at `0xA1D28–0xA1D46` by integer division. The profile, live mode and frame percentage then affect damage. [Creature attack](lol2-combat-ai.md#creature-state-and-attack-output)",
        table(("Level", "ODF slot", "MIX offset", "HP cap", "Attack B", "Attack floor"), creatures),
        "## Form requests",
        "Opcode 2 action byte +4 chooses a handler. [Opcode table](lol2-script-opcodes.md#opcode-table)\n\n**CONFIRMED.** The compare tree at `0xD84DF` sends ten actions into five form arms. Each arm starts with `mov edi, 1`. Actions 0x04, 0x13, 0x15, 0x16 and 0x17 enter at that instruction and set +4 to 0xFF after the request. Actions 0x3C, 0x3D, 0x3F, 0x40 and 0x41 enter five bytes later with `edi` 0 and leave +4 unchanged. Every arm first tests actor +0x228 bit 0x10. The arms for 0x15–0x17 and 0x3F–0x41 skip the request when form +0x1AB already equals the pushed form. Actions 0x04 and 0x3C with +5 zero call `0xD6B20` with form 0 and duration 0 (`0xD7F94–0xD7F97`). The duration helper at `0x649D8–0x64A22` splits +5 into low and high nibbles. With high nonzero it passes `15×low` and `15×(low+high)` to the RNG, otherwise it returns `15×low`. The tables list every stored opcode 2 command with one of these actions. The tool follows the compare tree for each action and checks each arm entry and form immediate.",
        table(("Action", "Arm entry", "Form request", "+4 after"), selectors),
        table(("Level", "MIX offset", "Action", "Operand +5", "Requested duration bounds"), form_calls),
    ]) + "\n"


def main():
    parser = lol2_cli.tool_args(__doc__, out_help="write the generated Markdown page")
    args = parser.parse_args()
    if args.check and args.out:
        parser.error("--check reads only")
    page = render(Path(args.data).resolve())
    if args.check:
        if PAGE.read_text(encoding="utf-8") != page:
            raise ValueError("docs/NUMBERS.md differs from the original tables")
        print("CHECK numbers: LoL2 tables match docs/NUMBERS.md")
    elif args.out:
        Path(args.out).write_text(page, encoding="utf-8")
    else:
        print(page, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
