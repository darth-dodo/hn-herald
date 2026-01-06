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

// Start fun facts rotation
function startFunFacts() {
  showRandomFunFact();
  funFactInterval = setInterval(showRandomFunFact, 5000); // Change every 5 seconds
}

// Stop fun facts rotation
function stopFunFacts() {
  if (funFactInterval) {
    clearInterval(funFactInterval);
    funFactInterval = null;
  }
}

// Generate digest using fetch API
async function generateDigest() {
  try {
    // Save profile to localStorage
    saveProfile();

    // Show loading indicator with fun facts
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    if (loadingDiv) {
      loadingDiv.style.display = 'block';
      startFunFacts();
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
      }
    };

    console.log('Sending digest request:', payload);

    // Make the API request
    const response = await fetch('/api/v1/digest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    // Hide loading indicator and stop fun facts
    stopFunFacts();
    if (loadingDiv) loadingDiv.style.display = 'none';

    if (!response.ok) {
      const errorData = await response.json();
      console.error('API error:', errorData);
      if (resultsDiv) {
        resultsDiv.innerHTML = `<div style="color: #cc0000; padding: 16px;">Error: ${errorData.detail || 'Failed to generate digest'}</div>`;
      }
      return;
    }

    // Parse and display the response
    const data = await response.json();
    console.log('Digest generated successfully:', data);

    // Display results
    if (resultsDiv && data.articles) {
      displayDigestResults(data);
    }
  } catch (error) {
    console.error('Failed to generate digest:', error);
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    stopFunFacts();
    if (loadingDiv) loadingDiv.style.display = 'none';
    if (resultsDiv) {
      resultsDiv.innerHTML = `<div style="color: #cc0000; padding: 16px;">Error: ${error.message}</div>`;
    }
  }
}

// Display digest results
function displayDigestResults(data) {
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
