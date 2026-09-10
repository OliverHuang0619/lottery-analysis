---
name: analyze-lottery-history
description: Extract and update 1-49 lottery histories, analyze rolling draw trends, predict the special-number zodiac and strongest number within it, select a three-number regular 3-of-3 candidate, preserve immutable forecasts, review accuracy, run walk-forward tests, and prepare dashboard data. Use for 开奖记录提取、走势图分析、特码生肖预测、生肖首选号码、平码3中3预测、命中复盘、准确率统计、前端仪表板 and iterative evaluation.
---

# Lottery History Analysis

Treat draws as random events. Never claim guaranteed profit, insider knowledge, stable predictive power, or “must hit” numbers. State that every valid outcome remains possible and avoid staking advice.

## Workflow

1. Extract records or append a verified user-supplied draw.
2. Validate issue uniqueness, seven distinct numbers, range 1-49, position order, and zodiac labels.
3. Run `scripts/lottery_history.py analyze records.json --out analysis.json`.
4. Run `scripts/lottery_history.py predict records.json --reviews-dir reviews --out prediction.json` and save the JSON before the draw.
5. Lead with exactly one `top_special_zodiac` and one `special.number` belonging to it, but call them a strong pick only when `forecast_assessment.strong_pick` is true. Otherwise lead with `no_demonstrated_edge` and describe the top item as a mechanical ranking. Then show ranked zodiac candidates, backup numbers in the primary zodiac, the six-number secondary regular set, and exactly three `regular_three` numbers for the 3-of-3 candidate.
6. When a result arrives, run `review`, preserve an immutable review entry, append the verified draw, and create the next prediction from the new cutoff.
7. Run `scripts/lottery_history.py backtest records.json --out backtest.json` for the production method and `scripts/lottery_history.py evaluate records.json --out evaluation.json` for fixed-candidate comparisons. Do not tune weights from one result and never overwrite superseded predictions.

## Accuracy improvement protocol

- Accumulate at least 20 genuine pre-draw saved reviews before an evidence-based promotion; prefer 50 or more. Never treat backfilled predictions as genuine forecasts.
- Always compare the production method with an equal-probability random baseline, fixed trend baseline, short-window, long-window, and lower-recency stable candidate on identical expanding-window targets and deterministic seeds.
- Keep candidate definitions fixed before evaluation. Check performance across multiple chronological segments; do not select a method solely because it wins on the full aggregate or latest draw.
- Treat the user-required no-repeat rule as an ablation: evaluate every candidate both with and without it. Keep the production constraint until the user changes it, but never claim it improves probability without out-of-sample evidence.
- Track zodiac Top-1 as primary, plus zodiac Top-3 coverage, exact-number Top-1, number Top-4 coverage, average regular hits, and exact 3-of-3. Reject candidates that improve one headline metric through material degradation elsewhere.
- Random mixing exists to diversify mechanical selections, not to create accuracy. Save one seed and one draw before the result; never reroll or select a favorable seed afterward.
- Promote a candidate only when it beats both random and the current production benchmark out of sample, remains stable across time segments, and is supported by genuine saved reviews. Version any promoted method and leave prior predictions immutable.

## Trend-first scoring

- Use method `trend-zodiac-first-v3` by default.
- Score special zodiac with a 20% historical baseline, 25% rolling-30 frequency, 30% rolling-10 frequency, and 25% EWMA with an eight-issue half-life.
- Assign zero positive weight to overdue gaps. Keep gaps descriptive only; absence does not make an outcome more likely.
- Rank numbers only within each candidate zodiac using the same trend windows and decay.
- Preserve source zodiac labels across lunar-year mapping changes.
- Report score components and method version. Ranking scores are not calibrated probabilities.

## Forecast calibration and model changes

- Combine expanding-window history with canonical saved reviews through `forecast_assessment`; prefer corrected review entries and never pool duplicate corrections.
- Compare zodiac Top-1 results with the `1/12` random baseline and report 95% Wilson intervals.
- Set `strong_pick` true only after at least 60 walk-forward folds and 20 genuine saved reviews, with both interval lower bounds above the random baseline. Otherwise output `no_demonstrated_edge` even though one mechanical top rank remains for auditability.
- Evaluate candidate methods against v3 on the same expanding-window targets. Reject a candidate that does not improve out-of-sample evidence; never deploy a cosmetic change merely to rotate the selected zodiac.

## User-required no-repeat constraint

- When the immediately preceding saved prediction missed the exact special number, exclude both its predicted special zodiac and predicted special number from the next issue's eligible special selection.
- Apply the constraint only when the latest canonical review's `actual_issue` equals the current records cutoff and `special_number_hit` is false. Do not carry it across missing reviews or more than one issue.
- Record the exclusions and the unconstrained top zodiac in `selection_constraints`. Preserve the superseded unconstrained forecast if one already exists.
- Apply the identical stateful rule in expanding-window backtests. Describe it as a user-required diversification constraint, not evidence that repetition is less likely.

## Seeded random selection

- After applying the no-repeat exclusions, sample one eligible special zodiac instead of always taking rank one.
- Use a fixed mixture of 70% normalized trend score and 30% uniform weight so every eligible zodiac has nonzero selection weight.
- Within the sampled zodiac, use the same 70/30 mixture to sample one eligible special number.
- Use the saved integer seed deterministically and record both candidate distributions and random draws in `random_selection`. Never rerun with a different seed after saving or after seeing the result.
- Keep `ranked_special_zodiacs` as the uncalibrated trend ranking for audit, while `top_special_zodiac` and `special` contain the sampled selections. Randomization adds diversity, not predictive probability.

## Regular 3-of-3 selection

- Build the six-number `regular` set first, then rank only those six by their existing trend score.
- Save the top three as `regular_three`; use score descending and number ascending as the deterministic tie-break.
- Never optimize the three-number rule from one result or describe it as a higher-probability guarantee.
- Review `regular_three_hits`, `regular_three_hit_count`, and `regular_three_exact_hit`. Count an exact hit only when all three occur among the six actual regular numbers; the actual special number never counts.

## Review ledger

Record predicted/actual special number and zodiac, exact hit flags, special pick appearing in regular positions, six-number regular hits, 3-of-3 picks and hits, all-seven overlap, absolute numeric distance, cutoff/target issue, method version, seed, and prediction timestamp.

Never rewrite an old prediction after seeing the result. A number appearing in a regular position is not a special-number hit.

Read `references/methodology.md` before interpreting reviews or modifying the method.

## Dashboard

Show historical statistics, the latest saved prediction, immutable reviewed-prediction accuracy, rolling accuracy, and walk-forward accuracy as separate metrics. Never label ranking scores as probabilities or combine backtest folds with genuine saved reviews into one rate.

## Chinese output order

1. 上期预测偏差复盘，先报特码号码和生肖对错
2. 数据更新与完整性
3. 特码生肖走势
4. 下期评估：先报有无已证明优势；仅在 `strong_pick` 为真时称为重点预测
5. 备选生肖、同肖号码、平码3中3组合和次要六码组合
6. 真实复盘准确率与回测准确率，明确区分口径
7. 不确定性说明
