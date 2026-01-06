/**
 * HN Herald - Minimal JavaScript with Theme Support
 */

const PROFILE_KEY = 'hn_herald_profile';
const THEME_KEY = 'hn_herald_theme';
const selectedTags = {
  'interest-tags': [],
  'disinterest-tags': []
};

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

// Save profile before form submission
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
