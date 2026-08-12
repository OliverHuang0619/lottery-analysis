# Methodology

## Core metrics

- `regular_hits`: intersection of six predicted regular numbers and six actual regular numbers.
- `special_number_hit`: exact equality of predicted and actual special number.
- `special_zodiac_hit`: exact equality of predicted and actual special zodiac.
- `special_pick_regular_hit`: predicted special number occurred among the six actual regular numbers; never count it as a special hit.
- `any_overlap`: intersection of all seven predicted and actual numbers.
- `special_abs_error`: absolute numeric distance; descriptive only because lottery numbers are categorical outcomes.
- Keep cumulative and rolling 10/20-issue hit rates for special number and special zodiac.
- `brier`: for probabilistic candidates, mean squared error between assigned probability and outcome indicator. Do not compute it from unnormalized scores.

## Trend features

Compute separately for all seven positions, the six regular positions, and the special position where sample size permits:

- full-history and rolling 10/20/30 issue frequencies;
- issues since last occurrence (gap);
- repeats from the immediately preceding issue;
- odd/even, 1-24 vs 25-49, tail digit, and zodiac counts;
- pair co-occurrence only as a low-weight descriptive feature because sparse pairs overfit easily.

## Review and improvement

Keep the model versioned. Evaluate candidate weight changes with expanding-window walk-forward tests. Optimize a predeclared metric, report the number of folds, and retain the old version unless improvement exceeds simulation noise. Never retrospectively change a saved prediction. Append a new version and explain the change.

For special-first models, use special-zodiac top-1 accuracy as the primary metric and special-number top-1 accuracy as the secondary metric. Also report top-3 zodiac recall when three candidates are emitted. Select the primary number only after selecting the primary zodiac, and require it to belong to that zodiac under the current mapping.

Randomness means short losing or winning streaks are expected. Avoid gambler's fallacy: an overdue number is not made more likely by previous absence, and a hot number is not made more likely by previous occurrence. Frequency and gap features are ranking heuristics only.
