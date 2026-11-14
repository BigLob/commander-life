# Micro Center MTG restock monitor

Pushes to your phone when Magic: The Gathering products come into stock (or first get listed)
at your Micro Center. Runs on your **home PC**, not in the cloud: microcenter.com's Cloudflare
check blocks cloud servers, but a home connection in a normal Chrome usually passes.

Micro Center says trading card restocks go live in stores **Fridays at 10 AM** (when the vendor
ships), new launches are posted on the website as soon as they know, and the stores use the same
inventory as the site. So the monitor checks every 5 minutes on Fridays 9:45 to 11:00 AM and every
30 to 60 minutes the rest of the week.

Set up for **Micro Center Dallas** (`storeid=131`) and **all MTG** products, minus accessories
(sleeves, deck boxes, playmats, binders, dice) and other card games.

## Setup (Windows, once)

1. Install Python 3 from python.org (tick "Add python.exe to PATH").
2. Get this folder: download the repo
   (https://github.com/BigLob/commander-life/archive/refs/heads/main.zip), unzip, and open
   `tools\microcenter` in a terminal (in Explorer: click the address bar, type `cmd`, Enter).
3. Install Playwright:
   ```
   pip install playwright
   playwright install chromium
   ```
   It uses your installed Google Chrome if you have it (best for Cloudflare), else Playwright's Chromium.
4. On your Android phone, install **ntfy** from the Play Store.
5. Send a test push:
   ```
   python monitor.py --test
   ```
   The first run creates `config.json` and prints a random topic like `mc-mtg-3f9a1c2b7e40`.
   In the ntfy app tap **+**, enter that topic, Subscribe. Run `--test` again: the push should arrive.
   Keep the topic private; anyone who knows it can read and send to it.
6. First real check, with debug files:
   ```
   python monitor.py --once --debug
   ```
   It should print something like `57 products, 12 in stock: https://...` and push
   "Baseline recorded". The first run only records what's there; alerts start on the next run.
   If it says **0 products parsed** or **blocked**, send the newest files from `debug\`
   (an `.html` and a `.png`) to Claude so the parser can be fixed.

## Keep it running

**Simple:** leave a terminal open with `python monitor.py` (it loops on its own schedule).

**Task Scheduler** (starts with Windows, no window to keep open):
1. Open Task Scheduler → Create Task.
2. General: name it "Micro Center MTG", tick "Run only when user is logged on".
3. Triggers: New → At log on.
4. Actions: New → Program `pythonw`, arguments `monitor.py`, Start in: the full path of
   this `tools\microcenter` folder.
5. Settings: untick "Stop the task if it runs longer than".

`pythonw` hides the console; to see what it's doing, run `python monitor.py --once` by hand.

## What you'll get

- **Back in stock**: something that was sold out is in stock (name, price, stock count, store; tap to open).
- **New and in stock**: a product that wasn't on the page before, in stock.
- **New listing (not in stock yet)**: a new product posted, e.g. a launch or preorder. Turn these off
  with `"alert_new_listings": false`.
- **Monitor blocked**: Cloudflare showed its check. At most one push an hour; the monitor waits
  longer each time (30 min, 1 h, then 2 h) instead of retrying hard. If it keeps happening, set
  `"headless": false` in `config.json`, run `python monitor.py --once`, and click through the
  check in the window that opens. The cookie is kept in `profile\`, so later runs can go back to
  headless.

Alerts say when a product isn't Commander-legal (Un-sets like Unfinity, playtest cards) or isn't
released yet (preorders). Regular sealed product, Secret Lair and Universes Beyond are legal.

## config.json

| Field | What it does |
| --- | --- |
| `store_id` | Micro Center store. Dallas is 131; check by picking your store on microcenter.com and looking for `storeid=` in the address bar. Every watch URL gets this store. |
| `store_name` | Shown in alerts. |
| `watch_urls` | Pages to check (search or category pages). `{storeid}` is filled in. To watch something narrower, search on the site, set filters, and paste the address. |
| `include` / `exclude` | Product name must contain one `include` word and no `exclude` word (lowercase match). |
| `alert_new_listings` | Push for new products that aren't in stock yet. |
| `ntfy_topic`, `ntfy_server` | Where pushes go. |
| `headless`, `channel` | Browser settings (see "Monitor blocked"). |

Local files (not in git): `config.json`, `state.json` (what's been seen), `profile\` (browser
cookies), `debug\`.

## Tests

`python -m unittest test_monitor.py` checks the parser against `fixtures\search.html` (a made-up page
in Micro Center's result layout), the Cloudflare check against `fixtures\challenge.html`, the
filters, baseline, restock and dedupe logic, the blocked-push limit and the schedule.

## Not checked live

microcenter.com couldn't be reached from where this was built (Cloudflare blocks it), so the real
page layout, the Dallas store id and the `rpp=96` page size haven't been confirmed. The parser reads
each `li.product_wrapper` result's `data-name`/`data-price` attributes and its `SKU:` and stock text,
with fallbacks; if the real page differs, `--debug` files show what to fix.
