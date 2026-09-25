# Bring! MCP Server: Quick Start

## Get started in 5 steps

### 1. Set up the environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Create the configuration

```bash
# Create the .env file
cp .env.example .env

# Edit .env and enter your Bring! credentials
nano .env  # or your preferred editor
```

Enter:

```
BRING_EMAIL=your.email@example.com
BRING_PASSWORD=your_password_here
```

Optional, for `bring_smart_add`: create your own store mappings from the template.

```bash
cp store_mappings.example.json store_mappings.json
```

`store_mappings.json` is ignored by git. Set `BRING_STORE_MAPPINGS` if you want to keep it somewhere else.

### 3. Test the connection

```bash
python test_connection.py
```

The script shows you:

- whether authentication works
- all your shopping lists
- the list UUIDs
- the items in your first list

### 4. Configure Claude Desktop

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

**Important**:

- Replace `/path/to/bring-mcp-server` with the actual path of your checkout
- Enter your real credentials

### 5. Restart Claude Desktop

Restart Claude Desktop so the changes take effect.

## First steps with Claude

### Show lists

```
Show me my Bring! shopping lists
```

### Add items

```
Add the following items to my weekly shopping list:
- Milk (2 litres)
- Apples
- Bread (wholegrain)
```

### Show the current list

```
Show me all items on my shopping list
```

### Mark items as purchased

```
Mark the milk as purchased
```

## Combining with other MCP servers

### Example: recipe to shopping list (e.g. with a Notion MCP server)

```
Get the recipe "Spaghetti Carbonara" from Notion and add all
ingredients to my Bring! shopping list
```

Claude will:

1. Look up the recipe in Notion
2. Extract the ingredients
3. Fetch your Bring! lists
4. Add the ingredients to the list

## Troubleshooting

### "No shopping lists found"

Create a list in the Bring! app on your phone first.

### "Not authenticated"

Check your credentials in `.env` or in the Claude Desktop configuration.

### Server does not start

```bash
# Check the Python version
python --version  # should be 3.12.x

# Reinstall dependencies
pip install -e ".[dev]"
```

## Useful commands

```bash
# Run the tests
python -m pytest -v

# Start the server manually (for debugging)
python -m bring_mcp.server

# Update dependencies
pip install --upgrade -e ".[dev]"
```

## More help

See [README.md](README.md) for the tools, configuration options, store mappings and limitations.
