from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.utils import showInfo
from aqt import gui_hooks
from anki.notes import Note
import json
from copy import deepcopy

# Use these variables to keep track of whether the card has actually changed
# Even though using the typing gui_hook should theoretically suffice for this,
# there is weird behavior w/ the "pop-up" current-card editor; the typing hook
# fires immediately upon opening/loading the card
note_fields_cached = None

def on_card_modified(note: Note):
    global note_fields_cached

    # https://forums.ankiweb.net/t/how-to-identify-editor-instance-in-editor-gui-hooks/1740/2
    if hasattr(mw.app.activeWindow(), "editor"):
        editor = mw.app.activeWindow().editor
    else:
        return

    # Ensure this is an AnkiHub note
    # NOTE: is there any better way to do this?
    if "ankihub_id" not in editor.note.keys():
        return

    focused_field_idx = editor.currentField

    tag = None
    if focused_field_idx == 0: # Text
        tag = "AnkiHub_Protect::Text"
    elif focused_field_idx == 1: # Extra
        tag = "AnkiHub_Protect::Extra"
    else:
        return

    # Ensure the user has actually changed the field
    # (see note above as for why this is necessary)
    if note_fields_cached[focused_field_idx] == editor.note.fields[focused_field_idx]:
        return
    note_fields_cached[focused_field_idx] = editor.note.fields[focused_field_idx]

    if tag and tag not in note.tags:
        note.addTag(tag)

    # derived from https://github.com/ankitects/anki/blob/64ca90934bc26ddf7125913abc9dd9de8cb30c2b/qt/aqt/editor.py#L592
    editor.web.eval(f'require("anki/ui").loaded.then(() => {{ setTags({json.dumps(note.tags)}); }})')

def cache_note_content_on_load(editor: Editor):
    global note_fields_cached
    note_fields_cached = deepcopy(editor.note.fields)

def init():
    global note_fields_cached
    note_fields_cached = None
    gui_hooks.editor_did_fire_typing_timer.append(on_card_modified)
    gui_hooks.editor_did_load_note.append(cache_note_content_on_load)

init()
