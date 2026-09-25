#!/usr/bin/env python3
"""Test script to verify Bring! API connection and credentials."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from src.bring_mcp.bring_api import BringAPI, BringAPIError


async def main():
    """Test Bring! API connection."""
    # Load environment variables
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("⚠️  No .env file found. Please create one from .env.example")
        return

    email = os.getenv("BRING_EMAIL")
    password = os.getenv("BRING_PASSWORD")

    if not email or not password:
        print("❌ Error: BRING_EMAIL and BRING_PASSWORD must be set in .env file")
        return

    print(f"🔑 Testing connection for: {email}")
    print("-" * 50)

    try:
        # Create and test API client
        async with BringAPI(email=email, password=password) as client:
            print("✅ Authentication successful!")
            print(f"   User UUID: {client._user_uuid}")
            print()

            # Get lists
            print("📋 Fetching shopping lists...")
            lists = await client.get_lists()

            if not lists:
                print("⚠️  No shopping lists found.")
                print("   Please create a list in the Bring! app first.")
                return

            print(f"✅ Found {len(lists)} shopping list(s):\n")

            for i, lst in enumerate(lists, 1):
                print(f"{i}. {lst['name']}")
                print(f"   UUID: {lst['listUuid']}")
                if lst.get("theme"):
                    print(f"   Theme: {lst['theme']}")

                # Get items from first list as example
                if i == 1:
                    print("\n   📦 Items in this list:")
                    items_data = await client.get_list_items(lst["listUuid"])

                    purchase_items = items_data.get("purchase", [])
                    recent_items = items_data.get("recently", [])

                    if purchase_items:
                        print("   To buy:")
                        for item in purchase_items[:5]:  # Show max 5
                            name = item.get("name", item.get("itemId", "Unknown"))
                            spec = item.get("specification", "")
                            print(f"     • {name}", end="")
                            if spec:
                                print(f" ({spec})", end="")
                            print()
                        if len(purchase_items) > 5:
                            print(f"     ... and {len(purchase_items) - 5} more")
                    else:
                        print("     (empty)")

                    if recent_items:
                        print(f"   Recently purchased: {len(recent_items)} items")

                print()

            print("=" * 50)
            print("✅ Connection test successful!")
            print("\n💡 Tips:")
            print("   - Use the list UUID to add items via MCP")
            print("   - Configure Claude Desktop with your credentials")
            print("   - See README.md for integration examples")

    except BringAPIError as e:
        print(f"❌ Bring! API Error: {e}")
        print("\n💡 Common issues:")
        print("   - Check your email and password in .env")
        print("   - Ensure you have an active Bring! account")
        print("   - Check your internet connection")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
