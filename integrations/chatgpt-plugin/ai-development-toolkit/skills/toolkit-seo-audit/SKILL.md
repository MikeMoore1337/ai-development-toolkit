---
name: toolkit-seo-audit
description: "Conduct evidence-based technical and content SEO audits for pages or sites: crawlability, indexing, canonical, sitemap, robots/noindex, search intent, internal links, structured data, mobile signals, Core Web Vitals, multilingual/local SEO. Проверь SEO сайта без придуманных позиций."
---

# SEO Audit (FULFILL_REQUEST)

**Triggers:** "проверь SEO сайта", "страницы не индексируются", "помоги с поисковой оптимизацией", "SEO audit my site". This is actual audit work, **not** an exportable prompt.

1. Inspect actual supplied pages, URLs, files, audience, geography/language and current evidence; avoid assuming Search Console, live crawler or indexing access.
2. Audit technical discovery: HTTP status and redirects, robots.txt versus noindex, canonical, XML sitemap, internal links, JS rendering, mobile usability, hreflang and duplicates. A sitemap does not guarantee indexation. An indexable page does not guarantee ranking.
3. Review page purpose, search intent, title/meta description, headings, helpful content, image alt text, internal links and content duplication. Avoid keyword stuffing and fabricated testimonials.
4. Recommend structured data only for factual content really present on the page. JSON-LD validity and rich-result eligibility do **not** guarantee appearance or ranking.
5. For actual Core Web Vitals, traffic, positions and conversions require measured evidence and dates; otherwise classify as `NOT_VERIFIED`. Treat observed findings as `CONFIRMED` and possible issues as `HYPOTHESIS`.
6. Report `priority P0-P3 | URL | observed evidence | confidence | impact hypothesis | fix | validation`. P0 requires a real significant indexing block; do not fabricate errors. Offer a measured follow-up through Search Console when data is available.
7. Do not edit/publish external sites or use paid APIs without explicit user authority. Major visual redesigns continue through UX/UI Design Orchestra and visual approval.

[Evidence checklist](references/CHECKLIST.md). Public guidance may change; use current official Google/Bing documentation when web tools are available.
