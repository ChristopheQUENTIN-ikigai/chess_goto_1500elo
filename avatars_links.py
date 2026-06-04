"""
avatars_links.py — User-editable mapping of master / player names to
avatar image filenames.

This file is intentionally plain data so non-programmers can add new
entries without having to touch the rendering code.

Usage
-----
1. Drop your image file into  ./assets/textures/avatars/
   (PNG / JPG / JPEG all work).
2. Add one line to the AVATAR_FILES dict below:

       "Some Player":  "SomePlayer.jpg",

   The key is the **exact player name** as it appears in the
   master_games.py records (e.g. "Garry Kasparov", not "Kasparov").
   The value is the **bare filename** relative to
   ./assets/textures/avatars/.

3. Save, relaunch the game. The avatar will appear next to the
   player's name in both the master-games browser and the in-game
   avatar cards.

Fallbacks
---------
When a name is not in this dict, the resolver still tries:
  - sanitized-name.{png,jpg,jpeg}   (e.g. "Bobby_Fischer.png")
  - raw-name.{png,jpg,jpeg}          (e.g. "Fischer.jpg")
  - last-token.{png,jpg,jpeg}        (e.g. "Fischer.jpg" from "Bobby Fischer")
So casual drop-ins keep working even without editing this file.

Adding a new master / player
----------------------------
Just add the key/value pair. No code change needed. Example:

    "Hikaru Nakamura":  "Nakamura.jpg",
    "Ding Liren":       "DingLiren.png",
"""

# Map: player name (str) → filename inside ./assets/textures/avatars/
AVATAR_FILES: dict[str, str] = {
    # ── Classical-era ────────────────────────────────────────────────
    "Jose Raul Capablanca": "Capablanca.jpg",
    "Mikhail Tal":          "Mikhail_Tal.jpg",
    "Anatoly Karpov":       "Karpov.jpg",
    "Bobby Fischer":        "Fischer.jpg",
    "Garry Kasparov":       "Kasparov.jpg",

    # ── v10: Modern players newly featured ────────────────────────────
    # Anand has a portrait file; Polgar and Ashley fall back to a
    # deterministic initials disc until you drop a file in
    # ./assets/textures/avatars/ matching one of these names. The
    # filesystem resolver in avatar_gen.py also picks these up
    # automatically when the file appears, so editing this map is
    # only required if you want a name that doesn't sanitise to the
    # filename you have on disk.
    "Viswanathan Anand":    "Viswanathan_Anand.png",
    # "Judit Polgar":       "Judit_Polgar.png",
    # "Maurice Ashley":     "Maurice_Ashley.png",

    # ── Entries ready to be filled in by the user ────────────────────
    # Drop a matching image file into ./assets/textures/avatars/ and
    # add the filename here. Until then, these players show a
    # deterministic initials disc (still perfectly readable in the
    # UI — the disc is generated on first use and cached to disk).
    #
    # "Boris Spassky":        "Spassky.jpg",
    # "Vasily Smyslov":       "Smyslov.jpg",
    # "Veselin Topalov":      "Topalov.jpg",
    # "Viswanathan Anand":    "Anand.jpg",
    # "Magnus Carlsen":       "Carlsen.jpg",
    # "Sergey Karjakin":      "Karjakin.jpg",
    # "Donald Byrne":         "Byrne.jpg",
    # "Savielly Tartakower":  "Tartakower.jpg",
    # "Wolfgang Unzicker":    "Unzicker.jpg",
}


def get_avatar_filename(name: str) -> str | None:
    """Return the filename registered for `name`, or None if the name
    is not in the mapping. The resolver in avatar_gen.py uses this as
    its highest-priority lookup, and falls back to filesystem
    heuristics when this returns None."""
    return AVATAR_FILES.get(name)
