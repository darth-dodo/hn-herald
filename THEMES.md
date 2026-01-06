# HN Herald Theme System

## Overview

HN Herald now supports three minimal, clean themes:

1. **HN Orange** (default) - Classic HackerNews orange theme
2. **Ocean** - Calming blue-green ocean theme
3. **Dark** - Easy-on-eyes dark theme with warm amber accents

## Theme Colors

### HN Orange Theme (default)
- Primary: #ff6600 (HN orange)
- Background: #f6f6ef (HN beige)
- Text: #000000 (black)
- Secondary: #828282 (gray)
- Header: #ff6600 (orange)
- Button: #ff6600 (orange)

### Ocean Theme
- Primary: #006d77 (deep teal)
- Background: #e0f2f1 (light cyan/mint)
- Text: #1a1a1a (near black)
- Secondary: #4a7c7e (teal gray)
- Header: #00838f (cyan)
- Button: #006d77 (deep teal)

### Dark Theme
- Primary: #ffa726 (warm amber)
- Background: #1a1a1a (charcoal)
- Text: #e0e0e0 (light gray)
- Secondary: #999999 (medium gray)
- Header: #0a0a0a (almost black)
- Button: #ffa726 (warm amber)

## Usage

### Switching Themes
Click the theme links in the header:
- **theme: hn | ocean | dark**

The current theme is shown in bold, others are clickable links.

### Footer
The footer is now sticky and remains visible at the bottom of the viewport.

### Theme Persistence
Your theme preference is saved to localStorage and persists across sessions.

### Default Theme
If no theme is saved, the app defaults to the HN Orange theme.

## Custom Tags

Each tag section (Interest Tags and Disinterest Tags) now includes:

1. **Predefined tags** - Click to add common tags
2. **Custom input** - Type your own tags
   - Enter text in the "Custom:" input field
   - Click "add" button or press Enter to add the tag
   - Input clears automatically after adding

## Technical Details

### CSS Variables
All themes use CSS custom properties for easy theming:

```css
:root {
  --primary-color: #ff6600;
  --bg-color: #f6f6ef;
  --text-color: #000000;
  --secondary-color: #828282;
  --border-color: #d4d4cc;
  --header-bg: #ff6600;
  --header-text: #000000;
  --input-bg: #ffffff;
  --selected-bg: #ffffff;
  --button-bg: #ff6600;
  --button-text: #ffffff;
  --button-hover: #ea580c;
  --loading-border: #ff6600;
}
```

### Theme Switching
Themes are applied via `data-theme` attribute on `<html>`:

```javascript
document.documentElement.setAttribute('data-theme', 'white');
```

### Files Modified
- `src/hn_herald/static/css/input.css` - CSS variables and theme definitions
- `src/hn_herald/templates/base.html` - Theme switcher in header
- `src/hn_herald/templates/partials/digest_form.html` - Custom tag inputs
- `src/hn_herald/static/js/app.js` - Theme management functions

## Design Philosophy

All three themes maintain:
- Minimal, functional aesthetics
- Verdana 10pt font (HN standard)
- 900px max width
- 4-8px padding (compact spacing)
- No shadows, gradients, or unnecessary effects
- Clean, readable typography
- High contrast for accessibility
