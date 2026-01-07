# Tailwind CSS Setup Guide

This guide explains how to set up and build Tailwind CSS for HN Herald's web interface.

## Prerequisites

- **Node.js** (v18 or higher)
- **npm** (comes with Node.js)

Check your versions:
```bash
node --version
npm --version
```

## Installation

### 1. Install Node.js Dependencies

Install Tailwind CSS as a development dependency:

```bash
npm install
```

Or using Make:
```bash
make install-node
```

This will install `tailwindcss` as specified in `package.json`.

## Building CSS

### Production Build (Minified)

Build the CSS for production with minification:

```bash
npm run build:css
```

Or using Make:
```bash
make css
```

This command:
- Reads `src/hn_herald/static/css/input.css`
- Processes Tailwind directives
- Outputs minified CSS to `src/hn_herald/static/css/styles.css`

### Development Build (Watch Mode)

For development, use watch mode to automatically rebuild on changes:

```bash
npm run watch:css
```

Or using Make:
```bash
make dev-css
```

Keep this running in a separate terminal while developing templates.

## File Structure

```
hn-herald/
├── tailwind.config.js              # Tailwind configuration
├── package.json                    # Node.js dependencies
├── src/hn_herald/static/css/
│   ├── input.css                   # Source CSS with Tailwind directives (EDIT THIS)
│   └── styles.css                  # Generated CSS (DO NOT EDIT - build artifact)
└── src/hn_herald/templates/        # HTML templates (referenced in config)
```

## Configuration

### tailwind.config.js

The Tailwind configuration includes:

**Content Paths**: Scans these files for class names
```javascript
content: ["./src/hn_herald/templates/**/*.html"]
```

**Custom Colors**:
- `primary` - Blue theme (buttons, links, highlights)
- `success` - Green (success states)
- `warning` - Yellow (warnings)
- `error` - Red (errors, validation)

**Dark Mode**:
```javascript
darkMode: 'media'  // Respects system preference
```

**Mobile-First Breakpoints**:
- `sm: 640px` - Large phones (landscape)
- `md: 768px` - Tablets
- `lg: 1024px` - Small laptops
- `xl: 1280px` - Desktops
- `2xl: 1536px` - Large screens

**Touch Target Utilities**:
- `min-h-12` - 48px minimum height
- `min-w-12` - 48px minimum width

### input.css

The input CSS file contains:

1. **Tailwind Directives**:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

2. **Custom Component Classes**:
   - `.btn-primary` - Primary button styling
   - `.btn-secondary` - Secondary button styling
   - `.form-input` - Form input styling
   - `.article-card` - Article card layout
   - `.tag-chip` - Tag chip styling
   - `.htmx-indicator` - Loading indicator (HTMX)

3. **Accessibility Features**:
   - Focus visible styles (keyboard navigation)
   - Screen reader only class (`.sr-only`)
   - Reduced motion support (`prefers-reduced-motion`)

4. **Print Styles**:
   - Hide interactive elements
   - Optimize article cards for printing

5. **Dark Mode Support**:
   - Automatic dark mode based on system preference

## Development Workflow

### Typical Development Setup

1. **Terminal 1**: Run the FastAPI server
   ```bash
   make dev
   ```

2. **Terminal 2**: Run Tailwind in watch mode
   ```bash
   make dev-css
   ```

3. **Edit files**:
   - Modify templates in `src/hn_herald/templates/`
   - Edit custom styles in `src/hn_herald/static/css/input.css`
   - Tailwind automatically rebuilds `styles.css`

### Adding Custom Styles

To add custom component classes, edit `input.css`:

```css
@layer components {
  .my-custom-class {
    @apply bg-blue-500 text-white p-4 rounded-lg;
    @apply hover:bg-blue-600 transition-colors;
  }
}
```

To add custom utilities:

```css
@layer utilities {
  .my-utility {
    @apply custom-property: value;
  }
}
```

## Production Deployment

### Build Process

1. **Install dependencies** (if not already installed):
   ```bash
   npm install
   ```

2. **Build minified CSS**:
   ```bash
   npm run build:css
   ```

3. **Verify output**:
   ```bash
   ls -lh src/hn_herald/static/css/styles.css
   ```

### Docker Build

The Dockerfile should include CSS build step:

```dockerfile
# Install Node.js and build CSS
RUN apt-get update && apt-get install -y nodejs npm
COPY package.json tailwind.config.js ./
COPY src/hn_herald/static/css/input.css ./src/hn_herald/static/css/
RUN npm install && npm run build:css
```

## Troubleshooting

### CSS Not Updating

**Problem**: Changes to templates or input.css not reflected

**Solutions**:
1. Check watch mode is running: `make dev-css`
2. Verify content paths in `tailwind.config.js`
3. Rebuild manually: `make css`
4. Clear browser cache: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

### Classes Not Generated

**Problem**: Tailwind classes in templates not appearing in output

**Solutions**:
1. Ensure template path is in `tailwind.config.js` content array
2. Use full class names (no dynamic concatenation)
3. Rebuild: `make css`

**Bad** (won't work):
```html
<div class="text-{{ color }}-500">  <!-- Dynamic class -->
```

**Good** (will work):
```html
<div class="text-blue-500">  <!-- Static class -->
```

### Build Errors

**Problem**: `npm run build:css` fails

**Solutions**:
1. Check Node.js version: `node --version` (need v18+)
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check file paths in `package.json` scripts
4. Verify `input.css` has valid CSS syntax

### Performance Issues

**Problem**: Large CSS file size

**Solutions**:
1. Use minified build: `npm run build:css` (not watch)
2. Remove unused custom CSS from `input.css`
3. Use Tailwind's purge feature (automatically enabled)
4. Check content paths cover only necessary files

## Best Practices

### 1. Use Tailwind Utilities First

Prefer Tailwind utility classes over custom CSS:

**Good**:
```html
<button class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
  Click me
</button>
```

**Better** (if repeated):
```css
/* input.css */
@layer components {
  .btn-primary {
    @apply bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700;
  }
}
```

```html
<button class="btn-primary">Click me</button>
```

### 2. Mobile-First Design

Write styles for mobile first, then add breakpoints:

```html
<!-- Mobile: full width, Tablet+: half width -->
<div class="w-full md:w-1/2">Content</div>

<!-- Mobile: stacked, Desktop: row -->
<div class="flex flex-col lg:flex-row">...</div>
```

### 3. Touch-Friendly Targets

Use minimum 48px touch targets for mobile:

```html
<button class="min-h-12 min-w-12 px-6 py-3">
  Touch-friendly button
</button>
```

### 4. Accessibility

Always include accessibility features:

```html
<!-- Focus rings for keyboard navigation -->
<button class="focus:ring-2 focus:ring-blue-500 focus:outline-none">

<!-- Screen reader text -->
<span class="sr-only">Close modal</span>

<!-- ARIA attributes -->
<button aria-label="Close" aria-expanded="false">
```

### 5. Dark Mode

Use `dark:` variant for dark mode support:

```html
<div class="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
  Adapts to system theme
</div>
```

## References

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Tailwind CLI Documentation](https://tailwindcss.com/docs/installation)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Mobile Touch Target Sizes](https://web.dev/accessible-tap-targets/)

## See Also

- [HTMX Templates Design](../design/06-htmx-templates.md)
- [FastAPI Endpoints](../design/05-fastapi-endpoints.md)
- [Project README](../../README.md)
