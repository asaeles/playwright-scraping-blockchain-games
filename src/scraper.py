import csv
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# --------------------------
# Configuration
# --------------------------
MAX_PAGES = 8  # how many persistent Page objects to keep in the pool (concurrency level)
TOTAL_PAGES = 61  # number of site pages to scrape
OUTPUT_DIR = Path("../output").resolve()  # Absolute path, available everywhere
OUTPUT_DIR.mkdir(exist_ok=True)  # Ensure directory exists

# --------------------------
# Page pool helpers
# --------------------------
async def build_page_pool(browser, size: int):
    """
    Create `size` independent Pages under separate contexts (JS disabled).
    Returns (page_slots, queue) where:
      - page_slots is a list of dicts with {'id', 'page', 'context'}
      - queue is an asyncio.Queue prefilled with these slots for reuse
    """
    print(f"[Pool] Creating {size} pages (one per isolated context)...")
    page_slots = []
    q = asyncio.Queue()
    for i in range(size):
        ctx = await browser.new_context(java_script_enabled=False)
        page = await ctx.new_page()
        slot = {'id': i + 1, 'page': page, 'context': ctx}
        page_slots.append(slot)
        await q.put(slot)
        print(f"[Pool] Page-{i+1} ready")
    print("[Pool] All pages are ready!")
    return page_slots, q

async def acquire_page(page_queue: asyncio.Queue):
    """Borrow a Page slot from the pool."""
    slot = await page_queue.get()
    return slot

def release_page(page_queue: asyncio.Queue, slot):
    """Return a Page slot to the pool."""
    page_queue.put_nowait(slot)

async def close_page_pool(page_slots):
    """Close all contexts (and pages) in the pool."""
    print("[Pool] Closing all pages and contexts...")
    for slot in page_slots:
        try:
            await slot['context'].close()
        except Exception as e:
            print(f"[Pool] Warning: error closing Page-{slot['id']}: {e}")
    print("[Pool] All closed.")

# --------------------------
# Scraping logic for one site page number
# --------------------------
async def scrape_site_page_with(page_slot, page_num: int):
    """
    Use a persistent Page to scrape a specific list page number.
    Optimized awaits: element handles are fetched once, then their text/attrs are gathered.
    """
    pid = page_slot['id']
    page = page_slot['page']
    url = f"https://playtoearn.com/blockchaingames?&page={page_num}"

    print(f"[Page-{pid}] Navigating to page #{page_num}: {url}")
    # Optional: increase timeout for flaky network; adjust as needed
    await page.goto(url, timeout=60000)

    # Fetch the whole games table HTML
    table = await page.query_selector('tbody.__TableItemsSwiper')
    if not table:
        print(f"[Page-{pid}][Scrape] No table found on site page {page_num}")
        return []
    table_html = await table.inner_html()

    # Parse the HTML with BeautifulSoup to extract game rows
    soup = BeautifulSoup(table_html, 'lxml')
    games = soup.find_all('tr')
    print(f"[Page-{pid}][Scrape] Found {len(games)} games on site page {page_num}")

    results = []

    # Process each game row
    for g, game in enumerate(games, start=1):
        td = game.find_all('td')
        link = (td[2].find('a', class_='dapp_detaillink') or {}).get('href')
        details = td[2].find('div', class_='__TextView')
        if not details:
            print(f"[Page-{pid}][Scrape] Skipping game {g} on site page {page_num} (no name found)")
            continue
        name = (t := details.find('b')) and t.get_text(strip=True)
        desc = (t := details.find('span')) and t.get_text(strip=True)
        category = '; '.join(div.get_text(strip=True) for div in details.find_all('div', class_='__TagItem'))
        blockchain = '; '.join(a['title'] for a in td[3].find_all('a', title=True))
        device = '; '.join(a['title'] for a in td[4].find_all('a', title=True))
        status = (t := td[5].find('a')) and t.get_text(strip=True)
        nft = (t := td[6].find('a')) and t.get_text(strip=True)
        f2p = (t := td[7].find('a')) and t.get_text(strip=True)
        p2e = '; '.join(a.get_text(strip=True) for a in td[8].find_all('a'))
        score = (t := td[9].find('span', class_='dailychangepercentage')) and t.get_text(strip=True)

        # Prepare the result dictionary
        results.append({
            'Name': name,
            'Desc': desc,
            'Category': category,
            'Blockchain': blockchain,
            'Device': device,
            'Status': status,
            'NFT': nft,
            'F2P': f2p,
            'P2E': p2e,
            'Score': score,
            'Link': link
        })
        #print(f"[Page-{pid}][Scrape] Finished parsing game {g} on site page {page_num}...")

    print(f"[Page-{pid}][Scrape] Finished site page {page_num}")
    return results

# --------------------------
# Worker for a given site page number
# --------------------------
async def page_worker(page_queue: asyncio.Queue, site_page_num: int):
    """
    Acquire a pooled Page, scrape one site page number, and release the Page.
    """
    slot = await acquire_page(page_queue)
    try:
        print(f"[Worker] Using Page-{slot['id']} for site page #{site_page_num}")
        data = await scrape_site_page_with(slot, site_page_num)
        print(f"[Worker] Page-{slot['id']} got {len(data)} rows from site page #{site_page_num}")
        return (site_page_num, data)  # Return page_num with results
    finally:
        release_page(page_queue, slot)

# --------------------------
# Main async runner
# --------------------------
async def main():
    print("[Main] Starting async scraping")
    async with async_playwright() as p:
        print("[Main] Launching Chromium...")
        browser = await p.chromium.launch(headless=True)

        # Build the pool of persistent Pages
        page_slots, page_queue = await build_page_pool(browser, MAX_PAGES)

        # Schedule all work
        print(f"[Main] Scheduling {TOTAL_PAGES} site pages with {MAX_PAGES} pooled pages...")
        tasks = [page_worker(page_queue, i) for i in range(1, TOTAL_PAGES + 1)]

        # Stream results as they complete
        unordered_results = []
        for coro in asyncio.as_completed(tasks):
            page_num, page_results = await coro  # Unpack tuple
            if page_results:
                unordered_results.append((page_num, page_results))

        # Sort by original page number and flatten
        unordered_results.sort(key=lambda x: x[0])
        all_results = [item for _, items in unordered_results for item in items]

        # Tear down the pool and browser
        await close_page_pool(page_slots)
        print("[Main] Closing browser...")
        await browser.close()

    # Write CSV
    print(f"[Main] Saving {len(all_results)} rows to games.csv")
    fieldnames = [
        'Name', 'Desc', 'Category', 'Blockchain', 'Device',
        'Status', 'NFT', 'F2P', 'P2E', 'Score', 'Link'
    ]
    with open(OUTPUT_DIR / 'games.csv', 'w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    print("[Main] Done! CSV saved to games.csv")

# --------------------------
# Entry point
# --------------------------
if __name__ == "__main__":
    asyncio.run(main())
