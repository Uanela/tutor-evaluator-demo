# OdF Lab — Session 1 starter

A tiny harness for the grading step: one model call -> validated JSON -> scored against a teacher's marks.

## Setup
```bash
pip install -r requirements.txt
ollama pull <a small model>      # see `ollama list` for the exact tag
```

## 1. Sanity-check the harness first (no GPU)
```bash
python run.py --model mock-oracle --mode schema --with-scheme
python run.py --model mock-noisy  --mode schema
python evaluate.py
```
A perfect "oracle" must score 100% and the noisy one must show `total_not_sum_of_points`.
If your harness can't pass this, no model result means anything.

## 2. The three structure methods (same model, same prompt, only `format` changes)
```bash
python run.py --model <tag> --mode prompt
python run.py --model <tag> --mode json
python run.py --model <tag> --mode schema
python evaluate.py
```

## 3. The field-order experiment
```bash
python run.py --model <tag> --mode schema --order reason_first
python run.py --model <tag> --mode schema --order mark_first
```

## 4. Variation and sample size
```bash
python run.py --model <tag> --mode schema --repeats 5
```
Compare the spread between seeds with the confidence intervals. With 10 answers, one answer moves the score 10 points.

## 5. Mark scheme given (Session 2 preview)
Add `--with-scheme`. Now per-point agreement is computed, because the marking points are fixed.

## Files
- `schema.py`  output schema (two field orders) + semantic checks
- `run.py`     calls the model, parses, retries once with the error message, logs every run to `results/`
- `evaluate.py` agreement, kappa, bootstrap CI, validity, issue counts
- `data/dev.jsonl` 10 placeholder answers. Replace with your own questions, answers and teacher marks.

## Next steps
1. Replace the dev data with 10-15 questions you mark yourself; have someone mark a subset too.
2. Port your Rate7Ai prompt as another prompt variant and compare.
3. Add `follow_up` to the schema, then a judge for `feedback` calibrated on your own ratings.
4. Add a TF-IDF / cosine-similarity baseline for explanation questions.
