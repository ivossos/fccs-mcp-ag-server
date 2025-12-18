# How to Create Entity Cache File

## Quick Start

The cache file has been created at: `.cache/members/Consol_Entity.json`

### Option 1: Edit the JSON file directly

1. Open `.cache/members/Consol_Entity.json` in a text editor
2. Replace the example entities with your actual entity names
3. Format:
```json
{
  "items": [
    {
      "name": "YourEntity1",
      "description": "Your Entity 1",
      "parent": "Root"
    },
    {
      "name": "YourEntity2",
      "description": "Your Entity 2",
      "parent": "Root"
    }
  ]
}
```

### Option 2: Use the helper script

```bash
# Interactive mode
python scripts/create_entity_cache.py

# Or provide entities as command line argument
python scripts/create_entity_cache.py "Entity1,Entity2,Entity3"
```

### Option 3: Export from Oracle Smart View

1. Export entity list from Oracle Smart View
2. Convert to JSON format matching the structure above
3. Save to `.cache/members/Consol_Entity.json`

## After Creating Cache

Once you have entities in the cache:

```bash
# Get top 10 performers for 2024
python scripts/get_top_10_performers.py
```

## Cache File Location

- **Path**: `.cache/members/Consol_Entity.json`
- **Format**: JSON with `items` array
- **Required fields**: `name` (minimum), `description` and `parent` (optional)

## Example Cache File

```json
{
  "items": [
    {
      "name": "North America",
      "description": "North America Region",
      "parent": "Root"
    },
    {
      "name": "Europe",
      "description": "Europe Region",
      "parent": "Root"
    },
    {
      "name": "Asia Pacific",
      "description": "Asia Pacific Region",
      "parent": "Root"
    }
  ]
}
```










