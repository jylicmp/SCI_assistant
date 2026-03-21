#!/usr/bin/env python3
"""
Check sync status between local files and Notion database.
Compares Hash IDs to find discrepancies.
"""

import os
import glob
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_local_hashes():
    """Get all Hash IDs from local data_md directory."""
    md_files = glob.glob("data_md/*.md")
    hashes = set(Path(f).stem for f in md_files)
    return hashes

def get_notion_hashes():
    """Query Notion database for all Hash IDs."""
    from notion_client import Client
    
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    hashes = set()
    has_more = True
    start_cursor = None
    
    while has_more:
        response = notion.databases.query(
            database_id=database_id,
            start_cursor=start_cursor
        )
        
        for page in response["results"]:
            hash_prop = page["properties"].get("Hash ID", {})
            if hash_prop.get("rich_text"):
                hash_value = hash_prop["rich_text"][0]["text"]["content"]
                hashes.add(hash_value)
        
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    
    return hashes

def main():
    print("=" * 60)
    print("Notion vs Local Files Sync Check")
    print("=" * 60)
    
    # Get local hashes
    local_hashes = get_local_hashes()
    print(f"\n本地MD文件数量: {len(local_hashes)}")
    
    # Get Notion hashes
    try:
        notion_hashes = get_notion_hashes()
        print(f"Notion页面数量: {len(notion_hashes)}")
    except Exception as e:
        print(f"\n❌ 无法连接Notion: {e}")
        print("请检查 NOTION_TOKEN 和 NOTION_DATABASE_ID 环境变量")
        return
    
    print()
    print("-" * 60)
    
    # Find differences
    only_local = local_hashes - notion_hashes
    only_notion = notion_hashes - local_hashes
    common = local_hashes & notion_hashes
    
    print(f"共同存在: {len(common)} 篇")
    print(f"只在本地: {len(only_local)} 篇")
    print(f"只在Notion: {len(only_notion)} 篇")
    print()
    
    # Show details
    if only_local:
        print("=" * 60)
        print(f"⚠️  只在本地存在 ({len(only_local)}篇):")
        print("-" * 60)
        for h in sorted(only_local):
            print(f"  {h}")
        print()
    
    if only_notion:
        print("=" * 60)
        print(f"⚠️  只在Notion存在 ({len(only_notion)}篇):")
        print("-" * 60)
        for h in sorted(only_notion)[:10]:  # Show first 10
            print(f"  {h}")
        if len(only_notion) > 10:
            print(f"  ... and {len(only_notion) - 10} more")
        print()
    
    if not only_local and not only_notion:
        print("=" * 60)
        print("✅ 完全一致！所有文章都已同步")
        print("=" * 60)
    else:
        print("=" * 60)
        print(f"总结: {len(common)}篇一致, {len(only_local)}篇待同步到Notion, {len(only_notion)}篇只在Notion")
        print("=" * 60)

if __name__ == "__main__":
    main()
