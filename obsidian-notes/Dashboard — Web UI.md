# Dashboard — plain English

[[Network-Tools-Dashboard/START HERE]] · [[Beyond the browser]]

---

### When it’s awake

Bookmark: [http://127.0.0.1:5050](http://127.0.0.1:5050)

### Wake it manually

Adjust the path—you might have cloned into a differently named folder.

```bash
cd /path/to/network-tools-dashboard
./start.sh
```

Hand-rolled activate:

```bash
cd /path/to/network-tools-dashboard
source .venv/bin/activate
python server.py
```

Different listener:

```bash
PORT=8080 python server.py
```

---

### Tabs in human words

That left rail is simpler than enterprise dashboards on purpose:

| Tab | Feeling | Rough API |
|-----|---------|-----------|
| **Domain Check** | “Does DNS answer, and does HTTP/HTTPS shrug or reply?” | `POST /check` |
| **Network Commands** | Your familiar CLI friends without jumping terminals | `POST /network-command` |
| **IP Check** | “Where-ish is this IP, who-ish owns the netblock?” thanks to ipinfo | `POST /ip-lookup` |
| **SSL Cert Check** | Leaf cert fingerprints and dates on a platter | `POST /ssl-check` |

External vs Internal toggles resolver flavor on supported paths—same spirit as the optional helper’s **`scope`** flag when you wire it.

IPv6 pasted into **Network Commands** routes through kinder primitives when possible (**PTR digs**, **`ping6`**, **`nmap -6`**). Bracket literals and stray zone suffixes handled conservatively (`[addr]`, strip `% iface` bits where tools would choke).

---

### Before handing it wifi credentials

Seriously read **`INTERNAL-SETUP.txt`**. localhost first, campfire stories later.

---

### Nearby notes

[[Network-Tools-Dashboard/START HERE]] · [[Beyond the browser]]
