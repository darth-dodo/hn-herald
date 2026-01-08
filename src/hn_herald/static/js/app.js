/**
 * HN Herald - Minimal JavaScript with Theme Support
 */

const PROFILE_KEY = 'hn_herald_profile';
const THEME_KEY = 'hn_herald_theme';
const selectedTags = {
  'interest-tags': [],
  'disinterest-tags': []
};

// HN Fun Facts for loading screen
const HN_FUN_FACTS = [
  "Hacker News was created by Paul Graham in 2007 and is powered by Arc, a Lisp dialect.",
  "The orange color (#ff6600) used on HN is the same as the Y Combinator logo.",
  "HN's algorithm favors newer stories - upvotes from the first few hours count more than later ones.",
  "The fastest way to get to the front page? Post between 8-11 AM EST on weekdays.",
  "HN users have a 'karma' score based on upvotes received, but you can't see others' scores.",
  "The 'dang' account moderates HN and is known for thoughtful, even-handed community management.",
  "Comments on HN can be edited for 2 hours after posting, but edited comments are marked.",
  "HN has spawned many startups - Dropbox, Airbnb, and Stripe all launched on HN.",
  "The HN API is one of the most reliable public APIs - built on Firebase with 99.9% uptime.",
  "Stories need 5+ upvotes to appear on /new, and the algorithm penalizes clickbait titles.",
  "HN's minimalist design hasn't changed much since 2007 - function over form.",
  "The 'Ask HN' and 'Show HN' tags were community-driven additions that became official.",
  "HN's source code is open source and available at github.com/HackerNews/API.",
  "The median HN story gets ~3 upvotes. Getting to the front page requires ~100-200 upvotes.",
  "HN readers prefer substance over sensationalism - detailed technical posts perform best."
];

let funFactInterval = null;

// Theme Management
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
  updateThemeSwitcher(theme);
  console.log(`Theme set to: ${theme}`);
}

function loadTheme() {
  const savedTheme = localStorage.getItem(THEME_KEY) || 'hn';
  setTheme(savedTheme);
}

function updateThemeSwitcher(currentTheme) {
  const switcher = document.getElementById('theme-switcher');
  if (!switcher) return;

  const themes = ['hn', 'ocean', 'dark'];
  switcher.innerHTML = themes.map(theme => {
    if (theme === currentTheme) {
      return `<span style="color: var(--header-text); font-weight: bold; font-size: 9pt;">${theme}</span>`;
    }
    return `<a href="#" onclick="setTheme('${theme}'); return false;" style="color: var(--header-text); text-decoration: none; font-size: 9pt;">${theme}</a>`;
  }).join(' | ');
}

// Load theme immediately (before DOMContentLoaded)
loadTheme();

// Add tag
function addTag(fieldId, tag) {
  tag = tag.trim();
  if (!tag || tag.length < 2) return;

  const tags = selectedTags[fieldId] || [];
  if (tags.some(t => t.toLowerCase() === tag.toLowerCase())) return;

  tags.push(tag);
  selectedTags[fieldId] = tags;

  updateTagDisplay(fieldId);
  updateHiddenInput(fieldId, tags);
}

// Remove tag
function removeTag(fieldId, tag) {
  const tags = selectedTags[fieldId] || [];
  selectedTags[fieldId] = tags.filter(t => t !== tag);

  updateTagDisplay(fieldId);
  updateHiddenInput(fieldId, selectedTags[fieldId]);
}

// Remove all tags
function removeAllTags(fieldId) {
  selectedTags[fieldId] = [];
  updateTagDisplay(fieldId);
  updateHiddenInput(fieldId, []);
}

// Update tag display
function updateTagDisplay(fieldId) {
  const selectedDiv = document.getElementById(`${fieldId}-selected`);
  if (!selectedDiv) return;

  const tags = selectedTags[fieldId] || [];

  if (tags.length === 0) {
    selectedDiv.innerHTML = '<span style="color: var(--secondary-color); font-size: 9pt;">Selected: (none) </span><a href="#" onclick="removeAllTags(\'' + fieldId + '\'); return false;" style="color: var(--secondary-color); font-size: 8pt; text-decoration: none;">[remove all]</a>';
    return;
  }

  const tagList = tags.map(tag =>
    `<span class="hn-tag-selected">${tag} <a href="#" class="hn-tag-remove" onclick="removeTag('${fieldId}', '${tag}'); return false;">[×]</a></span>`
  ).join(' ');

  selectedDiv.innerHTML = '<span style="color: var(--secondary-color); font-size: 9pt;">Selected: </span>' + tagList + ' <a href="#" onclick="removeAllTags(\'' + fieldId + '\'); return false;" style="color: var(--secondary-color); font-size: 8pt; text-decoration: none; margin-left: 8px;">[remove all]</a>';
}

// Update hidden input
function updateHiddenInput(fieldId, tags) {
  const hiddenInput = document.getElementById(`${fieldId}-hidden`);
  if (!hiddenInput) return;
  hiddenInput.value = tags.join(',');
}

// Show random fun fact
function showRandomFunFact() {
  const factDiv = document.querySelector('#fun-fact div:last-child');
  if (!factDiv) return;

  const randomFact = HN_FUN_FACTS[Math.floor(Math.random() * HN_FUN_FACTS.length)];
  factDiv.textContent = randomFact;
}

// Update pipeline stage message
function updatePipelineStage(message) {
  const statusDiv = document.querySelector('#loading > div:nth-child(2)');
  if (statusDiv) {
    statusDiv.textContent = message;
  }
}

// Start fun facts rotation
function startFunFacts() {
  showRandomFunFact();
  // Rotate fun facts every 5 seconds
  return setInterval(showRandomFunFact, 5000);
}

// Mock digest generation for development
async function generateMockDigest(funFactInterval, loadingDiv, buttonDiv, resultsDiv, payload) {
  const stages = [
    { message: 'Fetching HN stories...', delay: 500 },
    { message: 'Extracting article content...', delay: 1000 },
    { message: 'Filtering articles...', delay: 500 },
    { message: 'Summarizing with AI...', delay: 2000 },
    { message: 'Scoring relevance...', delay: 1000 },
    { message: 'Ranking articles...', delay: 500 }
  ];

  // Simulate pipeline stages
  for (const stage of stages) {
    updatePipelineStage(stage.message);
    await new Promise(resolve => setTimeout(resolve, stage.delay));
  }

  // Mock digest data
  const mockDigest = {
    articles: [
      {
        story_id: 1,
        title: "Example Article: Building Real-time Applications with SSE",
        url: "https://example.com/article1",
        hn_url: "https://news.ycombinator.com/item?id=1",
        hn_score: 450,
        summary: "This article explores Server-Sent Events (SSE) as a lightweight alternative to WebSockets for real-time updates. It covers implementation patterns, browser compatibility, and use cases where SSE excels.",
        key_points: ["SSE provides unidirectional server-to-client streaming", "Simpler protocol than WebSockets for many use cases", "Built-in reconnection and event ID tracking"],
        tech_tags: ["sse", "real-time", "web-development", "javascript"],
        relevance_score: 0.85,
        relevance_reason: "Matches interest in JavaScript and web development patterns",
        final_score: 0.82
      },
      {
        story_id: 2,
        title: "Mock Data Strategies for Frontend Development",
        url: "https://example.com/article2",
        hn_url: "https://news.ycombinator.com/item?id=2",
        hn_score: 380,
        summary: "A comprehensive guide to implementing mock data systems in frontend applications. Discusses strategies for development speed, testing, and offline functionality.",
        key_points: ["Mock data accelerates development iteration", "Enables offline development mode", "Facilitates comprehensive testing scenarios"],
        tech_tags: ["testing", "development", "frontend", "mock-data"],
        relevance_score: 0.75,
        relevance_reason: "Relevant to frontend development practices",
        final_score: 0.72
      }
    ],
    stats: {
      stories_fetched: 50,
      articles_extracted: 35,
      articles_summarized: 30,
      articles_scored: 25,
      articles_returned: 2,
      errors: 0,
      generation_time_ms: 5500
    },
    timestamp: new Date().toISOString(),
    profile_summary: {
      interests: payload.profile.interest_tags,
      disinterests: payload.profile.disinterest_tags,
      min_score: payload.profile.min_score,
      max_articles: payload.profile.max_articles
    }
  };

  // Hide loading and show results
  if (funFactInterval) clearInterval(funFactInterval);
  if (loadingDiv) loadingDiv.style.display = 'none';
  if (buttonDiv) buttonDiv.style.display = 'block';

  console.log('🎭 Mock digest generated:', mockDigest);
  console.log('Has stats?', !!mockDigest.stats, 'Stats:', mockDigest.stats);

  if (resultsDiv) {
    displayDigestResults(mockDigest);
  }
}

// Generate digest using Server-Sent Events
// Mock mode flag - set to true to use mock data for development
const MOCK_MODE = window.location.search.includes('mock=true');

// Global abort controller for canceling digest generation
let currentAbortController = null;
let currentFunFactInterval = null;

function abortDigest() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  if (currentFunFactInterval) {
    clearInterval(currentFunFactInterval);
    currentFunFactInterval = null;
  }

  // Reset UI
  const buttonDiv = document.querySelector('.hn-button');
  const loadingDiv = document.getElementById('loading');
  if (loadingDiv) loadingDiv.style.display = 'none';
  if (buttonDiv) buttonDiv.style.display = 'block';

  console.log('Digest generation cancelled by user');
}

async function generateDigest() {
  let funFactInterval = null;

  // Create new abort controller for this request
  currentAbortController = new AbortController();

  try {
    // Save profile to localStorage
    saveProfile();

    // Hide the button and show loading indicator with fun facts
    const buttonDiv = document.querySelector('.hn-button');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');

    if (buttonDiv) buttonDiv.style.display = 'none';
    if (loadingDiv) {
      loadingDiv.style.display = 'block';
      funFactInterval = startFunFacts();
      currentFunFactInterval = funFactInterval;
      updatePipelineStage('Initializing pipeline...');
    }

    // Create the JSON payload
    const payload = {
      profile: {
        interest_tags: selectedTags['interest-tags'] || [],
        disinterest_tags: selectedTags['disinterest-tags'] || [],
        min_score: parseFloat(document.getElementById('min-score').value),
        max_articles: parseInt(document.getElementById('article-limit').value),
        fetch_type: document.getElementById('story-type').value,
        fetch_count: parseInt(document.getElementById('story-count').value)
      },
      // Use backend mock mode when ?mock=true is in URL
      mock: MOCK_MODE
    };

    console.log('Sending digest request:', payload);
    if (MOCK_MODE) {
      console.log('🎭 MOCK MODE: Using backend mock data');
    }

    // Use fetch to POST the request and get the stream
    const response = await fetch('/api/v1/digest/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: currentAbortController.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Read the stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete message in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6));

            if (data.stage === 'error') {
              throw new Error(data.message);
            } else if (data.stage === 'complete') {
              // Hide loading and show results
              if (funFactInterval) clearInterval(funFactInterval);
              currentFunFactInterval = null;
              currentAbortController = null;
              if (loadingDiv) loadingDiv.style.display = 'none';
              if (buttonDiv) buttonDiv.style.display = 'block';

              console.log('Digest generated successfully:', data.digest);
              console.log('Has stats?', !!data.digest.stats, 'Stats:', data.digest.stats);
              if (resultsDiv && data.digest.articles) {
                displayDigestResults(data.digest);
              }
            } else if (data.message) {
              // Update the pipeline stage message
              updatePipelineStage(data.message);
            }
          } catch (parseError) {
            console.error('Failed to parse SSE data:', parseError);
          }
        }
      }
    }

  } catch (error) {
    // Don't show error for user-initiated abort
    if (error.name === 'AbortError') {
      console.log('Digest generation aborted');
      return;
    }

    console.error('Failed to generate digest:', error);
    const buttonDiv = document.querySelector('.hn-button');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');

    if (funFactInterval) clearInterval(funFactInterval);
    currentFunFactInterval = null;
    currentAbortController = null;
    if (loadingDiv) loadingDiv.style.display = 'none';
    if (buttonDiv) buttonDiv.style.display = 'block';
    if (resultsDiv) {
      resultsDiv.innerHTML = `<div style="color: #cc0000; padding: 16px;">Error: ${error.message}</div>`;
    }
  }
}

// Display digest results
function displayDigestResults(data) {
  console.log('displayDigestResults called with:', data);
  console.log('Has stats?', !!data.stats, 'Stats object:', data.stats);

  const resultsDiv = document.getElementById('results');
  if (!resultsDiv) return;

  let html = '<div class="hn-digest">';
  html += `<div class="hn-section-title">Your Personalized Digest (${data.articles.length} articles)</div>`;

  data.articles.forEach((article, index) => {
    html += `
      <div class="hn-article" style="margin-bottom: 16px; padding: 12px; border: 1px solid var(--border-color); background: var(--selected-bg);">
        <div style="font-weight: bold; margin-bottom: 4px;">
          ${index + 1}. <a href="${article.url}" target="_blank" rel="noopener" style="color: var(--primary-color);">${article.title}</a>
        </div>
        <div style="font-size: 9pt; color: var(--secondary-color); margin-bottom: 8px;">
          ${article.hn_score} points |
          <a href="${article.hn_url}" target="_blank" rel="noopener" style="color: var(--secondary-color);">discuss</a> |
          relevance: ${(article.relevance_score * 100).toFixed(0)}%
        </div>
        <div style="font-size: 9pt; margin-bottom: 8px;">${article.summary}</div>
        <div style="font-size: 9pt; color: var(--secondary-color);">
          <strong>Key points:</strong> ${article.key_points.join(' • ')}
        </div>
        <div style="font-size: 9pt; color: var(--secondary-color); margin-top: 4px;">
          <strong>Tags:</strong> ${article.tech_tags.join(', ')}
        </div>
      </div>
    `;
  });

  // Add pipeline statistics summary
  if (data.stats) {
    html += '<div class="hn-separator"></div>';
    html += '<div class="hn-section-title">📊 Pipeline Statistics</div>';
    html += '<div style="background: var(--selected-bg); border: 1px solid var(--border-color); padding: 12px; margin-bottom: 16px;">';

    // Processing funnel
    html += '<div style="font-size: 10pt; margin-bottom: 12px;">';
    html += '<div style="font-weight: bold; margin-bottom: 8px; color: var(--text-color);">Processing Funnel:</div>';
    html += '<div style="font-size: 9pt; color: var(--secondary-color); margin-left: 12px;">';
    html += `→ <strong>${data.stats.stories_fetched}</strong> stories fetched from HN<br>`;
    html += `→ <strong>${data.stats.articles_extracted}</strong> articles extracted (${((data.stats.articles_extracted / data.stats.stories_fetched) * 100).toFixed(1)}% success)<br>`;
    html += `→ <strong>${data.stats.articles_summarized}</strong> articles summarized with AI<br>`;
    html += `→ <strong>${data.stats.articles_scored}</strong> articles scored for relevance<br>`;
    html += `→ <strong>${data.stats.articles_returned}</strong> articles in final digest`;
    html += '</div>';
    html += '</div>';

    // Performance metrics
    html += '<div style="font-size: 10pt; margin-bottom: 12px;">';
    html += '<div style="font-weight: bold; margin-bottom: 8px; color: var(--text-color);">Performance:</div>';
    html += '<div style="font-size: 9pt; color: var(--secondary-color); margin-left: 12px;">';
    html += `⚡ Generation time: <strong>${(data.stats.generation_time_ms / 1000).toFixed(2)}s</strong><br>`;
    html += `⚡ Avg time per article: <strong>${(data.stats.generation_time_ms / data.stats.articles_returned).toFixed(0)}ms</strong><br>`;
    html += `⚡ Processing rate: <strong>${((data.stats.articles_summarized / (data.stats.generation_time_ms / 1000))).toFixed(1)} articles/sec</strong>`;
    html += '</div>';
    html += '</div>';

    // Quality metrics
    html += '<div style="font-size: 10pt;">';
    html += '<div style="font-weight: bold; margin-bottom: 8px; color: var(--text-color);">Quality:</div>';
    html += '<div style="font-size: 9pt; color: var(--secondary-color); margin-left: 12px;">';
    const extractionRate = ((data.stats.articles_extracted / data.stats.stories_fetched) * 100).toFixed(1);
    const filterRate = ((data.stats.articles_returned / data.stats.articles_scored) * 100).toFixed(1);
    html += `✓ Extraction success rate: <strong>${extractionRate}%</strong><br>`;
    html += `✓ Filter pass rate: <strong>${filterRate}%</strong> (min_score=${data.profile_summary.min_score})<br>`;
    if (data.stats.errors > 0) {
      html += `⚠ Errors encountered: <strong>${data.stats.errors}</strong>`;
    } else {
      html += `✓ No errors encountered`;
    }
    html += '</div>';
    html += '</div>';

    html += '</div>';
  }

  html += '</div>';
  resultsDiv.innerHTML = html;
}

// Save profile to localStorage
function saveProfile() {
  try {
    const profile = {
      interest_tags: selectedTags['interest-tags'],
      disinterest_tags: selectedTags['disinterest-tags'],
      story_type: document.getElementById('story-type').value,
      story_count: parseInt(document.getElementById('story-count').value),
      article_limit: parseInt(document.getElementById('article-limit').value),
      min_score: parseFloat(document.getElementById('min-score').value),
      last_updated: new Date().toISOString()
    };
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    console.log('Profile saved');
    return profile;
  } catch (error) {
    console.error('Failed to save profile:', error);
    return null;
  }
}

// Load profile on page load
function loadProfile() {
  try {
    const profileJSON = localStorage.getItem(PROFILE_KEY);
    if (!profileJSON) return null;

    const profile = JSON.parse(profileJSON);

    // Populate tags
    if (profile.interest_tags) {
      selectedTags['interest-tags'] = profile.interest_tags;
      updateTagDisplay('interest-tags');
      updateHiddenInput('interest-tags', profile.interest_tags);
    }

    if (profile.disinterest_tags) {
      selectedTags['disinterest-tags'] = profile.disinterest_tags;
      updateTagDisplay('disinterest-tags');
      updateHiddenInput('disinterest-tags', profile.disinterest_tags);
    }

    // Populate form fields
    if (profile.story_type) document.getElementById('story-type').value = profile.story_type;
    if (profile.story_count) document.getElementById('story-count').value = profile.story_count;
    if (profile.article_limit) document.getElementById('article-limit').value = profile.article_limit;
    if (profile.min_score) document.getElementById('min-score').value = profile.min_score;

    console.log('Profile loaded');
    return profile;
  } catch (error) {
    console.error('Failed to load profile:', error);
    return null;
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('HN Herald app initialized successfully');
  loadProfile();
});
