---
name: analyze-lottery-history
description: Extract and update 1-49 lottery histories, analyze 澳门/香港-style draws, prioritize special-number zodiac and the strongest number within that zodiac, save predictions, and review exact special-number and special-zodiac correctness when new results arrive. Use for 开奖记录提取、走势分析、特码生肖预测、生肖首选号码、命中复盘、偏差记录 and iterative walk-forward evaluation.
---

# Lottery History Analysis

Treat draws as random events. Never claim guaranteed profit, insider knowledge, stable predictive power, or “must hit” numbers. State that every valid outcome remains possible and avoid staking advice.

## Workflow

1. Extract records with `scripts/lottery_history.py extract INPUT --out records.json` or append a verified user-supplied draw.
2. Validate issue count, duplicate issues, seven distinct numbers, range 1-49, positions, and source zodiac labels.
3. Analyze with `scripts/lottery_history.py analyze records.json --out analysis.json`.
4. Predict with `scripts/lottery_history.py predict records.json --out prediction.json` and save the JSON before the draw.
5. Lead the prediction with exactly one `top_special_zodiac` and exactly one `primary_number` belonging to it. Then show ranked zodiac candidates, backup numbers inside the primary zodiac, and the secondary regular-number set.
6. When a result arrives, run `review`, append an immutable review-log entry, append the verified draw, and create the next prediction from the updated cutoff.
7. Do not tune weights from one result. Evaluate changes with expanding-window walk-forward tests and retain the old version unless out-of-sample special-zodiac performance improves beyond simulation noise.

## Special-first scoring

- Score special zodiac separately using historical special-zodiac frequency, rolling 10/20/30 frequency, issues since last special appearance, and bounded mean reversion.
- Rank numbers only within each candidate zodiac using special-position frequency first, then recent special frequency and bounded gap.
- Preserve source zodiac labels across lunar-year mapping changes. Build the future mapping from the latest complete mapping and mark inferred labels.
- Report score components and method version. Scores are rankings, not calibrated probabilities unless a calibrated model was fitted.

## Review ledger

Record independently: predicted/actual special number and `special_number_hit`; predicted/actual special zodiac and `special_zodiac_hit`; predicted special number appearing in an actual regular position (`special_pick_regular_hit`); regular hits; all-seven overlap; special absolute numeric distance; cutoff/target issue; method version; seed; and prediction timestamp.

Never rewrite an old prediction after seeing the result. A number appearing in a regular position is not a special-number hit.

Read `references/methodology.md` before interpreting reviews or modifying the method.

## Chinese output order

1. 上期预测偏差复盘（先报特码号码对/错与生肖对/错）
2. 数据更新与完整性
3. 特码生肖走势
4. 下期重点预测：首选生肖 + 该生肖首选号码
5. 备选生肖/号码与次要平码组合
6. 不确定性说明
