# Doubts

## Evidence check: strict or loose?

- `schema.py` checks that every quoted `evidence` appears word-for-word in `student_answer`.
- A correct mark worded differently gets flagged `evidence_not_in_answer` even though the mark is right.
  - Example: the student wrote "mass/volume", the model quoted "mass divided by volume".

Options:
1. **Strict (keep as is).** Every flag is a real quote mismatch. Read the flagged cases by hand. Paraphrased correct answers will be flagged too.
2. **Loose.** Pass the quote if most of its words appear in the answer (for example, 80%). Fewer false alarms, but a quote that is partly invented could pass.

Decision needed: which one do we use?
