# Beyond the browser

Sometimes you rehearse lookups where you edit code—not only where you click tabs. Think of **`network_tools_mcp_server.py`** as a **quiet backstage pass** into the exact **`server.py`** routes the webpage already exposes.

Touches base with **`[[START HERE]]`** · **`[[Dashboard — Web UI]]`**

---

### What quietly happens

Editors that support **attached helper scripts over stdio** can launch that Python sibling with roughly this recipe (paths mirror your checkout):

```json
{
  "mcpServers": {
    "network-tools-dashboard": {
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["network_tools_mcp_server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

The repo ships the same snippet as **`editor-config/mcp-servers.example.json`** — merge per your toolchain’s instructions, tweaking only when **`python`** paths differ outside **`.venv`**. Keep stray shell scribbles elsewhere; broken JSON sabotages unrelated helpers parked in manifests you never intend to publish.

Human-facing labels differ from gutsy internals—settings screens sometimes prepend random prefixes (**`project-0-…`**) while still mapping to **`network-tools-dashboard`** when things work.

Most routed calls reuse Flask internally—spinning `./start.sh` stays optional unless the browser screams **Failed to fetch**, which only listens when something truly needs HTTP sockets.

Install stack when you flirt with this pathway:

```bash
pip install -r requirements-mcp.txt
```

---

### Routed knobs (technical labels)

Tiny cheat sheet—you can skim past entirely if webpages answer every itch:

| Routed label | Loose meaning |
|-----------------|----------------|
| **network_lookup_smart** | Shoves mixed inputs toward IP vs **`host:port`** vs hostname; optional shell bundles (`dig`, `all`, …). |
| **start_network_dashboard** | Background `./start.sh` analogue; politely stops if localhost already chirps answers. Optional browser pop if your editor exposes it. |
| **domain_check** | Domain tab analogue; **`scope`** toggles resolver flavor (**external/internal** vibe). |
| **network_commands** | Commands-tab analogue (**`target`**, **`command`**, **`scope`**). IPv6 plumbing mirrors Flask quality-of-life tweaks. |
| **ip_geo_lookup** | IP tab analogue (ipinfo JSON). |
| **ssl_certificate_inspect** | SSL tab analogue; lists or commas; optional **`:port`**. |

---

### Token shelf when **network_lookup_smart** sorts input

| Token flavor | Route flavor |
|--------------|--------------|
| IPv4 / IPv6 literal | IP lookup family |
| Looks like **`host:port`** (not “just colons in IPv6”) | Certificate peek family |
| Hostname / domain | Domain tab family |
| **`extras_command` ≠ none** | Also funnels through **Network Commands** caps inside code |

---

### When you still fire up HTTP

| Feeling | Companion alone suffices? |
|---------|------------------------------|
| “Answer me lookups while I type” | Often **yes**—Flask listens only inside memory |
| “I crave real tabs / previews” | `./start.sh` or **start_network_dashboard** analogue |
| “Browser cries **Failed to fetch**” | Something must listen publicly again |

Related files sprinkled through repo roots: **`network_tools_mcp_server.py`**, **`server.py`**, **`README.md`**, **`INTERNAL-SETUP.txt`**.
