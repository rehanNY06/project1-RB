# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

The domain that I chose is "reviews of CS department at Rice University". This knowledge is valuable for those applying to Rice University's CS department and want to know what they are getting themselves into. The reason why this is useful is because official channels don't really have authenticity to them to a properly give you an assessment.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 |Rate My Professors |Web scrape (txt) |https://www.ratemyprofessors.com/search/professors/799?q=*&did=11 |
| 2 |Reddit  |Web scrape (txt) |https://www.reddit.com/r/riceuniversity/comments/ttd93h/how_is_overall_computer_science_experience_at_rice/ |
| 3 |AcademicJobs |Web scrape (txt) |https://www.academicjobs.com/rate-my-professor/rice-university/5067 |
| 4 |Quora Professor Rec|Web scrape (txt) |https://www.quora.com/Which-professors-would-you-recommend-people-take-classes-from-at-Rice-University |
| 5 |Rice University CS |Web scrape (txt) |https://ga.rice.edu/programs-study/departments-programs/engineering/computer-science/ |
| 6 |Facebook Rice University |Web scrape (txt) |https://www.facebook.com/RiceCS/ |
| 7 |Quora Worth It? |Web scrape (txt) |https://www.quora.com/Is-it-worth-it-to-go-to-Rice-for-computer-science-grad-school-What-are-the-job-prospects-after-attending-Rice-as-well-as-the-return-on-investment |
| 8 |LinkedIn |Web scrape (txt) |https://www.linkedin.com/company/ricecs/ |
| 9 |GradCafe |Web scrape (txt) |https://forum.thegradcafe.com/topic/16994-has-anybody-heard-from-rice-univ-cs-phd-program/ |
| 10 |Quora Value |Web scrape (txt) |https://www.quora.com/How-good-is-Rice-Universitys-Computer-Science-department |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**
300 tokens
**Overlap:**
30 tokens
**Why these choices fit your documents:**
Majority of my documents were forum posts that had at most 1-3 paragraphs from each review. A 300 token chunk was more than sufficient enough to be able to capture a complete thought without opinions from the other people merging in. The overlap of only 30 tokens is there mainly for the purpose of capturing any review that carries over the initial chunk boundary; ensuring that no key detail is lost. Before chunking, each document had to be cleaned to remove HTML entities & JSON garbage like "Thumbs up" or "&amp". Minimizing as much noise as possible along the way.
**Final chunk count:**
87 chunks
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
all-MiniLM-L6-v2 via sentence-transformers --> Easily accessible locally to run. As well as, fast enough to run 87 chunks in under a minute while still performing well on short conversational text.
**Production tradeoff reflection:**
After researching more options, the current model that I've used has a limit of 256 tokens which means that chunks greater than this token count gets loaded silently. So, a greater model that would allow a larger token portion would potentially score  higher on retrieval benchmarks. As for Multilingual support is a main problem as all sources are written in English and most of these questions would be asked by an indivdual who should know a English well enough. 
---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The LLM contained instructions that were enforced at every question. The key instructions were "Answer ONLY using the information provided in the context documents below. Do NOT use any outside knowledge, even if you think it is correct. If the context does not contain enough information to answer the question, respond with exactly: 'I don't have enough information on that based on the available student reviews and sources." Temperature was also set to 0.2 to ensure the model didn't give generalized responses. The retrieved chunks were passed in a labeled context block above the question, formatted as [Source:  RateMyProfessors], [Source: Reddit], etc., so the model could reference them by name rather than by number.
**How source attribution is surfaced in the response:**
After generation, the retrieve() function returns metadata for every chunk it pulled. These are formatted into a separate "Retrieved from" box in the Gradio UI automatically,  so even if the LLM fails to cite a source in its answer, the user still  sees exactly which documents were used and how closely they matched the query.
---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Is Devika Subramanian a decent professor for my first semester? | She is a solid professor as majority of students rated her at least a 3. | Described her as "one of the friendliest teachers at Rice", patient outside class, good at explaining difficult concepts, with one older negative review about organization. | Relevant | Partially accurate |
| 2 | Is there grade inflation within Rice at all, or is it extremely difficult? | Not really, but with collaboration of you and other students you can get by. | Retrieved a quote that "Rice sets a high bar, but everyone helps each other get over that bar", suggesting collaboration matters but no inflation. | Partially relevant | Partially accurate |
| 3 | Who is the department chair of the CS department and their contact information? | The department chair is Christopher M. Jermaine and their method of contact is through email: christopher.m.jermaine@rice.edu. | Correctly identified Christopher M. Jermaine as department chair with email christopher.m.jermaine@rice.edu. | Relevant | Accurate |
| 4 | What's the most recent workshop they've held for students? | Rice University is hosting the Crossroads of AI & Society Workshop at the Rice Global Paris Center, July 15-16, 2026 in Paris, France. | System responded "I don't have enough information on that based on the available student reviews and sources." | Off-target | Inaccurate |
| 5 | Is Rice University's CS department worth it for grad school in terms of job prospects? | Students and alumni reflect positively on job prospects, noting strong research opportunities. | Cited alumni achieving desired careers with "ROI near infinity" and students working at Google, Microsoft, Amazon, and Facebook. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
What's the most recent workshop they've held for students?
**What the system returned:**
"I don't have enough information on that based on the available student reviews and sources."
**Root cause (tied to a specific pipeline stage):**
The part of the pipeline stage that is the root cause of this error is the ingestion stage. The source that was supposed to be used in order to answer the question was the Facebook of Rice University. So, either the information of the dates from that .txt was not properly captured or the text never made it into chunks.json.
**What you would change to fix it:**
Go back to the Facebook source and ensure that the dates were properly associated with each post within the .txt files so that when it goes through the process of chunk loading the LLM can properly display and cite the information. 
---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The spec helped me during my implentation as it allowed Claude to properly generate code. As well as, allow me to ask it questions on specific parts that confused me of what I've written there.
**One way your implementation diverged from the spec, and why:**
Initially I was planning to use TOP_K = 3 but diverged from there to TOP_K = 4. This is because the best answers were showing up to Rank 4 and with the LLM retrieving an additional chunk gave it more than enough to answer questions.
---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
I gave claude my planning.md, along with my pipeline diagram, and asked it to implement a script that loads documents, cleans them, and produces chunks matching my specified chunk size and overlap.
- *What it produced:*
It generated ingest_and_chunk_local.py using 300 tokens and 30 token overlap, a cleaning function that stripped HTML tags and entities, and a JSON output of all chunks with metadata.
- *What I changed or overrode:*
The original script expected files named s01_ratemyprofessors.txt, s02_reddit_cs.txt, etc. My actual files were named differently (ratemyprofessor.txt, reddit.txt, etc.), so I had Claude update the filenames to match. I also had Claude add additional boilerplate patterns to the cleaning function after inspecting the first cleaned document and seeing leftover RateMyProfessors UI noise like "Thumbs up", "Helpful", and "Arrow Icon" still present in the chunks.

**Instance 2**

- *What I gave the AI:*
I gave Claude my Retrieval Approach section from  planning.md, my pipeline diagram, and the chunks.json output from  Milestone 3, and asked it to implement embedding with all-MiniLM-L6-v2, storage in ChromaDB with source metadata, and a retrieval function returning top-k chunks with distance scores.
- *What it produced:*
It generated embed_and_retrieve.py which loaded chunks, embedded them using sentence-transformers, stored them in a persistent ChromaDB collection with metadata including source name, filename, and chunk index, and ran 3 evaluation queries printing results with distance scores and a quality assessment.
- *What I changed or overrode:*
I changed top-k from 3 to 4 after seeing that the correct answer for the department chair question was appearing at rank 4 and would have been missed. I also had Claude fix the LLM citation behavior in app.py after noticing it was saying "According to Document 1" instead of using the actual source name.
