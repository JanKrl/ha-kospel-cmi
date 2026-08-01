---
name: ponytail-gain
description: >
  Show ponytail's measured impact as a compact scoreboard: less code, less
  cost, more speed, from the benchmark medians. One-shot display, not a
  persistent mode, and not a per-repo number. Trigger: /ponytail-gain,
  "ponytail gain", "what does ponytail save", "show ponytail impact",
  "ponytail scoreboard".
---

# Ponytail Gain

Display this scoreboard when invoked. One-shot: do NOT change mode, write flag
files, or persist anything.

## Scoreboard

```
  ponytail gain                     benchmark median · 5 tasks · 3 models

  Lines of code   no-skill  ████████████████████  100%
                  ponytail  ███                   -54% (up to -94%)

  Tokens          no-skill  ████████████████████  100%
                  ponytail  ███████████████       -22%

  Cost            no-skill  ████████████████████  100%
                  ponytail  ███████████████       -20%

  Speed           no-skill  ████████████████████  100%
                  ponytail  ██████████████        -27%
```
