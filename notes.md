(.venv) [uanela@uanela tutor-demo]$ py run.py --model gemma4:e2b --mode schema --with-scheme
[ok ] q_density-a1 pred=2 teacher=2 attempts=1
[ok ] q_density-a2 pred=0 teacher=0 attempts=1
[iss] q_density-a3 pred=1 teacher=1 attempts=1 ['point_count_mismatch']
[ok ] q_massweight-b1 pred=1 teacher=2 attempts=1
[ok ] q_massweight-b2 pred=0 teacher=0 attempts=1
[ok ] q_massweight-b3 pred=1 teacher=1 attempts=1
[ok ] q_gaspressure-c1 pred=3 teacher=3 attempts=1
[ok ] q_gaspressure-c2 pred=0 teacher=0 attempts=1
[ok ] q_power-d1 pred=3 teacher=3 attempts=1
[ok ] q_power-d2 pred=0 teacher=2 attempts=1

saved -> /home/uanela/Documents/development/python/tutor-demo/results/gemma4-e2b_schema_reason_firs
t_scheme_20261003-082633.jsonl
now run: python evaluate.py
(.venv) [uanela@uanela tutor-demo]$ python evaluate.py

=== gemma4:e2b | mode=schema | order=reason_first | scheme | n=10 (1 seed(s)) ===
syntactic valid 100% retried: 0
semantic valid 90% (parsed AND no issue codes)
total exact (all) 80% [50-100] failures count as wrong
total exact (valid) 80% <- flatters the model: failures dropped
total within 1 (all) 90% [70-100]
kappa (valid, totals) 0.73
per-point agreement 86% [68-100] (22 points)
issues point_count_mismatch x1
latency/answer 95.0s output tokens/answer 194
(.venv) [uanela@uanela tutor-demo]$

