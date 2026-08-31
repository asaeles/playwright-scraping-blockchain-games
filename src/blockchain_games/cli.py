"""Command-line interface for the blockchain-games scraper."""

import asyncio
from .app import main as app_main


def main():
    """Main CLI entry point for the blockchain-games application."""
    asyncio.run(app_main())


if __name__ == "__main__":
    main()
