# LLM Evaluation Study Plan (for the OdF LLM & Agents Lab)

## The one thing to master

**Build a small evaluation harness and learn to trust it.**

A script that runs a model on student answers, compares its marks with a human's marks, and tells you whether a difference between two models is real. Everything else in the lab (schemas, retrieval, tools, agents, finetuning) is judged by this harness.

> Key rule: one model run is one sample, not "the answer". Never trust a difference smaller than the run-to-run variation.

---

## Step 0: Prerequisites (skip what you already know)

You said you know nothing yet and your time is short, so only learn what the harness needs: basic Python, reading JSON, and basic statistics (average, percentage agreement, sample size).

| Need | Resource | Cost | Time |
|---|---|---|---|
| Python basics | Kaggle Learn: *Python* (kaggle.com/learn) | Free | ~5 h |
| Working with data (tables, CSV) | Kaggle Learn: *Pandas* | Free | ~4 h |
| Statistics intuition (variation, sample size, confidence) | StatQuest with Josh Starmer (YouTube): search "StatQuest confidence intervals" and "StatQuest standard error" | Free | ~1-2 h |
| JSON + validation | Pydantic docs, "Getting started / Models" page | Free | ~2 h |

Your ML course covers part of this too, so use its Python and statistics material and don't repeat it here.

---

## Step 1: Understand what an LLM is (about 3 hours)

Watch these in order. Don't take notes, just get the picture.

1. **Andrej Karpathy: "Intro to Large Language Models"** (YouTube, ~1 h). Best first video.
2. **3Blue1Brown: "Neural Networks" series** (YouTube). Watch the chapters on how LLMs and transformers work.
3. **Andrej Karpathy: "Deep Dive into LLMs like ChatGPT"** (YouTube, ~3 h). Optional, watch if you have time.

Why it matters: your Session 1 document states that output is probable text, not correct text, that format is not guaranteed, and that output varies. These videos explain why.

---

## Step 2: Learn to use an LLM as a program component (about 4-5 hours)

- **DeepLearning.AI short courses** (learn.deeplearning.ai, mostly free, 1-2 h each):
  - *ChatGPT Prompt Engineering for Developers*
  - *Building Systems with the ChatGPT API*
  - *Evaluating and Debugging Generative AI*
- **Anthropic and OpenAI docs**: read the "structured outputs / tool use" and "evals" guides.

Hands-on task: write the Session 1 schema (marking points, total mark, error type, feedback) in Pydantic. Call a model. Break it on purpose and see the two failure types:

- **Syntactic**: invalid JSON, missing fields.
- **Semantic**: valid JSON, but total mark does not equal the sum of the points.

---

## Step 3: Learn evaluation (the core, about 10-12 hours)

Read and watch in this order:

1. **Hamel Husain: "Your AI Product Needs Evals"** (hamel.dev, blog). Start here.
2. **Hamel Husain: blog posts on error analysis and LLM-as-a-judge** (hamel.dev). Search for his latest evals posts.
3. **Eugene Yan: posts on LLM evals and LLM-as-judge** (eugeneyan.com).
4. **Evidently AI: "LLM Evaluation for Builders"** (free, code-first course). Covers test datasets, judges, RAG evals.
5. **Book: *AI Engineering* by Chip Huyen (O'Reilly).** Read the chapters on evaluation and dataset engineering. Skim the rest.

Later, if you can afford it: Hamel Husain and Shreya Shankar's cohort course on Maven ("AI Evals for Engineers & PMs"). Check price and dates on Maven before deciding.

---

## Step 4: Build the harness (the real learning, 2-3 weekends)

Do these in order. Each one is a small script.

| # | Task | What you learn |
|---|---|---|
| 1 | Pick 20-30 past-paper questions. Write student-style answers (right, wrong, partial). Mark them yourself with the mark scheme. | Ground truth, how Cambridge marks |
| 2 | Write the Pydantic schema and a validator (syntactic + semantic checks). | Output contracts |
| 3 | Run one model on your answers. Save every output to a file. | Reproducibility |
| 4 | Compute: exact agreement, agreement within 1 mark, per-marking-point agreement, **Cohen's kappa**. | Metrics, chance agreement |
| 5 | Run the same model 5 times. Look at the spread. | Variation, sample size |
| 6 | Write baselines: a numeric checker (value, unit, tolerance) and a keyword matcher. | Where code beats an LLM |
| 7 | Read the cases where model and marker disagree. Sort them into failure types. | Error analysis |
| 8 | Rate 20 feedback texts yourself. Then add an LLM judge and check if it agrees with you. Test with a short vs long version of the same feedback. | Judge bias and calibration |

Important habits:

- Tune prompts on a **development set**. Keep a separate **test set** that you never tune on.
- Keep failed outputs in your results. Removing them makes the model look better than it is.
- With 50 answers, one answer moves the score by 2 percentage points.

---

## Step 5: For fine-tuning data later (after the harness works)

| Topic | Resource |
|---|---|
| Fine-tuning, LoRA basics | Hugging Face LLM Course (huggingface.co/learn), fine-tuning chapters (free) |
| Preference data, reward models, data quality | *The RLHF Book* by Nathan Lambert (rlhfbook.com, free) |
| Annotation guidelines, inter-annotator agreement | Search "Cohen's kappa" and "Krippendorff's alpha" tutorials; Chip Huyen's dataset chapter |
| Data quality checks | Deduplication, test-set contamination, label noise, coverage. Practise on a public set such as UltraFeedback or HH-RLHF by annotating 100 samples yourself |

---

## Time-boxed plan for a busy schedule

Assumes about 5-6 hours per week alongside your ML course.

| Week | Focus | Hours |
|---|---|---|
| 1 | Python and Pandas basics (Kaggle), Karpathy intro video, 3Blue1Brown | ~6 |
| 2 | DeepLearning.AI short courses, Pydantic, build schema + validator (Step 4, tasks 1-3) | ~6 |
| 3 | Hamel's and Eugene's posts, Evidently course, metrics and variation (tasks 4-5) | ~6 |
| 4 | Baselines, error analysis (tasks 6-7), start reading Chip Huyen's evals chapters | ~6 |
| 5 | LLM judge and calibration (task 8) | ~5 |
| 6+ | Move to retrieval, tools, agents, finetuning with the lab | ongoing |

If you only have 2 hours a week, stretch each week into two and drop the optional items (Karpathy deep dive, Maven course, the full *AI Engineering* book).

---

## If you do only five things

1. Watch Karpathy's "Intro to Large Language Models".
2. Read Hamel Husain's "Your AI Product Needs Evals".
3. Mark 20-30 answers yourself.
4. Write a script that computes agreement and Cohen's kappa.
5. Run the same model several times and look at the spread.

*Links and course details change. Check each resource's current availability and price before committing time or money.*
