from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.utils import showInfo, tooltip
from aqt import gui_hooks
from anki.notes import Note
import json
from copy import deepcopy

# Use these variables to keep track of whether the card has actually changed
# Even though using the typing gui_hook should theoretically suffice for this,
# there is weird behavior w/ the "pop-up" current-card editor; the typing hook
# fires immediately upon opening/loading the card
note_fields_cached = None

# Cache the editor object upon loading the note since the user can sometimes
# close the editor quickly, before on_card_modified is run
editor_cached = None

def on_card_modified(note: Note):
    global note_fields_cached, editor_cached

    if note_fields_cached is None or editor_cached is None:
        raise Exception("Failed to automatically add AnkiHub_Protect tags due to unexpected error! Please try again.")

    # Ensure this is an AnkiHub note
    # NOTE: is there any better way to do this?
    if "ankihub_id" not in note.keys():
        return

    focused_field_idx = editor_cached.currentField
    if focused_field_idx is None:
        return

    # Ensure the user has actually changed the field
    # (see above as for why this is necessary)
    if note_fields_cached[focused_field_idx] == note.fields[focused_field_idx]:
        return
    note_fields_cached[focused_field_idx] = note.fields[focused_field_idx]

    # Can remove "field_name in" check to expand auto-protection to all note fields
    field_name = note.keys()[focused_field_idx]
    tag = f"AnkiHub_Protect::{field_name}"
    if tag in note.tags:
        return
    if field_name in ("Text", "Extra"):
        note.addTag(tag)
        editor_cached._save_current_note()

    # derived from https://github.com/ankitects/anki/blob/64ca90934bc26ddf7125913abc9dd9de8cb30c2b/qt/aqt/editor.py#L592
    editor_cached.web.eval(f'require("anki/ui").loaded.then(() => {{ setTags({json.dumps(note.tags)}); }})')

    # Notify user
    tooltip(f"Added tag '{tag}'", period=1500)

def cache_objects_on_load(editor: Editor):
    global note_fields_cached, editor_cached

    # https://forums.ankiweb.net/t/how-to-identify-editor-instance-in-editor-gui-hooks/1740/2
    if hasattr(mw.app.activeWindow(), "editor"):
        editor_cached = mw.app.activeWindow().editor
    else:
        return

    note_fields_cached = deepcopy(editor_cached.note.fields)

def init():
    global note_fields_cached, editor_cached
    note_fields_cached = None
    editor_cached = None
    gui_hooks.editor_did_fire_typing_timer.append(on_card_modified)
    gui_hooks.editor_did_load_note.append(cache_objects_on_load)

init()
