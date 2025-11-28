# Playwright Scraping Blockchain Games

A robust Python-based web scraper designed to extract data from PlayToEarn.com. This project leverages Playwright to handle dynamic content rendering and BeautifulSoup for efficient HTML parsing, all wrapped in an asynchronous architecture for improved performance.

## Background

This repository was originally developed as a technical proof-of-concept for a freelance project bid. Although I was not selected for the final contract, the code demonstrates a fully functional, production-ready approach to handling complex, JavaScript-heavy web scraping tasks using modern Python tools.

## Features

* **Headless Dynamic Content Handling**: Uses Playwright to render and interact with JavaScript-heavy pages where standard requests fail.
* **Efficient Parsing**: Utilizes BeautifulSoup (bs4) to extract specific game data (titles, genres, scores, status) from the rendered DOM.
* **Data Export**: Automatically creates an `output/` directory and saves the scraped data to a structured CSV file.
* **Asynchronous Execution**: Built with asyncio to handle network requests and processing concurrently, significantly reducing execution time.
* **Containerized**: Includes a Dockerfile and entrypoint script for easy deployment and environment isolation.

## Tech Stack

* Python
* Playwright (Browser Automation)
* BeautifulSoup4 (HTML Parsing)
* Docker (Containerization)

## Prerequisites

* Python 3.8 or higher
* Docker (optional, for containerized run)

## Installation

1. Clone the repository
```bash
git clone  https://github.com/asaeles/playwright-scraping-blockchain-games.git
cd playwright-scraping-blockchain-games
```
2. Install Python dependencies
```
pip install -r requirements.txt
```
3. Install Playwright browsers Playwright requires browser binaries to function correctly.
```
playwright install
```

## Usage

### Running Locally

To start the scraper on your local machine, run the main script located in the src directory:
```bash
python src/scraper.py
```

### Running with Docker

This project comes with a Dockerfile for easy containerization.

1. Build the Docker image
```bash
docker build -t p2e-scraper .
```
2. Run the container
```bash
docker run --rm p2e-scraper
```

## Project Structure

```text
.
├── src/                    # Source code directory
│   └── scraper.py          # Main Python script utilizing Playwright & BS4
├── output/                 # Directory created at runtime to store results
│   └── games.csv           # The final output file containing scraped data
├── .dockerignore           # Excludes files from the Docker build context
├── .gitignore              # Specifies files to be ignored by Git version control
├── Dockerfile              # Blueprint for building the container image
├── entrypoint.sh           # Shell script to initialize and run the container
└── requirements.txt        # List of Python dependencies (playwright, beautifulsoup4)
```

## Roadmap & Enhancements

While the current version serves as a functional proof-of-concept, the following features are planned for future production releases:

* **Rate Limiting & Jitter**: Implement randomized delays (`asyncio.sleep`) between requests to mimic human behavior and prevent server overload or WAF triggering.
* **Proxy Rotation**: Integrate a proxy pool (e.g., BrightData or IPRoyal) to distribute requests across multiple IPs, preventing IP-based blocking.
* **Robust Error Handling**: Add retry logic (exponential backoff) for network timeouts or failed selector matching to ensure data completeness during long scraping sessions.
* **Configuration Management**: Decouple settings (e.g., `MAX_PAGES`, `TOTAL_PAGES`) from the source code by moving them to environment variables or a `.env` file.
* **Database Integration**: Migrate from CSV storage to a structured database (PostgreSQL or MongoDB) to handle larger datasets and enable incremental scraping updates.
* **Headless Toggle**: Add a command-line argument to easily switch between headless and headed mode for easier debugging.

## Legal Notice

This project is for educational and research purposes. Please ensure you comply with:

* **Website Terms of Service**: Review the target site's policies.
* **Rate Limiting**: Adhere to polite scraping intervals to avoid burdening the server.
* **Robots.txt**: Check the `robots.txt` file for disallowed paths.

Always respect website policies and consider using official APIs when available.