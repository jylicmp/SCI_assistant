#!/usr/bin/env python3
"""
Notion Sync - Main synchronization script

Syncs markdown files from data_md/ directory to Notion Database.
Supports incremental updates based on Hash ID.

Uses @tryfabric/martian for markdown to Notion blocks conversion.

Usage:
    python notion_sync.py --sync-all     # Full sync
    python notion_sync.py --file xxx.md  # Sync single file
    python notion_sync.py --dry-run      # Preview without changes
"""

import os
import re
import sys
import json
import subprocess
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import frontmatter
from dotenv import load_dotenv
from notion_client import Client

from notion_schema import NOTION_SCHEMA, get_property_payload

# Load environment variables
load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
DATA_MD_DIR = Path(__file__).parent / "data_md"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NotionSync:
    """Main class for Notion synchronization."""

    def __init__(self):
        if not NOTION_TOKEN or not NOTION_DATABASE_ID:
            raise ValueError(
                "NOTION_TOKEN and NOTION_DATABASE_ID must be set in .env file"
            )

        self.client = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID
        logger.info(f"Initialized Notion client for database: {NOTION_DATABASE_ID}")

    def parse_md_frontmatter(self, file_path: Path) -> dict:
        """
        Parse markdown file and extract metadata from the "基本信息" section.

        The markdown format uses a structured section instead of YAML frontmatter:
        ## 📄 基本信息 (Metadata)
        - **Authors**: ...
        - **Journal/Year**: ...
        - **File Hash ID**: ...
        - **Keywords**: ...

        Args:
            file_path: Path to markdown file

        Returns:
            Dict containing extracted metadata
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata section
        metadata_section = re.search(
            r"## 📄 基本信息 \(Metadata\)\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL
        )

        if not metadata_section:
            logger.warning(f"No metadata section found in {file_path}")
            return {}

        metadata_text = metadata_section.group(1)
        metadata = {}

        # Parse individual fields
        authors_match = re.search(r"\*\*Authors\*\*:\s*(.+)", metadata_text)
        if authors_match:
            metadata["Authors"] = authors_match.group(1).strip()

        journal_year_match = re.search(
            r"\*\*Journal/Year\*\*:\s*([^/\n]+)\s*/\s*(\d{4})",
            metadata_text
        )
        if journal_year_match:
            metadata["Journal"] = journal_year_match.group(1).strip()
            metadata["Year"] = int(journal_year_match.group(2))

        hash_match = re.search(r"\*\*File Hash ID\*\*:\s*(\d+)", metadata_text)
        if hash_match:
            metadata["Hash ID"] = hash_match.group(1)

        keywords_match = re.search(r"\*\*Keywords\*\*:\s*(.+)", metadata_text)
        if keywords_match:
            metadata["Keywords"] = keywords_match.group(1).strip()

        # Extract title from first heading
        title_match = re.search(r"^#\s*(.+?)(?:\s*-\s*Literature Summary)?\s*$", content, re.MULTILINE)
        if title_match:
            metadata["Title"] = title_match.group(1).strip()

        metadata["File Path"] = str(file_path.resolve().relative_to(Path(__file__).parent))

        # Last modified time
        mtime = os.path.getmtime(file_path)
        metadata["Last Modified"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

        return metadata

    def md_to_notion_blocks(self, file_path: Path) -> list:
        """
        Convert markdown content to Notion Blocks API format using @tryfabric/martian.

        Uses the Node.js martian converter for full Markdown/GFM support including:
        - Headers (h1, h2, h3)
        - Paragraphs with inline formatting (bold, italic, code)
        - Bullet lists, numbered lists, checkboxes
        - Blockquotes and callouts
        - Code blocks with syntax highlighting
        - LaTeX equations (inline $...$ and block $$...$$)
        - Tables
        - Horizontal rules

        Args:
            file_path: Path to markdown file

        Returns:
            List of Notion block objects
        """
        # Call martian converter via Node.js
        try:
            result = subprocess.run(
                ["node", str(Path(__file__).parent / "martian_convert.js"), "--file", str(file_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Martian converter error: {result.stderr}")
                return []

            output = json.loads(result.stdout)

            if output.get("error"):
                logger.error(f"Martian converter error: {output.get('message')}")
                return []

            all_blocks = output.get("blocks", [])

            # Filter out metadata section blocks
            # Keep blocks starting from "## 1." sections or "## 🎯" (Core Takeaway)
            content_blocks = []
            skip_metadata = True

            for block in all_blocks:
                block_type = block.get("type")

                if skip_metadata:
                    # Check if this is a section we want to keep
                    if block_type in ["heading_1", "heading_2", "heading_3"]:
                        rich_text = block.get(block_type, {}).get("rich_text", [])
                        if rich_text:
                            text_content = "".join(
                                rt.get("text", {}).get("content", "")
                                for rt in rich_text
                            )
                            # Keep if it's a numbered section or Core Takeaway
                            if re.match(r"^\d+\.", text_content) or "🎯" in text_content or "Core" in text_content:
                                skip_metadata = False

                if not skip_metadata:
                    content_blocks.append(block)

            return content_blocks[:500]  # Limit to reasonable number

        except subprocess.TimeoutExpired:
            logger.error("Martian converter timed out")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse martian output: {e}")
            return []
        except Exception as e:
            logger.error(f"Error calling martian converter: {e}")
            return []

    def find_page_by_hash_id(self, hash_id: str) -> Optional[str]:
        """
        Query Notion database for a page with the given Hash ID.

        Args:
            hash_id: Hash ID to search for

        Returns:
            Page ID if found, None otherwise
        """
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Hash ID",
                    "rich_text": {
                        "contains": hash_id
                    }
                }
            )

            if response["results"]:
                page_id = response["results"][0]["id"]
                logger.info(f"Found existing page: {page_id} for Hash ID: {hash_id}")
                return page_id

            logger.info(f"No existing page found for Hash ID: {hash_id}")
            return None

        except Exception as e:
            logger.error(f"Error querying database: {e}")
            return None

    def create_page(self, metadata: dict, blocks: list) -> str:
        """
        Create a new page in Notion database.

        Args:
            metadata: Page properties
            blocks: Content blocks

        Returns:
            Created page ID
        """
        properties = {}

        for prop_name, prop_schema in NOTION_SCHEMA.items():
            if prop_name in metadata:
                properties[prop_name] = get_property_payload(
                    prop_name,
                    metadata[prop_name],
                    prop_schema["type"]
                )

        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=blocks[:100]  # API limit: 100 blocks per request
        )

        logger.info(f"Created new page: {response['id']}")
        return response["id"]

    def update_page(self, page_id: str, metadata: dict, blocks: list):
        """
        Update an existing page in Notion database.

        Args:
            page_id: Page to update
            metadata: New properties
            blocks: New content blocks
        """
        # Update properties
        properties = {}
        for prop_name, prop_schema in NOTION_SCHEMA.items():
            if prop_name in metadata:
                properties[prop_name] = get_property_payload(
                    prop_name,
                    metadata[prop_name],
                    prop_schema["type"]
                )

        self.client.pages.update(
            page_id=page_id,
            properties=properties
        )

        # Delete existing child blocks first, then add new ones
        self._delete_child_blocks(page_id)

        # Add new blocks in batches of 100 (API limit)
        if blocks:
            for i in range(0, len(blocks), 100):
                batch = blocks[i:i+100]
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=batch
                )
            logger.info(f"Added {len(blocks)} blocks in {max(1, (len(blocks)+99)//100)} batches")

        logger.info(f"Updated page: {page_id}")

    def _delete_child_blocks(self, page_id: str):
        """
        Delete all child blocks of a page.

        Args:
            page_id: Page ID to delete blocks from
        """
        try:
            total_deleted = 0

            while True:
                # Get child blocks
                response = self.client.blocks.children.list(
                    block_id=page_id,
                    page_size=100
                )

                blocks_to_delete = response.get('results', [])

                if not blocks_to_delete:
                    break

                # Delete each block
                for block in blocks_to_delete:
                    self.client.blocks.delete(block_id=block['id'])
                    total_deleted += 1

            logger.info(f"Deleted {total_deleted} blocks from page {page_id}")

        except Exception as e:
            logger.error(f"Error deleting blocks: {e}")

    def sync_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """
        Sync a single markdown file to Notion.

        Args:
            file_path: Path to markdown file
            dry_run: If True, preview changes without applying

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing: {file_path}")

        try:
            # Parse metadata
            metadata = self.parse_md_frontmatter(file_path)
            if not metadata:
                logger.warning(f"Skipping {file_path}: no metadata found")
                return False

            hash_id = metadata.get("Hash ID")
            if not hash_id:
                logger.warning(f"Skipping {file_path}: no Hash ID found")
                return False

            # Convert to blocks
            blocks = self.md_to_notion_blocks(file_path)

            if dry_run:
                logger.info(f"[DRY RUN] Would {'update' if self.find_page_by_hash_id(hash_id) else 'create'} page for {file_path.name}")
                logger.info(f"  Metadata: {list(metadata.keys())}")
                logger.info(f"  Blocks: {len(blocks)}")
                return True

            # Check if page exists
            page_id = self.find_page_by_hash_id(hash_id)

            if page_id:
                # Update existing page
                self.update_page(page_id, metadata, blocks)
            else:
                # Create new page
                self.create_page(metadata, blocks)

            logger.info(f"Successfully synced: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error syncing {file_path}: {e}")
            return False

    def sync_all(self, dry_run: bool = False) -> dict:
        """
        Sync all markdown files in data_md/ directory.

        Args:
            dry_run: If True, preview changes without applying

        Returns:
            Dict with sync statistics
        """
        stats = {"success": 0, "failed": 0, "skipped": 0}

        md_files = list(DATA_MD_DIR.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in {DATA_MD_DIR}")

        for file_path in md_files:
            result = self.sync_file(file_path, dry_run=dry_run)
            if result:
                stats["success"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"\n=== Sync Summary ===")
        logger.info(f"Success: {stats['success']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped: {stats['skipped']}")

        return stats


def main():
    parser = argparse.ArgumentParser(description="Sync markdown files to Notion")
    parser.add_argument(
        "--sync-all",
        action="store_true",
        help="Sync all files in data_md/"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Sync a specific file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying"
    )

    args = parser.parse_args()

    try:
        syncer = NotionSync()

        if args.sync_all:
            syncer.sync_all(dry_run=args.dry_run)
        elif args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                sys.exit(1)
            syncer.sync_file(file_path, dry_run=args.dry_run)
        else:
            parser.print_help()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
