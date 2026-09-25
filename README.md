# Bring! MCP Server

An MCP (Model Context Protocol) server that connects Claude to the Bring! shopping list app. Claude can read shopping lists, add items, check them off and sort them into the right store automatically.

> **Disclaimer:** This is an unofficial project. It is not affiliated with, endorsed by or supported by Bring! Labs AG. It uses the undocumented Bring! API, which can change without notice and may break this server at any time. The `X-BRING-API-KEY` header value in the code is the public client key that ships with the Bring! apps; it is not a personal secret. Use at your own risk.

## Purpose

Bring! is a popular shopping list app, but it has no official API for third-party integrations. This MCP server uses the unofficial Bring! API and lets Claude manage your shopping lists directly: dictate items while you shop, look up a list, or sort items by store automatically, all from the chat.

## Available tools

| Tool | Description |
|---|---|
| `bring_get_lists` | List all Bring! shopping lists of the account (name and UUID) |
| `bring_get_list_items` | Get all items of a list (items to buy and recently purchased items) |
| `bring_add_item` | Add one or more items to a list (with an optional specification, e.g. a quantity) |
| `bring_complete_item` | Mark an item as purchased and remove it from the active list |
| `bring_remove_item` | Remove an item from the list completely (without marking it as purchased) |
| `bring_smart_add` | Add items smartly: assigns each item to the right store list automatically (based on the store mappings file) |

## Requirements

- Python 3.12+
- An active Bring! account (free at [getbring.com](https://www.getbring.com))
- The shopping lists you want to use must already exist in the Bring! app

## Installation

```bash
git clone https://github.com/AndreClaassen1/bring-mcp-server.git
cd bring-mcp-server
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .            # or: pip install -e ".[dev]" for tests
```

## Configuration

### Environment variables

Copy `.env.example` to `.env` and enter your Bring! credentials:

```env
BRING_EMAIL=your.email@example.com
BRING_PASSWORD=your_password_here
```

| Variable | Required | Description |
|---|---|---|
| `BRING_EMAIL` | yes | Email address of your Bring! account |
| `BRING_PASSWORD` | yes | Password of your Bring! account |
| `BRING_STORE_MAPPINGS` | no | Path to the store mappings file (default: `store_mappings.json` in the project root) |

### Store mappings (optional)

The store mappings file defines which items belong to which store. This lets the `bring_smart_add` tool put each item on the right list automatically. Each store name must match the name of a list in your Bring! account.

Your personal mappings live in `store_mappings.json`. That file is ignored by git so your own data never ends up in the repository. To get started, copy the template:

```bash
cp store_mappings.example.json store_mappings.json
```

```json
{
  "include_stores": ["Supermarket", "Discounter", "Drugstore"],
  "stores": {
    "Discounter": ["Milch", "Butter", "Eier", "Mehl"],
    "Supermarket": ["Avocado", "Mozzarella", "Pesto"],
    "Drugstore": ["Zahnpasta", "Shampoo"]
  },
  "default_store": "Supermarket",
  "_learned": {
    "last_run": null,
    "items": []
  }
}
```

- `stores`: maps each store (list name) to the items bought there.
- `default_store`: list used for items that have no mapping.
- `include_stores` and `_learned`: not read by the server; reserved for external tooling that maintains the file. They can stay as in the template.

To keep the file somewhere else, set `BRING_STORE_MAPPINGS` to its absolute path. If the file does not exist, `bring_smart_add` has no mappings and no default store, so it reports every item as unmapped instead of adding it. Items whose store has no matching list in your Bring! account are reported as unmapped as well.

The server recognises common German singular and plural forms automatically (e.g. "Ei" also matches "Eier").

## Claude Desktop integration

```json
{
  "mcpServers": {
    "bring": {
      "command": "/path/to/bring-mcp-server/.venv/bin/python",
      "args": ["-m", "bring_mcp.server"],
      "env": {
        "BRING_EMAIL": "your.email@example.com",
        "BRING_PASSWORD": "your_password_here"
      }
    }
  }
}
```

Add `"BRING_STORE_MAPPINGS": "/path/to/store_mappings.json"` to `env` if your mappings file lives outside the project root.

The configuration file is located at:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

See [QUICKSTART.md](QUICKSTART.md) for a step by step setup.

## Example prompts

```
Add milk, butter and eggs to my shopping list.
```

```
Show me all items on my supermarket list.
```

```
I bought the milk, please check it off.
```

## Status and limitations

Working. The server uses the unofficial Bring! API (`api.getbring.com`). Because the API is undocumented, endpoints and behaviour can change without notice, and the server may stop working until it is adapted. The store matching is tuned for German item names.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT, see [LICENSE](LICENSE).

The name and any logo/icon are not covered by the license.
