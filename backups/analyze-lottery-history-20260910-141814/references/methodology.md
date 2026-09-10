# Methodology

## Core metrics

- `regular_hits`: intersection of six predicted regular numbers and six actual regular numbers.
- `regular_three_hits`: intersection of the three predicted `regular_three` numbers and six actual regular numbers.
- `regular_three_exact_hit`: true only when `regular_three_hit_count == 3`; never include the actual special number.
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

## Regular 3-of-3 rule

Select the six regular candidates with the existing v3 process. Rank those six by trend score descending, breaking exact ties by number ascending, and save the first three as `regular_three`. Keep this rule fixed across saved predictions and walk-forward folds. Report exact 3-of-3 accuracy separately from average hits; do not tune the rule after a single draw.

## Analysis features

Compute separately for all seven positions, regular positions, and the special position:

- full-history and rolling 10/20/30 frequencies;
- exponentially decayed frequency;
- issues since last occurrence for description only;
- immediate repeats, odd/even, 1-24 vs 25-49, tail digit, and zodiac counts;
- sparse pair co-occurrence only as a low-weight descriptive feature.

## Review and improvement

Keep the model versioned and preserve every saved prediction. Evaluate candidate changes with expanding-window walk-forward tests. Use special-zodiac Top-1 accuracy as the primary metric, exact special-number accuracy as secondary, and Top-3 zodiac recall when available.

Report genuine saved-review accuracy separately from walk-forward accuracy, including `regular_three_exact_accuracy` for both when available. The former measures forecasts actually saved before a draw; the latter is development evidence and must include fold count and target range. Never pool them.

Randomness makes short streaks expected. A hot or overdue outcome is not made more likely by past draws; trend features are ranking heuristics only.

## Fixed candidate evaluation

Use `evaluate` to compare predefined models on identical expanding-window folds:

- `random-uniform`: equal-probability control;
- `trend-v3`: production weighting and 10/30 windows;
- `trend-short`: 5/20 windows;
- `trend-long`: 20/50 windows;
- `stable-candidate`: 30% history, 25% long window, 15% short window, and 30% EWMA.

Run each with no-repeat disabled and enabled. This is an ablation test, not permission to remove the user's production constraint. Report zodiac Top-1, zodiac Top-3 coverage, number Top-1, number Top-4 coverage, mean regular hits, and exact 3-of-3. Inspect chronological segments when choosing a candidate; aggregate wins alone are insufficient.

Do not promote a candidate from backtest alone. Require at least 20 genuine saved reviews (prefer 50), fixed definitions chosen before observation, improvement over both equal-random and production benchmarks, and no material collapse in secondary metrics. Preserve the previous model version and all immutable forecasts.

## Calibration gate

Treat ranking and demonstrated predictive ability as separate outputs. Compute 95% Wilson intervals for special-zodiac Top-1 accuracy in expanding-window folds and canonical genuine saved reviews. The random-zodiac reference is `1/12`. Require at least 60 folds and 20 saved reviews, and require both lower confidence bounds to exceed `1/12`, before setting `strong_pick` to true. Until then, retain one top rank for immutable comparison but label the forecast `no_demonstrated_edge`.

When evaluating a replacement ranking method, use identical target folds and preserve the v3 result as the benchmark. Do not promote a candidate with equal or worse out-of-sample results, even if it produces a different next zodiac.

## No-repeat-after-miss constraint

If the latest canonical saved review shows that the previous exact special-number pick missed, remove that prediction's zodiac and number from the immediately following issue's eligible special candidates before seeded sampling. Save the excluded values plus the unconstrained top zodiac for audit. Simulate the same one-step state transition in walk-forward evaluation. This is a user-selected diversification policy and must never be justified as a change in the random draw probability.

## Seeded trend-weighted randomization

After exclusions, convert eligible zodiac ranking scores into sampling weights using `0.70 * normalized_trend_score + 0.30 * uniform_share`. Sample once with the immutable prediction seed. Apply the identical mixture within the sampled zodiac to select the special number. Save distributions and random draws, and simulate the exact seeded procedure in every walk-forward fold. This prevents deterministic rank-one repetition but does not make the selected outcome statistically more likely.
