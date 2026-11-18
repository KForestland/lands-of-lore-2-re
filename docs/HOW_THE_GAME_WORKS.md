# How Lands of Lore II works

This guide follows the original DOS game from finding its files to saving your progress. The steps below describe confirmed behavior. Follow the links for examples and the original file offsets or program addresses behind each step.

## Starting up and finding files

The game keeps most of its files in MIX archives. Think of a MIX as a box with a directory at the front. Each directory entry gives a short numeric key, a position and a size. Each entry is found by a key computed from its name; the keys match the names the game uses (how the program searches the directory is still open).

The game uses separate archives for shared data, levels, rooms and media. When opening a room archive, it builds the filename from the selected room name. For instance, the room name `text_` becomes `text.mix`: the game cuts the name at the underscore and adds `.mix`.

Details and evidence. [MIX archives](formats/mix.md#layout) · [Room archive selection](lol2-room-archives.md)

## Loading a level

A level archive contains a map, a set of textures and records for things the player can encounter. The map gives the game points and regions bounded by those points. A region describes its floor and ceiling. An edge can link to another region through a portal, which is an opening the renderer can follow to draw what lies beyond it.

The texture bank supplies pictures for the level. The bank is stored in compressed blocks; once unpacked, it holds a palette and a list of images with their sizes. The map also places objects such as props, controls and creatures. Those placements tell the engine where it can find each object's event records.

Details and evidence. [Level header and object tables](lol2-level-script-format.md#header-fields-proven-by-consistent-reading-on-all-15-levels) · [Geometry and portals](formats/geometry.md#portals) · [Texture bank](lol2-level-texture-container.md#lzo1x-block-layout-proven)

## Running scripts

Object and region event records connect something that happens to a list of commands. For example, moving across a region boundary sends one event to the previous region and another to the new one. A record may include a predicate, which is a test the game checks before running the commands. A predicate can compare a shared state value with a number.

Some objects have countdown timers. The engine reduces the countdown by the elapsed amount and can run a command list when it expires. Each command starts with an opcode, a number that tells the engine what operation to perform and how to read the remaining bytes. The original command lengths frame all 15 levels' script streams.

Details and evidence. [Events and timers](lol2-script-events.md) · [Shared state tests](lol2-script-events.md#predicates-and-shared-bytes) · [Opcode table and disassembler](lol2-script-opcodes.md)

## Picking up and using items

An item definition describes a kind of item. A live item points to its definition and carries its own changing data, such as the charges on certain items. A script can grant an item by ID and set the starting value of its instance byte.

When an item is used, its definition selects a handler, a small routine in the executable. The handler also sees what kind of action prompted the request. Swinging a weapon, using an item in the hand, and being told it was equipped or taken off each have their own action number. The same item can therefore behave differently depending on the action.

Details and evidence. [Item grants and instances](lol2-item-effects.md) · [Use and equipment handlers](lol2-item-handlers.md)

## Learning and casting spells

Some scroll handlers call the lesson routine after taking the item from the hand. The lesson code examines the known-school list. If the school is not known yet, the game sends a message, and the handler for that message adds the school to the list.

When you cast, the game combines the selected school and charge level to find an effect and read its cost. The resource check and the eventual debit have separate rules. For example, the player's current form can change the debit. The selected effect then runs its own routine. Some effects create a hit request for the combat code.

Details and evidence. [Acquisition and cost](lol2-spells.md) · [Player effect routines](lol2-spell-dispatch.md)

## Creature decisions and combat

A creature has a current behavior, which selects the part of its update routine that runs. That code can check observations and other conditions, update the behavior and choose an animation. Tracing these changes shows which behaviors can follow one another.

An attack packages the attacker, target and starting amount into a hit request. The receiver applies the original difficulty rules and damage modifiers, then updates health. A hit can also match an object's script record. That lets an object's script react to damage as well as to ordinary interactions.

Details and evidence. [Creature decisions](lol2-creature-transitions.md) · [Observations](lol2-creature-observation.md) · [Hit processing and scripted reactions](lol2-combat-ai.md)

## Playing movies and sound

A script can ask for a movie by scene number. The game looks up the scene name and tries a VQA filename. The VQA format stores small pieces of picture data in a codebook. A frame can refer to those pieces, and later frames can supply a new book.

Scripts can also send sound cue IDs to the sound player. A music command selects the short name of a track. The music builder adds `.AUD` for digital music or `.HMI` for MIDI music, depending on a setting.

Details and evidence. [Movie scenes](lol2-movie-scenes.md) · [VQA frames](formats/vqa.md) · [Sound cues](lol2-sound-cues.md) · [Music selection](lol2-music-selection.md)

## Saving and loading

A save slot begins with its display name, version stamps and a directory of positions. That directory points to a compressed preview, game-wide data and separate blocks for levels. Two directory entries can point to the same place to describe an empty section.

Some sections preserve things that have changed while you played. The save has sections for live items and where they are placed, along with separate level state. When the game loads a slot, it checks version stamps before restoring the data.

Details and evidence. [Native save slots and version checks](lol2-save-format.md) · [Save sections and item placement](lol2-save-sections.md#items-and-occupancy)
