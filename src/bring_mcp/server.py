"""MCP Server for Bring! Shopping List integration."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

from .bring_api import BringAPI, BringAPIError

# Load environment variables
load_dotenv()

# Store mappings file path: BRING_STORE_MAPPINGS, defaulting to the project root
_MAPPINGS_FILE = Path(
    os.getenv(
        "BRING_STORE_MAPPINGS",
        Path(__file__).resolve().parent.parent.parent / "store_mappings.json",
    )
)


def _german_variants(word: str) -> set[str]:
    """Generate plausible German singular/plural variants of a word.

    Covers the most common German plural patterns:
    -n, -en, -s, -e, -er and their removal.
    """
    w = word.lower()
    variants = {w}

    # Strip endings to find potential singular forms
    if w.endswith("en") and len(w) > 3:
        variants.add(w[:-1])       # Orangen → Orange
        variants.add(w[:-2])       # Kartoffeln would not hit this, but harmless
    if w.endswith("n") and len(w) > 2:
        variants.add(w[:-1])       # Zwiebeln → Zwiebel
    if w.endswith("s") and len(w) > 2:
        variants.add(w[:-1])       # Joghurts → Joghurt
    if w.endswith("e") and len(w) > 2:
        variants.add(w[:-1])       # Tomaten... Tomate → Tomat (harmless)
    if w.endswith("er") and len(w) > 3:
        variants.add(w[:-2])       # Eier → Ei

    # Add endings to find potential plural forms
    variants.add(w + "n")          # Zwiebel → Zwiebeln
    variants.add(w + "en")         # Tomate → Tomaten
    variants.add(w + "s")          # Joghurt → Joghurts
    variants.add(w + "e")          # Hund → Hunde
    variants.add(w + "er")         # Ei → Eier

    return variants


def _load_store_mappings() -> dict[str, str]:
    """Load item-to-store mappings from store_mappings.json.

    Generates German singular/plural variants for fuzzy matching.

    Returns:
        Dictionary mapping item name variants (lowercase) to store names.
    """
    if not _MAPPINGS_FILE.exists():
        return {}

    with open(_MAPPINGS_FILE) as f:
        data = json.load(f)

    item_to_store: dict[str, str] = {}
    for store, items in data.get("stores", {}).items():
        for item in items:
            for variant in _german_variants(item):
                item_to_store[variant] = store

    return item_to_store


def _get_default_store() -> str | None:
    """Get the default store from mappings."""
    if not _MAPPINGS_FILE.exists():
        return None

    with open(_MAPPINGS_FILE) as f:
        data = json.load(f)

    return data.get("default_store")

# Server instance
app = Server("bring-mcp-server")

# Global API client instance
_bring_client: BringAPI | None = None


def _get_bring_client() -> BringAPI:
    """Get or create the Bring! API client instance."""
    global _bring_client

    if _bring_client is None:
        email = os.getenv("BRING_EMAIL")
        password = os.getenv("BRING_PASSWORD")

        if not email or not password:
            raise ValueError(
                "BRING_EMAIL and BRING_PASSWORD must be set in environment variables"
            )

        _bring_client = BringAPI(email=email, password=password)

    return _bring_client


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Bring! MCP tools."""
    return [
        Tool(
            name="bring_get_lists",
            description="Get all available Bring! shopping lists for the authenticated user. Returns list names and UUIDs.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="bring_get_list_items",
            description="Get all items from a specific Bring! shopping list. Returns items to purchase and recently purchased items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uuid": {
                        "type": "string",
                        "description": "UUID of the shopping list. Use bring_get_lists to find the UUID.",
                    },
                },
                "required": ["list_uuid"],
            },
        ),
        Tool(
            name="bring_add_item",
            description="Add one or more items to a Bring! shopping list. Can add multiple items in a single call.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uuid": {
                        "type": "string",
                        "description": "UUID of the shopping list. Use bring_get_lists to find the UUID.",
                    },
                    "items": {
                        "type": "array",
                        "description": "List of items to add to the shopping list",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the item (e.g., 'Milk', 'Apples')",
                                },
                                "specification": {
                                    "type": "string",
                                    "description": "Optional specification or details (e.g., '2 liters', 'organic')",
                                },
                            },
                            "required": ["name"],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["list_uuid", "items"],
            },
        ),
        Tool(
            name="bring_complete_item",
            description="Mark an item as purchased/completed and remove it from the shopping list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uuid": {
                        "type": "string",
                        "description": "UUID of the shopping list",
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Name of the item to mark as completed",
                    },
                },
                "required": ["list_uuid", "item_name"],
            },
        ),
        Tool(
            name="bring_remove_item",
            description="Completely remove an item from a shopping list (without marking as purchased).",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_uuid": {
                        "type": "string",
                        "description": "UUID of the shopping list",
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Name of the item to remove",
                    },
                },
                "required": ["list_uuid", "item_name"],
            },
        ),
        Tool(
            name="bring_smart_add",
            description=(
                "Smart-add items to Bring! shopping lists based on stored store preferences. "
                "Automatically routes each item to the correct store list (e.g. Aldi, Rewe) "
                "based on store_mappings.json. Items without a mapping are reported back. "
                "Use this instead of bring_add_item when you don't know which list an item belongs to."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "List of items to add. Each item is routed to its mapped store list automatically.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the item (e.g., 'Butter', 'Milch')",
                                },
                                "specification": {
                                    "type": "string",
                                    "description": "Optional specification (e.g., '500g', 'Bio')",
                                },
                            },
                            "required": ["name"],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["items"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for Bring! operations."""
    try:
        client = _get_bring_client()

        # Ensure we're logged in
        if not client._access_token:
            await client.login()

        if name == "bring_get_lists":
            lists = await client.get_lists()

            if not lists:
                return [
                    TextContent(
                        type="text",
                        text="No shopping lists found. Create a list in the Bring! app first.",
                    )
                ]

            result = "Available Bring! Shopping Lists:\n\n"
            for lst in lists:
                result += f"• {lst['name']}\n"
                result += f"  UUID: {lst['listUuid']}\n"
                if lst.get("theme"):
                    result += f"  Theme: {lst['theme']}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "bring_get_list_items":
            list_uuid = arguments.get("list_uuid")
            if not list_uuid:
                return [
                    TextContent(
                        type="text",
                        text="Error: list_uuid is required",
                    )
                ]

            items_data = await client.get_list_items(list_uuid)

            purchase_items = items_data.get("purchase", [])
            recent_items = items_data.get("recently", [])

            result = f"Shopping List Items (UUID: {list_uuid}):\n\n"

            if purchase_items:
                result += "📋 Items to Purchase:\n"
                for item in purchase_items:
                    name = item.get("name", item.get("itemId", "Unknown"))
                    spec = item.get("specification", "")
                    result += f"  • {name}"
                    if spec:
                        result += f" ({spec})"
                    result += "\n"
                result += "\n"
            else:
                result += "📋 No items to purchase\n\n"

            if recent_items:
                result += "✅ Recently Purchased:\n"
                for item in recent_items:
                    name = item.get("name", item.get("itemId", "Unknown"))
                    result += f"  • {name}\n"
            else:
                result += "✅ No recently purchased items"

            return [TextContent(type="text", text=result)]

        elif name == "bring_add_item":
            list_uuid = arguments.get("list_uuid")
            items = arguments.get("items", [])

            if not list_uuid:
                return [
                    TextContent(
                        type="text",
                        text="Error: list_uuid is required",
                    )
                ]

            if not items:
                return [
                    TextContent(
                        type="text",
                        text="Error: at least one item is required",
                    )
                ]

            added_items = []
            for item in items:
                item_name = item.get("name")
                specification = item.get("specification", "")

                if not item_name:
                    continue

                await client.add_item(
                    list_uuid=list_uuid,
                    item_name=item_name,
                    specification=specification,
                )
                added_items.append((item_name, specification))

            result = f"✅ Successfully added {len(added_items)} item(s) to the list:\n\n"
            for name, spec in added_items:
                result += f"  • {name}"
                if spec:
                    result += f" ({spec})"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "bring_complete_item":
            list_uuid = arguments.get("list_uuid")
            item_name = arguments.get("item_name")

            if not list_uuid or not item_name:
                return [
                    TextContent(
                        type="text",
                        text="Error: list_uuid and item_name are required",
                    )
                ]

            await client.complete_item(list_uuid=list_uuid, item_name=item_name)

            return [
                TextContent(
                    type="text",
                    text=f"✅ Marked '{item_name}' as purchased and removed from list",
                )
            ]

        elif name == "bring_remove_item":
            list_uuid = arguments.get("list_uuid")
            item_name = arguments.get("item_name")

            if not list_uuid or not item_name:
                return [
                    TextContent(
                        type="text",
                        text="Error: list_uuid and item_name are required",
                    )
                ]

            await client.remove_item(list_uuid=list_uuid, item_name=item_name)

            return [
                TextContent(
                    type="text",
                    text=f"✅ Removed '{item_name}' from the list",
                )
            ]

        elif name == "bring_smart_add":
            items = arguments.get("items", [])

            if not items:
                return [
                    TextContent(type="text", text="Error: at least one item is required")
                ]

            # Load mappings and resolve store names to list UUIDs
            item_to_store = _load_store_mappings()
            default_store = _get_default_store()

            all_lists = await client.get_lists()
            store_to_uuid = {lst["name"].lower(): lst["listUuid"] for lst in all_lists}

            # Group items by store
            by_store: dict[str, list[tuple[str, str]]] = {}
            unmapped: list[str] = []

            for item in items:
                item_name = item.get("name", "")
                specification = item.get("specification", "")
                if not item_name:
                    continue

                store = item_to_store.get(item_name.lower()) or default_store
                if store and store.lower() in store_to_uuid:
                    by_store.setdefault(store, []).append((item_name, specification))
                else:
                    unmapped.append(item_name)

            # Add items per store
            added: dict[str, list[str]] = {}
            for store, store_items in by_store.items():
                list_uuid = store_to_uuid[store.lower()]
                for item_name, specification in store_items:
                    await client.add_item(
                        list_uuid=list_uuid,
                        item_name=item_name,
                        specification=specification,
                    )
                    added.setdefault(store, []).append(item_name)

            # Build result
            parts = []
            for store, names in added.items():
                parts.append(f"  {store}: {', '.join(names)}")

            result = ""
            if parts:
                result += f"Added {sum(len(n) for n in added.values())} item(s):\n" + "\n".join(parts)

            if unmapped:
                if result:
                    result += "\n\n"
                result += f"No store mapping found for: {', '.join(unmapped)}\n"
                result += "Use bring_add_item with a specific list_uuid, or add mappings to store_mappings.json."

            return [TextContent(type="text", text=result)]

        else:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'",
                )
            ]

    except BringAPIError as e:
        return [
            TextContent(
                type="text",
                text=f"Bring! API Error: {str(e)}",
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"Unexpected error: {str(e)}",
            )
        ]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def run():
    """Entry point for the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
