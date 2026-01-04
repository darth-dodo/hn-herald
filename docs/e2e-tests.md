# E2E Tests for HN Herald

Manual E2E test scenarios using Playwright MCP. Run these interactively with Claude Code.

## Prerequisites

```bash
# Ensure the dev server is running
uv run uvicorn hn_herald.main:app --reload --port 8000
```

---

## Test 1: Homepage Loads

**Goal**: Verify the homepage renders correctly.

**Steps**:
1. Navigate to `http://localhost:8000`
2. Take a screenshot
3. Verify page title contains "HN Herald"

**Expected**: Homepage loads with header and navigation.

---

## Test 2: Fetch Top Stories from HN API

**Goal**: Verify HN API integration works.

**Steps**:
1. Navigate to `https://hacker-news.firebaseio.com/v0/topstories.json`
2. Verify response is a JSON array of numbers
3. Take first story ID and fetch `https://hacker-news.firebaseio.com/v0/item/{id}.json`
4. Verify story has `title`, `by`, `score` fields

**Expected**: API returns valid story data.

---

## Test 3: Article Extraction - Wikipedia

**Goal**: Verify article extraction works on a stable page.

**Steps**:
1. Navigate to `https://en.wikipedia.org/wiki/Extreme_programming`
2. Take a screenshot
3. Verify page contains "Extreme programming" heading
4. Check that article content has `<article>` or `#mw-content-text` with paragraphs

**Expected**: Wikipedia article loads with extractable content about XP methodology.

---

## Test 4: Blocked Domain Detection

**Goal**: Verify blocked domains are identified correctly.

**Steps**:
1. Navigate to `https://twitter.com` (will likely show login)
2. Take a screenshot
3. Note: ArticleLoader should skip this domain

**Expected**: Twitter requires login, confirming it should be blocked.

---

## Test 5: Real Article Extraction

**Goal**: Test extraction on a real tech article.

**Steps**:
1. Navigate to `https://news.ycombinator.com`
2. Find a story link (not GitHub, Twitter, YouTube)
3. Click on external article link
4. Take a screenshot
5. Verify article has `<article>` or `<main>` tag with content

**Expected**: Real articles have extractable content.

---

## Test 6: Ask HN Page Structure

**Goal**: Verify Ask HN posts have text content.

**Steps**:
1. Navigate to `https://news.ycombinator.com/ask`
2. Click on an "Ask HN:" story
3. Take a screenshot
4. Verify the post has `.fatitem` with text content (not external URL)

**Expected**: Ask HN posts have inline text, no external URL.

---

## Test 7: PDF Link Detection

**Goal**: Verify PDF links are identifiable.

**Steps**:
1. Navigate to `https://arxiv.org/abs/2301.00001`
2. Find the PDF link
3. Verify it ends with `.pdf`

**Expected**: PDF links are detectable by extension.

---

## Test 8: Mobile Responsiveness

**Goal**: Verify pages render on mobile viewport.

**Steps**:
1. Resize browser to 375x667 (iPhone SE)
2. Navigate to `https://news.ycombinator.com`
3. Take a screenshot
4. Verify content is readable without horizontal scroll

**Expected**: HN renders acceptably on mobile.

---

## Running Tests with Playwright MCP

Ask Claude Code to run any test above:

```
Run Test 3 using Playwright MCP
```

Claude will:
1. Use `mcp__playwright__browser_navigate` to open the URL
2. Use `mcp__playwright__browser_snapshot` to capture the page
3. Use `mcp__playwright__browser_take_screenshot` for visual verification
4. Report pass/fail based on expected outcomes

---

## Quick Test Commands

```
# Test homepage
Navigate to http://localhost:8000 and take a screenshot

# Test HN API
Navigate to https://hacker-news.firebaseio.com/v0/topstories.json and show the content

# Test article extraction
Navigate to https://en.wikipedia.org/wiki/Extreme_programming, take a screenshot, and extract the main content text
```
