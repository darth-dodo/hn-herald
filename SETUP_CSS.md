# CSS Setup Instructions

## Quick Start

HN Herald uses Tailwind CSS for styling. Before running the application, you need to build the CSS.

### 1. Install Node.js Dependencies

```bash
make install-node
```

Or directly with npm:
```bash
npm install
```

### 2. Build CSS

```bash
make css
```

Or directly with npm:
```bash
npm run build:css
```

This will generate `src/hn_herald/static/css/styles.css` from `src/hn_herald/static/css/input.css`.

### 3. Development Workflow

For development, run Tailwind in watch mode in a separate terminal:

```bash
make dev-css
```

This will automatically rebuild CSS when you modify templates or `input.css`.

## What Was Created

Phase 5 implementation created the following files:

### Configuration Files

- **`tailwind.config.js`** - Tailwind CSS configuration
  - Content paths for template scanning
  - Custom colors (primary, success, warning, error)
  - Mobile-first breakpoints
  - Custom utilities for touch targets
  - Dark mode support (system preference)

- **`package.json`** - Node.js dependencies and scripts
  - `tailwindcss@^3.4.0` as dev dependency
  - Build and watch scripts

### CSS Files

- **`src/hn_herald/static/css/input.css`** - Source CSS file (EDIT THIS)
  - Tailwind directives (@tailwind base, components, utilities)
  - Custom component classes:
    - `.btn-primary` - Primary button styling
    - `.btn-secondary` - Secondary button styling
    - `.form-input` - Form input styling
    - `.article-card` - Article card layout
    - `.tag-chip-*` - Tag styling with hover/focus states
    - `.htmx-indicator` - Loading indicator (hidden by default)
  - Accessibility utilities:
    - Focus visible styles
    - Screen reader only class (`.sr-only`)
    - Reduced motion support
  - Dark mode support (prefers-color-scheme)
  - Print styles

- **`src/hn_herald/static/css/styles.css`** - Generated CSS (DO NOT EDIT)
  - This file is created by running `npm run build:css`
  - It's the compiled output used by the application

### Build Scripts (Updated)

- **`Makefile`** - Added CSS build targets:
  - `make install-node` - Install npm dependencies
  - `make css` - Build CSS for production (minified)
  - `make css-watch` - Watch CSS for development
  - `make dev-css` - Alias for css-watch
  - `make clean` - Now also removes node_modules and styles.css

### Documentation

- **`docs/setup/tailwind-css-setup.md`** - Comprehensive setup guide
  - Installation instructions
  - Build process explanation
  - Configuration details
  - Development workflow
  - Troubleshooting guide
  - Best practices

## Features Implemented

### Mobile-First Design
- Base styles for 320px+ screens
- Progressive enhancement with breakpoints
- Touch-friendly interactions (48px minimum touch targets)
- Readable font sizes (16px+ body text)

### Custom Colors
- **Primary (Blue)**: Main theme color for buttons, links, highlights
- **Success (Green)**: Success states and positive feedback
- **Warning (Yellow)**: Warnings and cautions
- **Error (Red)**: Errors and validation messages

Each color has 11 shades (50-950) for flexibility.

### Accessibility
- WCAG 2.1 AA compliant color contrasts
- Keyboard navigation support (focus rings)
- Screen reader utilities
- Reduced motion preferences respected
- Touch-friendly target sizes

### HTMX Integration
- `.htmx-indicator` class for loading states
- Auto-shows during HTMX requests
- Hidden by default

### Dark Mode
- System preference detection (`prefers-color-scheme: dark`)
- Automatic theme switching
- All components support dark variants

### Performance
- Minified CSS for production
- PurgeCSS automatically removes unused styles
- Optimized for fast page loads

## Next Steps

After building the CSS, proceed with:

1. **Phase 6: Template Creation**
   - Create Jinja2 templates using the CSS classes
   - Implement HTMX integration
   - Build interactive components

2. **Phase 7: JavaScript Functionality**
   - Tag selector logic
   - Profile management (localStorage)
   - Form validation

3. **Phase 8: Testing**
   - E2E tests with Playwright
   - Accessibility compliance tests
   - Mobile viewport tests
   - Performance benchmarks

## Troubleshooting

### "npm: command not found"

Install Node.js from https://nodejs.org/ (LTS version recommended)

### CSS not updating in browser

1. Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
2. Check if watch mode is running (`make dev-css`)
3. Rebuild manually: `make css`

### Build fails

1. Check Node.js version: `node --version` (need v18+)
2. Delete and reinstall: `rm -rf node_modules && npm install`
3. Check for syntax errors in `input.css`

## References

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Design Document](docs/design/06-htmx-templates.md)
- [Full Setup Guide](docs/setup/tailwind-css-setup.md)
