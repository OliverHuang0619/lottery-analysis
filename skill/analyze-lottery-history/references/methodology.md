# Methodology

## Core metrics

- `regular_hits`: intersection of six predicted regular numbers and six actual regular numbers.
- `special_number_hit`: exact equality of predicted and actual special number.
- `special_zodiac_hit`: exact equality of predicted and actual special zodiac.
- `special_pick_regular_hit`: predicted special number occurred among the six actual regular numbers; never count it as a special hit.
- `any_overlap`: intersection of all seven predicted and actual numbers.
- `special_abs_error`: descriptive numeric distance only; lottery numbers are categorical outcomes.
- Keep cumulative and rolling 10/20-review rates for special number and zodiac.

## Trend model v3

Use fixed components for zodiac and within-zodiac number ranking:

- 20% full-history frequency;
- 25% rolling-30 frequency;
- 30% rolling-10 frequency;
- 25% exponentially weighted frequency with an eight-issue half-life;
- 0% positive overdue weighting.

Treat gap as descriptive metadata only. Never infer that a long absence increases the next-draw probability. Treat scores as rankings rather than calibrated probabilities.

## Analysis features

Compute separately for all seven positions, regular positions, and the special position:

- full-history and rolling 10/20/30 frequencies;
- exponentially decayed frequency;
- issues since last occurrence for description only;
- immediate repeats, odd/even, 1-24 vs 25-49, tail digit, and zodiac counts;
- sparse pair co-occurrence only as a low-weight descriptive feature.

## Review and improvement

Keep the model versioned and preserve every saved prediction. Evaluate candidate changes with expanding-window walk-forward tests. Use special-zodiac Top-1 accuracy as the primary metric, exact special-number accuracy as secondary, and Top-3 zodiac recall when available.

Report genuine saved-review accuracy separately from walk-forward accuracy. The former measures forecasts actually saved before a draw; the latter is development evidence and must include fold count and target range. Never pool them.

Randomness makes short streaks expected. A hot or overdue outcome is not made more likely by past draws; trend features are ranking heuristics only.
