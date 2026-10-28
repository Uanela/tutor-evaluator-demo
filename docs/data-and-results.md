# Data and results

This document explains the two kinds of files the project reads and writes:

- `data/` holds the student answers and the teacher's marks (input).
- `results/` holds what the model returned for each answer (output).

## 1. The data file

### Format

`run.py` reads the data file one line at a time, and each non-empty line must be a single JSON object (JSON Lines, `.jsonl`). Each object is one student answer.

**Note:** the file currently on disk is `data/dev.json`, which is a single JSON array, not one object per line. `run.py` expects `data/dev.jsonl` by default, so the two do not match yet. See `DOUBTS.md`.

### Fields

| Field | Example | Sent to the model? | Purpose |
|---|---|---|---|
| `id` | `q_density-a3` | no | Unique name for this answer. Used to match results to the answer key. |
| `question_id` | `q_density` | no | Groups answers that share a question. |
| `syllabus_ref` | `1.4` | yes | Syllabus topic the question comes from. |
| `level` | `Core` | yes | Core or Extended tier. |
| `kind` | `calculation` | no | `calculation` or `explanation`. Used for analysis only. |
| `max_mark` | `2` | yes | Highest mark the answer can get. |
| `question` | `A block has a mass of 240 g...` | yes | The question text. |
| `mark_scheme` | `["Uses density = mass / volume", ...]` | only with `--with-scheme` | One entry per marking point, worth one mark each. |
| `student_answer` | `density = mass/volume = 240/30 = 8` | yes | The text being graded. Also used for the evidence check. |
| `teacher_points` | `[true, false]` | **no** | Teacher's yes/no for each marking point, in the same order as `mark_scheme`. |
| `teacher_total` | `1` | **no** | Teacher's total mark. |
| `teacher_note` | `Correct method... no unit` | **no** | Teacher's reason, for humans to read. Not used by the code. |

The fields marked **no** form the answer key. They must never be put in the prompt, or the model could copy them.

### Example

```json
{
  "id": "q_density-a3",
  "question_id": "q_density",
  "syllabus_ref": "1.4",
  "level": "Core",
  "kind": "calculation",
  "max_mark": 2,
  "question": "A block has a mass of 240 g and a volume of 30 cm3. Calculate the density of the block. Give the unit of your answer.",
  "mark_scheme": [
    "Uses density = mass / volume (e.g. 240 / 30)",
    "Answer 8.0 g/cm3 (or 8000 kg/m3) with a correct unit"
  ],
  "student_answer": "density = mass/volume = 240/30 = 8",
  "teacher_points": [true, false],
  "teacher_total": 1,
  "teacher_note": "Correct method and value but no unit, so the answer mark is withheld."
}
```

## 2. The results files

### Where they go

Every `run.py` call writes one file to `results/`. The file name is built from the run settings:

```
<model>_<mode>_<order>_<scheme|noscheme>_<YYYYMMDD-HHMMSS>.jsonl
```

Example: `gemma4-e2b_schema_reason_first_scheme_20261003-082633.jsonl`

The model name has `:` and `/` replaced with `-`, so `gemma4:e2b` becomes `gemma4-e2b`.

### Format

Each line is one graded answer. The line is a JSON object with these parts:

| Field | Meaning |
|---|---|
| `config` | The settings used for the run: `model`, `mode`, `order`, `with_scheme`, `max_attempts`, `temperature`, `seed`, `git_commit`, `data` (the file name used). |
| `id`, `kind` | Which answer this line is about. |
| `valid` | `true` if the reply parsed into the schema. |
| `error` | The parse error message, or `null`. |
| `attempts` | How many tries it took (1 or 2). |
| `issues` | Semantic issue codes found by `semantic_issues()`, for example `point_count_mismatch`. |
| `pred_total`, `pred_points` | What the model said. `null` if the reply was not valid. |
| `teacher_total`, `teacher_points` | The answer key, copied from the data file. |
| `max_mark` | The maximum mark for the question. |
| `latency_s`, `output_tokens` | Time taken and size of the reply. |
| `raw` | The exact text the model returned. Kept so every score can be traced back. |

### Example (shortened)

```json
{
  "config": {
    "model": "gemma4:e2b",
    "mode": "schema",
    "order": "reason_first",
    "with_scheme": true,
    "max_attempts": 2,
    "temperature": 0,
    "git_commit": "55f073c",
    "data": "dev.jsonl",
    "seed": 0
  },
  "id": "q_density-a3",
  "kind": "calculation",
  "valid": true,
  "error": null,
  "attempts": 1,
  "issues": ["point_count_mismatch"],
  "pred_total": 1,
  "pred_points": [true],
  "teacher_total": 1,
  "teacher_points": [true, false],
  "max_mark": 2,
  "latency_s": 70.861,
  "output_tokens": 144,
  "raw": "{ ...the exact model reply, stored as one string... }"
}
```

Here the model returned only one marking point, while the mark scheme has two. That is why the `point_count_mismatch` issue is flagged.

### How the files are used

`evaluate.py` reads every `.jsonl` file in `results/`, groups the lines by (model, mode, order, scheme), and prints the scores. The results files are the only input it needs, so the data file is not read again.

## 3. Where this fits with the README

The README's "Files" section lists `data/dev.jsonl` as "10 placeholder answers". That is a short description only. This document is the full reference for the format of both the data and the results.
