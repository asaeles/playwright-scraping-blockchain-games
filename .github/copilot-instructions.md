# Copilot Instructions for Playwright Blockchain Games Scraper

## Project Overview

**Purpose:** Web scraper for extracting game data from PlayToEarn.com using Playwright for dynamic content rendering and BeautifulSoup for HTML parsing.

**Entry Point:** `src/scraper.py` (204 lines)

**Output:** CSV file in `output/` directory with scraped game data (titles, genres, scores, status)

**Tech Stack:** Python, Playwright, BeautifulSoup4, asyncio

---

## Critical Architecture Pattern: Page Pool for Concurrency

This project uses a **page pool pattern** with async context managers for efficient, concurrent web scraping. This is the key architectural decision.

### How It Works

**Page Pool Creation** (`build_page_pool(browser, size)`):
```python
async def build_page_pool(browser, size: int):
    """
    Create `size` independent Pages under separate contexts (JS disabled).
    Returns (page_slots, queue) where:
      - page_slots is a list of dicts with {'id', 'page', 'context'}
      - queue is an asyncio.Queue prefilled with these slots for reuse
    """
    page_slots = []
    q = asyncio.Queue()
    for i in range(size):
        ctx = await browser.new_context(java_script_enabled=False)
        page = await ctx.new_page()
        slot = {'id': i + 1, 'page': page, 'context': ctx}
        page_slots.append(slot)
        await q.put(slot)
    return page_slots, q
```

**Usage Pattern** (Borrow/Return):
```python
# Acquire page from pool
slot = await acquire_page(page_queue)
page = slot['page']

# Use page
await page.goto(url)

# Return to pool
release_page(page_queue, slot)
```

**Benefits:**
- **Memory efficiency:** N persistent pages instead of spawning/destroying browsers
- **Isolated state:** Each page lives in its own context (no JS pollution between requests)
- **True concurrency:** Multiple pages can scrape different URLs simultaneously
- **Async-friendly:** Integrates seamlessly with `asyncio`

---

## Key Configuration

Located at top of `src/scraper.py`:

```python
MAX_PAGES = 8        # Concurrency level: number of persistent Page objects in pool
TOTAL_PAGES = 61     # Total number of site pages to scrape (e.g., pagination)
```

**Tuning Guide:**
- **`MAX_PAGES`:** Increase for faster scraping (CPU/network permitting); start at 4-8
- **`TOTAL_PAGES`:** Adjust based on actual site pagination or test range

---

## Output Path Handling

The project calculates output directory independently of run location:

```python
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'output'
)
```

**Why this matters:**
- Goes up from `src/scraper.py` → project root
- Works regardless of current working directory
- Automatically creates `output/` if it doesn't exist

---

## Scraping Logic

### Per-Page Scraping (`scrape_site_page_with(page_slot, page_num)`):

1. Navigate to page URL (with 60-second timeout)
2. Query CSS selector for game table: `tbody.__TableItemsSwiper`
3. Extract HTML and parse with BeautifulSoup
4. Iterate through table rows (`<tr>`) and extract game data
5. Return results list

### Data Extraction:
- **Selectors used:** CSS selectors for game rows, titles, genres, scores, status
- **Parser:** BeautifulSoup with lxml backend
- **Error handling:** Continues on missing table; logs warnings

### Main Concurrency Loop:
```python
# Create pool
page_slots, page_queue = await build_page_pool(browser, MAX_PAGES)

# Create tasks for all pages
tasks = []
for page_num in range(1, TOTAL_PAGES + 1):
    task = scrape_site_page_with(acquire_page(page_queue), page_num)
    tasks.append(task)

# Run concurrently
results = await asyncio.gather(*tasks)

# Cleanup
await close_page_pool(page_slots)
```

---

## Project Structure

```
blockchain-games/
├── src/
│   └── scraper.py              # Main scraper (204 lines)
├── output/                      # Generated CSV (git-ignored)
├── requirements.txt             # Dependencies
├── .github/
│   └── copilot-instructions.md  # This file
├── Dockerfile                   # Container definition
├── entrypoint.sh                # Container entry script
└── README.md
```

---

## Development Workflows

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers (required for first run):
   ```bash
   playwright install
   ```

3. Run scraper:
   ```bash
   python src/scraper.py
   ```

### Local Testing

- **Test single page:** Change `TOTAL_PAGES = 1` in `src/scraper.py`
- **Check output:** Verify CSV structure in `output/games.csv`
- **Debug selectors:** Add temporary `print()` statements in `scrape_site_page_with()`

### Docker Execution

```bash
docker build -t blockchain-scraper .
docker run --rm -v $(pwd)/output:/app/output blockchain-scraper
```

---

## Debugging Checklist

| Issue | Solution |
|-------|----------|
| `table = await page.query_selector(...)` returns None | Site structure changed; inspect `playtoearn.com` and update selector |
| Script hangs on `page.goto()` | Network timeout; increase timeout in `scrape_site_page_with()` (e.g., `timeout=120000`) |
| Memory bloat with high `MAX_PAGES` | Reduce `MAX_PAGES` (e.g., 4-6 instead of 8) or add cleanup between batches |
| CSV missing data | Check BeautifulSoup selector strings match actual HTML (vary selector specificity) |
| JavaScript-heavy content missing | By design, JS is disabled (`java_script_enabled=False`). If needed, set to `True` in `build_page_pool()` |

---

## Common Modifications

### Adjust Concurrency
```python
MAX_PAGES = 4  # Conservative: 4 concurrent pages
```

### Enable JavaScript (for dynamic content)
In `build_page_pool()`:
```python
ctx = await browser.new_context(java_script_enabled=True)  # Changed from False
```

### Add Retry Logic for Failed Pages
Wrap `scrape_site_page_with()` call in try/except:
```python
try:
    await scrape_site_page_with(acquire_page(page_queue), page_num)
except Exception as e:
    print(f"Page {page_num} failed: {e}")
    # Could add to retry queue
```

### Export to Different Format
Modify CSV writer to support JSON:
```python
import json
with open('output/games.json', 'w') as f:
    json.dump(all_games, f, indent=2)
```

### Scrape Different Site
1. Update `page.goto(url)` with new target URL
2. Inspect new site's HTML for game table selector
3. Update `query_selector()` and BeautifulSoup parsing logic
4. Adjust data field extraction to match new site structure

---

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `playwright` | Browser automation (async) |
| `beautifulsoup4` | HTML parsing |
| `lxml` | BeautifulSoup parser backend (faster) |
| `asyncio` | Concurrency framework (stdlib) |

---

## Tips for AI Agents

1. **Page pool is the core pattern:** Always use `acquire_page()` and `release_page()` for concurrency
2. **JavaScript is disabled by default:** If content is missing, check if it's loaded dynamically
3. **Timeout tuning is important:** Network latency varies; increase `page.goto(timeout=...)` for slow connections
4. **Selectors are fragile:** Any site structure change breaks the scraper; periodically validate selectors
5. **Async/await is required:** All Playwright operations are async; don't try to run synchronously
6. **Output path is relative to src/:** The `OUTPUT_DIR` calculation depends on script location
7. **Concurrency over sequencing:** The architecture favors many concurrent pages over sequential requests
