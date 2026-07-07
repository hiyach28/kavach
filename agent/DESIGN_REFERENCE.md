# KAVACH v2 — Design Reference

Two surfaces, two moods, one system. v1's "Investigator's Terminal" identity was good — keep its DNA (dark command-center, condensed uppercase headers, mono data, severity color logic) and make it consistent and calmer.

## 1. Brand
- **Name story:** Kavach = armor/shield (Sanskrit). Shield protects citizens; Terminal arms investigators.
- **Logo direction:** minimal shield glyph with a network-node cutout. Works at 16px favicon.
- **Voice:** Terminal — precise, operational, zero fluff. Shield — calm, protective, plain language ("This looks like a scam. Police never video-call. Hang up."). Never alarmist, never jokey.

## 2. Tokens (single source of truth — implement as CSS variables in `styles/tokens.css`)

### Color — Terminal (dark)
```
--bg-base:        #0B0F14   /* near-black blue */
--bg-raised:      #121821
--bg-overlay:     #1A2230
--border-hairline:#243040
--text-primary:   #E6EDF3
--text-secondary: #8B98A9
--text-muted:     #5A6678
--accent:         #4FA3FF   /* interactive, links, focus */
--sev-critical:   #FF4D4D
--sev-high:       #FF9F1C
--sev-medium:     #FFD166
--sev-low:        #9BA9BB
--sev-verified:   #2EC27E   /* safe/legitimate */
--viz-semantic:   #B07CFF   /* semantic edges in graph */
--viz-infra:      #4FA3FF   /* infrastructure edges */
```
Severity colors are **semantic** — never use them decoratively. Risk bands: ≥70 critical, 40–69 high, <40 low, null → "REVIEW" (high).

### Color — Shield (light, citizen-facing)
```
--sh-bg:      #F7F9FC   --sh-card: #FFFFFF   --sh-text: #101828
--sh-danger:  #D92D20   --sh-warn: #DC6803   --sh-safe: #067647
--sh-accent:  #1D4ED8
```
High contrast (AA minimum), big type — assume sunlight, cheap screens, stressed users.

### Typography
- UI: **Inter** (400/500/600). Headers: **IBM Plex Sans Condensed** 600, uppercase, +0.04em tracking (v1's condensed-caps identity). Data/IDs/hashes: **IBM Plex Mono**.
- Scale: 12 / 13 (base, Terminal is dense) / 15 / 18 / 22 / 28. Shield base: 16.

### Spacing & shape
4px grid. Radii: 6 (controls), 10 (cards), 16 (Shield verdict card). Borders over shadows in Terminal; soft shadow (`0 1px 3px rgb(16 24 40 / .1)`) in Shield.

## 3. Layout patterns
- **Terminal shell:** left icon rail (module nav, 56px) · top status bar (env, live indicator, user) · main canvas · right dossier panel (persistent case context, collapsible). This is v1's shell — keep it.
- **Graph view:** canvas dominates; campaign list as left drawer; takedown brief slides in from right when a campaign is selected. Edge legend always visible (infra = blue solid, semantic = purple dashed).
- **Shield PWA:** single column, one primary action per screen. Verdict card = color-banded top edge + icon + one-sentence verdict + "why" expandable + one CTA ("Report to 1930" / "Block & report").

## 4. Signature moments (design these deliberately — they're the demo)
1. **Live intercept warning** (Shield): full-screen state change to danger red with haptic pulse, message in user's language, giant "End Call" guidance. Must read from 2 meters away on a phone.
2. **Case lands in graph** (Terminal): new node drops in with a brief pulse ring, edges draw in over ~600ms, campaign halo recolors. This is the flywheel made visible.
3. **Early-warning banner:** amber, top of Terminal, with sparkline of campaign velocity and projected victims. Dismissible, never modal.
4. **Evidence chain viewer:** vertical hash chain with link icons; verified segments get a green check cascade. Makes integrity *visible*.

## 5. Motion & states
150–250ms ease-out for UI, 600ms for graph choreography. Animate only meaning (state changes, new data), never decoration. Every view ships with empty / loading (skeleton, no spinners over 300ms) / error (typed message + retry) states — checked at the phase gate.

## 6. Accessibility
AA contrast both themes · full keyboard nav in Terminal · focus rings (`--accent`, 2px) · reduced-motion media query honored · Shield copy at CEFR-B1 reading level, localized, never idiomatic.

## 7. Anti-patterns (do not)
No emoji in UI · no more than 2 typefaces + mono · no red for anything except danger/critical · no charts without axis labels · no "AI magic" language anywhere — always show *why* a verdict was reached.
