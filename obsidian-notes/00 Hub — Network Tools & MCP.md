# Network Tools — notebook hub

This folder is intentionally written like **notes**, not specs. Flip between the two linked sheets below—the tone matches.

---

### Jump links inside this folder

- [[Dashboard — Web UI]]
- [[MCP Server — Cursor reference]]

---

### Open the dashboard in a browser

[http://127.0.0.1:5050](http://127.0.0.1:5050)

Kick off `./start.sh` (repo root), *then* open that link—or you’ll stare at silence.

---

### Keeping these notes beside Obsidian

Obsidian happily reads Markdown anywhere on disk—no plugin ceremony required here.

Pick whichever habit feels natural:

| Habit | What it looks like |
|-------|---------------------|
| **Symlink this folder into a vault** | One command, no duplication. Edits anywhere show up instantly. Example:  
`ln -s /FULL/PATH/network-tools-dashboard/obsidian-notes /FULL/PATH/your-vault/Network-Tools-dashboard` |
| **Copy instead** | Drop the **`obsidian-notes`** folder under any vault subdirectory; merge later manually if README changes. |
| **Open this repo in Obsidian wholesale** | “Open folder as vault” on **`obsidian-notes`**—good if Obsidian-only that day |

If you symlink, give the sibling folder whatever title you prefer in your vault—“Network Stuff”, “Toolbox”, whatever reads well to morning-you.

---

### Two doors, same room

You can click through the Flask UI tabs *or* let Cursor MCP call the backing routes—you’re touching the same Python surface either way:

| Preference | Everyday flow |
|-----------|----------------|
| **Browser-first** | `./start.sh` → tabs → done |
| **Editor-first / chat** | Leave MCP wired; lookups often ride Flask’s test helpers without spawning the listener |
| **Both** | Use **`start_network_dashboard`** MCP (or `./start.sh`) when the browser screams “Failed to fetch” |

Technical deep dive on MCP names / routes → [[MCP Server — Cursor reference]].

---

Further reading bundled with the repo:

- **`INTERNAL-SETUP.txt`** — DNS scope quirks, seriousness about exposure  
- **`README.md`** — friendlier onboarding + Cursor wiring  
