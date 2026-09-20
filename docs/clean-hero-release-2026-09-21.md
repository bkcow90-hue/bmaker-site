# Clean hero release — 2026-09-21

## Approved scope

Keep the existing heading, subtext, one free diagnosis CTA, and original-aspect consultation portrait. Remove the hero case card and below-button proof/fee block. Preserve fee/disclaimer in diagnosis and form; relocate the existing ledger aggregate and source link to cases. Add a decorative concept architecture backdrop and finite motion, not an autoplay video.

## Search and accessibility safeguards

- Compared against `f41cac0`: title, H1 text, every meta tag, canonical, JSON-LD objects, and distinct anchor destinations are identical.
- robots.txt, sitemap.xml, llms.txt and llms-full.txt have no content changes.
- Main copy, proof, fees and case links remain ordinary HTML; no JS-only content or hidden search copy.
- Original portrait assets are unchanged. Aspect ratio and horizontal overflow checked at 320, 390, 768, 1024 and 1440px.
- All hero animations run once and end by 4.4 seconds. Text starts at 90% opacity, never hidden. Reduced-motion disables them.
- The source marker `home-proof` remains builder-managed in its new section; matching case cards and source IDs still update correctly.

## Performance experiment

Chromium, 390×844, CPU 4× slowdown, network 60ms latency and 200,000 bytes/s download, cache off, external services blocked, reduced-motion. Before and after HTML both supplied through the same browser interception method so document delivery is identical; resource requests use the local server and the same throttling. This is a controlled lab comparison, not real-user or Google field data.

Initial comparison accidentally used intercepted HTML for baseline and network HTML for the new version; that result is not a valid before/after claim. Repeated with symmetric delivery. Trace showed late discovery of decorative background; media-specific preload moved background discovery before stylesheet parsing. No duplicate mobile/desktop background download.

Final three runs (milliseconds):
- Baseline LCP: 1172, 1068, 1096. Median 1096.
- New LCP: 1188, 1128, 1104. Median 1128.
- CLS: 0 in all six runs.
- Resource transfer totals excluding document: 89,445 → 101,454 bytes (+12,009 including CSS/request overhead).

No claim of zero ranking change or guaranteed AI recommendation. Technical compatibility is verified; traffic and indexing outcomes require post-release platform data.

## Release gates

Builder chain must remain idempotent (two passes), full pytest with REQUIRE_BROWSER=1, conversion/analytics Node tests, whitespace check, independent read-only review, then live browser verification after main deployment. Evidence and asset provenance are documented separately in `hero-architecture-asset.md`.

Pre-merge result: builder second-pass churn 0; 82 pytest tests and 20 subtests passed; both Node suites passed; diff whitespace check clean. Independent review and follow-up preload review found no blocking issues.
