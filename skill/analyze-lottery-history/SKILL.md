---
name: analyze-lottery-history
description: Extract and update 1-49 lottery histories, analyze rolling draw trends, predict the special-number zodiac and strongest number within it, preserve immutable forecasts, review accuracy, run walk-forward tests, and prepare dashboard data. Use for 开奖记录提取、走势图分析、特码生肖预测、生肖首选号码、命中复盘、准确率统计、前端仪表板 and iterative evaluation.
---

# Lottery History Analysis

Treat draws as random events. Never claim guaranteed profit, insider knowledge, stable predictive power, or “must hit” numbers. State that every valid outcome remains possible and avoid staking advice.

## Workflow

1. Extract records or append a verified user-supplied draw.
2. Validate issue uniqueness, seven distinct numbers, range 1-49, position order, and zodiac labels.
3. Run `scripts/lottery_history.py analyze records.json --out analysis.json`.
4. Run `scripts/lottery_history.py predict records.json --out prediction.json` and save the JSON before the draw.
5. Lead with exactly one `top_special_zodiac` and one `special.number` belonging to it. Then show ranked zodiac candidates, backup numbers in the primary zodiac, and the secondary regular-number set.
6. When a result arrives, run `review`, preserve an immutable review entry, append the verified draw, and create the next prediction from the new cutoff.
7. Run `scripts/lottery_history.py backtest records.json --out backtest.json` for expanding-window evaluation. Do not tune weights from one result and never overwrite superseded predictions.

## Trend-first scoring

- Use method `trend-zodiac-first-v3` by default.
- Score special zodiac with a 20% historical baseline, 25% rolling-30 frequency, 30% rolling-10 frequency, and 25% EWMA with an eight-issue half-life.
- Assign zero positive weight to overdue gaps. Keep gaps descriptive only; absence does not make an outcome more likely.
- Rank numbers only within each candidate zodiac using the same trend windows and decay.
- Preserve source zodiac labels across lunar-year mapping changes.
- Report score components and method version. Ranking scores are not calibrated probabilities.

## Review ledger

Record predicted/actual special number and zodiac, exact hit flags, special pick appearing in regular positions, regular hits, all-seven overlap, absolute numeric distance, cutoff/target issue, method version, seed, and prediction timestamp.

Never rewrite an old prediction after seeing the result. A number appearing in a regular position is not a special-number hit.

Read `references/methodology.md` before interpreting reviews or modifying the method.

## Dashboard

Show historical statistics, the latest saved prediction, immutable reviewed-prediction accuracy, rolling accuracy, and walk-forward accuracy as separate metrics. Never label ranking scores as probabilities or combine backtest folds with genuine saved reviews into one rate.

## Chinese output order

1. 上期预测偏差复盘，先报特码号码和生肖对错
2. 数据更新与完整性
3. 特码生肖走势
4. 下期重点预测：首选生肖和该生肖首选号码
5. 备选生肖、同肖号码和次要平码组合
6. 真实复盘准确率与回测准确率，明确区分口径
7. 不确定性说明
