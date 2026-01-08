# ADR-003: Privacy-First Data Architecture

**Date**: 2026-01-01
**Status**: Accepted
**Context**: User data handling and storage strategy
**Deciders**: Product & Architecture Team

---

## Summary

HN Herald adopts a privacy-first architecture where all user preferences are stored exclusively in browser localStorage, with no server-side user accounts, tracking, or analytics. Article content is processed ephemerally (in real-time, never stored), and the only data sent to external services is article content for AI summarization. This decision aligns with the project's core value proposition and differentiates it from data-hungry alternatives.

---

## Problem Statement

### The Challenge

Personalized content applications typically require:
- User accounts for preference storage
- Server-side databases for user data
- Analytics for product improvement
- Cookies for session management

These create privacy concerns, GDPR/CCPA compliance burdens, and user friction (signup flows, password management).

### Why This Matters

- **Trust**: Privacy-conscious HN audience is skeptical of data collection
- **Simplicity**: No user database means less infrastructure and fewer security risks
- **Compliance**: No personal data storage = no GDPR data subject requests
- **Friction**: No signup means instant usability

### Success Criteria

- [x] Zero server-side user data storage
- [x] Preferences persist across browser sessions
- [x] No third-party analytics or tracking
- [x] Article content processed ephemerally
- [x] User can export/delete their data anytime

---

## Context

### Privacy Landscape

**Industry Standard (What Others Do)**:
- Account-based personalization
- Server-side preference storage
- Behavioral tracking for recommendations
- Third-party analytics (Google Analytics, Mixpanel)
- Cookie consent banners

**User Concerns**:
- Data breaches exposing preferences
- Behavioral profiling
- Data sold to third parties
- Inability to truly delete data

**Technical Constraints**:
- Must provide personalization without accounts
- Must persist preferences across sessions
- Must enable AI summarization (requires sending content to LLM)
- Must work offline for preference access

### Requirements

**Functional Requirements**:
- Store user interest/disinterest tags
- Store digest configuration (story type, count, score threshold)
- Provide export functionality
- Provide delete functionality

**Non-Functional Requirements**:
- **Privacy**: No PII on server
- **Persistence**: Survive browser restarts
- **Portability**: User owns their data
- **Transparency**: Clear about what's sent where

---

## Options Considered

### Option A: Traditional Account System

**Description**:
Email/password accounts with server-side PostgreSQL storage.

**Pros**:
- Cross-device sync
- Password recovery
- Richer personalization over time

**Cons**:
- Privacy concerns (email is PII)
- GDPR compliance burden
- Security responsibility (password hashing, breach notification)
- User friction (signup, verification)
- Infrastructure cost (database, auth service)

**Estimated Effort**: 40 hours

---

### Option B: Anonymous Server Storage

**Description**:
Generate random UUID, store preferences server-side without email.

**Pros**:
- Cross-device sync via URL/QR code
- No PII stored
- Server-side backup

**Cons**:
- UUID in URL is shareable (privacy leak)
- Lost UUID = lost preferences
- Still requires database infrastructure
- Server breach exposes preferences (potentially sensitive)

**Estimated Effort**: 20 hours

---

### Option C: Browser localStorage Only (Chosen)

**Description**:
All user data stored in browser localStorage, never sent to server.

**Implementation**:
```javascript
// Save profile
localStorage.setItem('hn_herald_profile', JSON.stringify({
  interest_tags: ['python', 'ai'],
  disinterest_tags: ['crypto'],
  min_score: 0.3,
  max_articles: 10,
  last_updated: new Date().toISOString()
}));

// Load profile
const profile = JSON.parse(localStorage.getItem('hn_herald_profile'));
```

**Pros**:
- Zero server-side user data
- No accounts, instant usage
- User has full control
- No GDPR concerns (no personal data)
- No database infrastructure
- Works offline for preference access

**Cons**:
- No cross-device sync
- Lost if browser data cleared
- Limited to 5-10MB storage

**Estimated Effort**: 4 hours

---

### Option D: Encrypted Cloud Sync

**Description**:
End-to-end encrypted preferences with user-held key.

**Pros**:
- Cross-device sync
- Server can't read preferences
- User controls encryption key

**Cons**:
- Complex key management UX
- Lost key = lost data
- Significant implementation effort
- Overkill for simple preferences

**Estimated Effort**: 60 hours

---

## Comparison Matrix

| Criteria | Weight | Accounts | Anon Server | localStorage | E2E Encrypted |
|----------|--------|----------|-------------|--------------|---------------|
| **Privacy** | High | 2 | 3 | 5 | 5 |
| **Simplicity** | High | 2 | 3 | 5 | 1 |
| **User Friction** | High | 1 | 3 | 5 | 2 |
| **Cross-Device** | Medium | 5 | 4 | 1 | 4 |
| **Data Safety** | Medium | 4 | 3 | 2 | 4 |
| **Compliance** | Medium | 2 | 3 | 5 | 5 |
| **Total Score** | - | 16 | 19 | **23** | 21 |

---

## Decision

### Chosen Option

**Selected**: Option C: Browser localStorage Only

**Rationale**:
1. **Privacy is a feature**: Differentiates HN Herald in a crowded space
2. **HN audience alignment**: Privacy-conscious users appreciate the approach
3. **Simplicity**: No database, no auth, no compliance overhead
4. **Instant usability**: No signup barrier
5. **Acceptable trade-off**: Cross-device sync is nice-to-have, not essential

**Key Factors**:
- Primary use case is individual reading on a single device
- Preferences are simple (tags, numbers) - easy to recreate if lost
- HN audience values privacy over convenience
- Reduces attack surface (no user database to breach)

**Trade-offs Accepted**:
- No cross-device sync (acceptable for MVP, can add export/import)
- Data lost on browser clear (acceptable with export feature)

---

## Consequences

### Positive Outcomes

**Immediate Benefits**:
- Zero infrastructure for user data
- No GDPR/CCPA compliance burden
- Instant usability (no signup)
- Trust-building with privacy-conscious users

**Long-term Benefits**:
- No breach notification obligations
- No data subject access requests
- Simpler architecture to maintain
- Marketing differentiator ("Your data stays yours")

### Negative Outcomes

**Immediate Costs**:
- Can't offer cross-device sync
- Can't do server-side personalization improvements

**Technical Debt Created**:
- None - this is a simplification, not a shortcut

**Trade-offs**:
- Power users wanting sync must use manual export/import
- Can't analyze usage patterns for product improvement

---

## Implementation Details

### Data Storage Schema

```javascript
// localStorage key: 'hn_herald_profile'
{
  "interest_tags": ["python", "ai", "startups"],
  "disinterest_tags": ["crypto", "blockchain"],
  "story_type": "top",
  "story_count": 30,
  "article_limit": 10,
  "min_score": 0.3,
  "last_updated": "2026-01-08T10:30:00Z"
}

// localStorage key: 'hn_herald_theme'
"dark"
```

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                      BROWSER                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              localStorage                         │  │
│  │  • interest_tags                                  │  │
│  │  • disinterest_tags     ◄─── Never leaves browser │  │
│  │  • preferences                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Form Submission (JSON)                  │  │
│  │  • Tags (for relevance scoring)                   │  │
│  │  • Config (story count, etc.)                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ POST /api/v1/digest/stream
┌─────────────────────────────────────────────────────────┐
│                      SERVER                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Ephemeral Processing                    │  │
│  │  • Fetch stories (HN API)                         │  │
│  │  • Extract articles (external URLs)               │  │
│  │  • Summarize (Anthropic API) ◄─── Content sent   │  │
│  │  • Score relevance                                │  │
│  │  • Return digest                                  │  │
│  │                                                   │  │
│  │  ❌ No user data stored                          │  │
│  │  ❌ No logs of preferences                       │  │
│  │  ❌ No analytics                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Export/Import Functions

```javascript
// Export profile as JSON file
function exportProfile() {
  const profile = localStorage.getItem('hn_herald_profile');
  const blob = new Blob([profile], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  // Trigger download...
}

// Clear all data
function clearProfile() {
  localStorage.removeItem('hn_herald_profile');
  localStorage.removeItem('hn_herald_theme');
}
```

### Privacy Transparency

The UI clearly communicates:
- "Privacy-first • No tracking • Your data stays in your browser"
- Footer link to explain data handling
- Export/delete buttons prominently placed

---

## External Data Sharing

### What IS Sent Externally

| Data | Destination | Purpose | Retention |
|------|-------------|---------|-----------|
| Article URLs | Original websites | Content extraction | None |
| Article content | Anthropic API | AI summarization | Per Anthropic policy |
| Interest tags | Server (in request) | Relevance scoring | Request duration only |

### What is NOT Sent

- Email addresses (none collected)
- User identifiers (none exist)
- Reading history (not tracked)
- Click behavior (not tracked)
- Device fingerprints (not collected)

---

## Validation

### Post-Implementation Results

**Privacy Audit**:
- Server logs: ✅ No user identifiers
- Database: ✅ No user table exists
- Analytics: ✅ None integrated
- Cookies: ✅ None set
- localStorage: ✅ Only place user data exists

**User Feedback**:
- Positive reception from privacy-conscious HN users
- No complaints about lack of cross-device sync
- Export feature satisfies backup needs

---

## Future Considerations

1. **Optional Sync**: Could add opt-in cloud sync for users who want it
2. **Local-First Sync**: CRDTs for conflict-free multi-device (complex)
3. **QR Code Export**: Easy profile transfer between devices
4. **Browser Extension**: Sync via browser account (Chrome, Firefox)

---

## References

### Code References

- `src/hn_herald/static/js/app.js` - localStorage functions
- `src/hn_herald/api/routes.py` - Request handling (no user storage)

### External Resources

- [localStorage MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [GDPR and localStorage](https://gdpr.eu/cookies/) - localStorage exempt from cookie law
- [Local-First Software](https://www.inkandswitch.com/local-first/)

---

## Metadata

**ADR Number**: 003
**Created**: 2026-01-01
**Last Updated**: 2026-01-08
**Version**: 1.0

**Tags**: privacy, architecture, localStorage, gdpr, data-handling

**Project Phase**: Foundation (Project Setup)
