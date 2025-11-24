# Search Functionality

## Simple Search

```python
async def search_command(update, context):
    """Search command."""
    if not context.args:
        await update.message.reply_text("Usage: /search <query>")
        return
    
    query = " ".join(context.args)
    results = await perform_search(query)
    
    if not results:
        await update.message.reply_text("No results found")
        return
    
    message = f"Search results for '{query}':\n\n"
    for i, result in enumerate(results[:5], 1):
        message += f"{i}. {result['title']}\n"
    
    await update.message.reply_text(message)
```

## Fuzzy Search

```python
from fuzzywuzzy import fuzz

def fuzzy_search(query: str, items: list[str], threshold: int = 70) -> list[str]:
    """Perform fuzzy search."""
    results = []
    
    for item in items:
        score = fuzz.ratio(query.lower(), item.lower())
        if score >= threshold:
            results.append((item, score))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    return [item for item, score in results]
```

## Search with Filters

```python
async def advanced_search(query: str, filters: dict) -> list:
    """Search with filters."""
    results = await db.search(query)
    
    # Apply filters
    if 'category' in filters:
        results = [r for r in results if r.category == filters['category']]
    
    if 'date_from' in filters:
        results = [r for r in results if r.created_at >= filters['date_from']]
    
    return results
```

## Paginated Search Results

```python
async def show_search_results(update, context, results: list, page: int = 0):
    """Show paginated search results."""
    per_page = 5
    start = page * per_page
    end = start + per_page
    
    page_results = results[start:end]
    total_pages = (len(results) + per_page - 1) // per_page
    
    message = f"Results (Page {page + 1}/{total_pages}):\n\n"
    for i, result in enumerate(page_results, start + 1):
        message += f"{i}. {result['title']}\n"
    
    keyboard = create_pagination_keyboard(page, total_pages)
    await update.message.reply_text(message, reply_markup=keyboard)
```
