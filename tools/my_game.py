"""Make an offline guide from a player's copy of Lands of Lore II."""
import re

from cli_errors import game_path
from edition import identify, WITNESSES
from game_names import creature_tags, level_names, spell_names
from level_html import find_data
from lol2_item_labels import display_names
from lol2_level_report import level_files
from lol2_level_schematic import draw, load
from lol2_progression import collect, selectors
from my_game_ui import MyGame, catalogue, edition_label, png_bytes, report


TITLE = "Lands of Lore II · My Game"

# These are the four trigger gaps documented in PROGRESSION.md.
OPEN_TRIGGERS = {("L9_DR", "prop:104"), ("L12_CM", "control:74"),
                 ("L16_CA", "control:74"), ("L17_HC", "movable:50")}
COMPARISONS = {"==": "is", "!=": "is not", "<=": "is at most", ">=": "is at least",
               ">": "is above", "<": "is below"}
OBJECT_EXITS = {
    ("L1_DC", "prop:447"): "Wait for the exit scene to finish.",
    ("L3_DH", "control:82"): "Go through the bars and approach the glowing mirror. The exact scene callback is still open.",
    ("L8_SJ", "prop:1198"): "Enter the temple approach.",
    ("L14_HT", "prop:170"): "Use either exit control with an empty hand.",
}


def readable_guard(guard):
    guard = guard.replace("object+0x25", "the object's state")
    guard = re.sub(r"\blocal (\d+)", r"area marker \1", guard)
    guard = re.sub(r"\bshared (\d+)", r"story marker \1", guard)
    return re.sub(r"(?<= )(==|!=|<=|>=|>|<)(?= )", lambda match: COMPARISONS[match[0]], guard)


def exit_rows(data, names):
    rows, _ = collect(data)
    arrivals, _ = selectors(rows)
    for index, (source, target, entry, _, _, _, guard, owner, event_id) in enumerate(rows):
        if event_id in (2, 4):
            action = f"Enter {owner}."
        elif (source, owner) in OPEN_TRIGGERS:
            action = "Open question: the action that starts this exit is still unknown."
        else:
            action = OBJECT_EXITS.get((source, owner), "Open question: the action that starts this exit is still unknown.")
        condition = "No extra condition on this exit."
        if guard != "none":
            condition = readable_guard(guard)
            if index in arrivals:
                condition += " This chooses the arrival when the exit runs."
            else:
                condition = "Requires " + condition + "."
        yield names.get(source, source), names.get(target, target), entry, action, condition


def game_page(folder):
    data = find_data(folder, "DAT", "L1_DC.MIX")
    names = level_names(data)
    items = display_names(data)
    spells = spell_names(data)
    if not names or not items or not spells:
        raise ValueError("missing game name tables")
    edition = edition_label(data, identify, WITNESSES, "DOS layout (exact version unverified)")

    maps, creatures = [], []
    for stem in level_files(data):
        name = names.get(stem, stem)
        image, _, _ = draw(name, *load(data, stem), None, None, 700)
        maps.append((stem, name, png_bytes(image), "png"))
        archive = game_path(data, f"{stem}.MIX").read_bytes()
        creatures.extend((tag, name, slot) for slot, tag in creature_tags(archive, stem).items())

    tables = (
        ("items", "Items", catalogue("items", "Items", ("Name",), ((name,) for name in sorted(items.values(), key=str.casefold)))),
        ("spells", "Spells", catalogue("spells", "Spells", ("Spell school", "Number"), ((name, slot) for slot, name in spells.items()))),
        ("creatures", "Creatures", catalogue("creatures", "Creatures", ("Name in the game files", "Area", "Definition"),
                                             sorted(creatures), "These labels come from the stored creature definitions.")),
    )
    heading = "Why can't I leave?"
    exits = catalogue("exits", heading, ("From", "To", "Arrival", "What starts it", "Condition"),
                      exit_rows(data, names),
                      "One line per exit in the game files. The area and story markers record game progress. "
                      "Some still have an open question about what sets them.")
    return report(TITLE, edition, maps, tables, extras=(("exits", heading, exits),))


app = MyGame("LoL2 My Game", TITLE, "Lands of Lore II", "DAT", game_page)


if __name__ == "__main__":
    raise SystemExit(app.main())
