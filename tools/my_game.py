"""Make an offline guide from a player's copy of Lands of Lore II."""
from cli_errors import game_path
from edition import identify, WITNESSES
from game_names import creature_label, creature_roles, creature_tags, level_names, spell_names
from level_html import find_data
from lol2_item_labels import display_names
from lol2_level_report import level_files
from lol2_level_schematic import draw, load
from lol2_progression import collect, selectors
from lol2_save_writer import parse_slot
from my_game_ui import DATA_ERRORS, MyGame, catalogue, edition_label, png_bytes, report


TITLE = "Lands of Lore II · My Game"

# Landmarks and script branches documented in PROGRESSION.md and the level notes.
EXIT_ACTIONS = {
    **{("L1_DC", f"region {region}"): "Cross the bridge, open the door at the far end and walk into the passage."
       for region in (1190, *range(1217, 1225))},
    ("L1_DC", "prop:447"): "Wait for the exit scene to finish.",
    ("L3_DH", "control:82"): "Open the bars with the wall switch, then walk through to the glowing mirror.",
    ("L4_HJ", "region 2809"): "Walk into the cave mouth beyond the thorn maze and the oil pool.",
    ("L4_HJ", "region 2604"): "Take the low passage into the cave if your current form fits.",
    ("L8_SJ", "prop:1198"): "Enter the temple approach.",
    ("L14_HT", "prop:170"): "Use either exit control with an empty hand.",
}
EXIT_CONDITIONS = {
    ("L1_DC", "(local 2 == 5)"): "Progress in the guard encounter chooses this version of the exit scene.",
    ("L3_DH", "(object+0x25 == 3)"): "The approach scene has to start. Its exact trigger is still open.",
    ("L17_HC", "(object+0x25 == 1)"): "The exit object has to be ready. What activates it afterward is still open.",
}


def exit_rows(data, names, level=None):
    rows, _ = collect(data)
    arrivals, _ = selectors(rows)
    for index, (source, target, entry, _, _, _, guard, owner, event_id) in enumerate(rows):
        if level is not None and source != level:
            continue
        action = EXIT_ACTIONS.get((source, owner))
        if action is None:
            action = ("Walk across the exit area." if event_id in (2, 4)
                      else "The action that starts this exit is still unknown.")
        if index in arrivals:
            condition = "Your earlier progress selects this version of the route."
        elif guard == "none":
            condition = "No extra condition."
        else:
            condition = EXIT_CONDITIONS.get((source, guard), "This path opens after an earlier step in the area.")
        yield names.get(source, source), names.get(target, target), entry, action, condition, owner


def game_page(folder):
    data = find_data(folder, "DAT", "L1_DC.MIX")
    names = level_names(data)
    items = display_names(data)
    spells = spell_names(data)
    if not names or not items or not spells:
        raise ValueError("missing game name tables")
    edition = edition_label(data, identify, WITNESSES, "DOS layout (exact version unverified)")

    roles = creature_roles(data)
    maps, creatures = [], []
    for stem in level_files(data):
        name = names.get(stem, stem)
        image, _, _ = draw(name, *load(data, stem), None, None, 700)
        maps.append((stem, name, png_bytes(image), "png"))
        archive = game_path(data, f"{stem}.MIX").read_bytes()
        creatures.extend((creature_label(tag, roles), name, tag, slot)
                         for slot, tag in creature_tags(archive, stem).items())

    tables = (
        ("items", "Items", catalogue("items", "Items", ("Name",), ((name,) for name in sorted(items.values(), key=str.casefold)))),
        ("spells", "Spells", catalogue("spells", "Spells", ("Spell school", "Number"), ((name, slot) for slot, name in spells.items()))),
        ("creatures", "Creatures", catalogue("creatures", "Creatures", ("Name or label", "Area", "File label", "Definition"),
                                             sorted(creatures, key=lambda row: (row[0] == "—", row[0].casefold(), row[1:])),
                                             "Names come from the cast credits. The table displays simple file labels "
                                             "in title case and shows a dash when only a file code is available.")),
    )
    heading = "Why can't I leave?"
    exits = catalogue("exits", heading, ("From", "To", "Arrival", "What to do", "When it works", "File record"),
                      exit_rows(data, names),
                      "One line per exit record. Several records can lead through the same passage. "
                      "Where the exact steps are unknown, the file record identifies the exit.")
    return report(TITLE, edition, maps, tables, extras=(("exits", heading, exits),))


def saved_page(source, folder):
    try:
        slot = parse_slot(source.read_bytes())
        level, x, y, heading, _ = slot.state[-5:]
    except DATA_ERRORS as error:
        raise ValueError("Choose an original Lands of Lore II DOS 1.30 saved game.") from error

    try:
        data = find_data(folder, "DAT", "L1_DC.MIX")
        stem = next(stem for stem in level_files(data) if stem.split("_", 1)[0] == f"L{level}")
        names = level_names(data)
        name = names.get(stem, stem)
        geometry = load(data, stem)
        exits = list(exit_rows(data, names, stem))
    except (*DATA_ERRORS, StopIteration) as error:
        raise ValueError("Choose the Lands of Lore II folder containing the level in this saved game.") from error

    plan, _, _ = draw(name, *geometry, None, None, 900, player=(x, y, heading))
    image = (stem, name, png_bytes(plan), "png")
    heading &= 0xFFFF
    facts = catalogue("save", "Save summary for a bug report", ("Field", "Value"),
                      (("Level", f"{name} ({level})"), ("X", x / 65536), ("Y", y / 65536),
                       ("Facing (game units)", heading)),
                      "Copy these values into the issue if you report a fault. The page omits unconfirmed save fields.")
    routes = catalogue("exits", "Exits from this level", ("From", "To", "Arrival", "What to do", "When it works", "File record"),
                       exits, "The plan uses the saved position and facing. Exit conditions describe the game scripts.")
    return report(f"{TITLE} · You are here", "DOS 1.30 saved game", (image,), (),
                  extras=(("save", "Save summary", facts), ("exits", "Exits from this level", routes)))


app = MyGame("LoL2 My Game", TITLE, "Lands of Lore II", "DAT", game_page, read_saved=saved_page)


if __name__ == "__main__":
    raise SystemExit(app.main())
