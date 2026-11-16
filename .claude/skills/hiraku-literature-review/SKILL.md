---
name: hiraku-literature-review
description: Conduct scholarly literature reviews for research projects managed in Hiraku. Use when users request paper discovery, literature surveys, related-work summaries, evidence synthesis, or research-gap analysis. Search and analyze publications with alphaXiv MCP tools when available, then save cited findings in a Hiraku context record.
---

# Hiraku literature review

Use this skill when asked to review research literature in a Hiraku project.
Keep the review scoped to the user's question, and create or update a Hiraku
`context` record containing the result.

## alphaXiv availability

Use the alphaXiv MCP tools when they are available:

- `discover_papers` to find and rank candidate papers.
- `get_paper_content` for a paper overview or extracted text.
- `answer_pdf_queries` for focused, citation-ready answers from the paper PDF.

If alphaXiv MCP tools are unavailable, tell the user how to set them up:
[alphaXiv MCP setup](https://www.alphaxiv.org/docs/mcp). Do not imply that
searches or paper checks were performed. Continue with the review only if the
user provides papers or asks for a clearly labeled preliminary synthesis from
other available sources.

## Literature review

1. Establish the research question and useful boundaries from the request or
   existing project records: topic, population or domain, methods, date range,
   and desired depth. Inspect the current Hiraku project and related records
   before choosing a destination.
2. Call `discover_papers` with the user's topic and terms. Use the returned
   candidates to identify relevant papers and gaps in coverage. For a broad
   review, make additional discovery calls with meaningfully varied keywords,
   questions, or difficulty when the tool's current limits allow. Do not
   repeatedly send near-identical searches.
3. Select papers based on their relevance to the question and the evidence
   available. Include foundational and recent work where the scope calls for
   both. Clearly identify the search coverage and do not describe a targeted
   search as exhaustive.
4. Use `get_paper_content` when an overview or broader extracted context is
   useful. For claims central to the review, use `answer_pdf_queries` and batch
   all relevant questions for each paper into one call. Ask about the methods,
   data, results, limitations, and the specific claims needed for synthesis.
   Query papers separately so returned evidence and citation tags stay tied to
   the correct paper.
5. Synthesize across papers around themes, agreements, disagreements, methods,
   limitations, and open questions. Distinguish source-supported findings from
   interpretation. Do not invent bibliographic details, quotations, or results;
   note when a PDF or relevant evidence could not be retrieved.
6. Cite claims next to the supporting paper using its title, authors when
   available, year, and a stable alphaXiv/arXiv link. Preserve citation tags
   supplied by `answer_pdf_queries` when using its extracted evidence. Keep any
   direct quotation brief and faithful to the returned text.
7. Save the review in a Hiraku record, then inspect the saved record to confirm
   its title, relationships, and Markdown body.

### Review record

Use an existing literature/context record when it matches the request. If none
exists, create a `context` record under a clear project-relative ID, preferably
as a child of the relevant research root when there is one. Check for ID
collisions first. Preserve relevant existing notes when updating a record.
Use Hiraku MCP record tools when available; otherwise use the CLI. For example,
write the review to a Markdown file and create a record with:

```bash
hiraku record create literature/<topic> \
  --title "Literature review: <topic>" --type context \
  --markdown-file review.md
hiraku record show literature/<topic> --json
```

Choose a concise ID and title suited to the project. If the record already
exists, update its Markdown while retaining useful existing content; do not
silently replace unrelated material. In the saved review include:

- Research question and scope, including any date or domain boundaries.
- A brief note on the alphaXiv search approach and coverage limitations.
- The selected papers with bibliographic details and links.
- A synthesis organized by themes, with citations near supported claims.
- Disagreements, evidence limitations, and open research questions.

