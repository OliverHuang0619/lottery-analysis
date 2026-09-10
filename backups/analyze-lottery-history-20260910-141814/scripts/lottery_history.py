#!/usr/bin/env python3
import argparse
import json
import random
from collections import Counter
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path

ANIMALS = list("鼠牛虎兔龙蛇马羊猴鸡狗猪")
POSITIONS = ["平一", "平二", "平三", "平四", "平五", "平六", "特码"]
MODEL_CONFIGS = {
    "random-uniform": {"weights": (0.0, 0.0, 0.0, 0.0), "recent_short": 10, "recent_long": 30, "uniform_mix": 1.0},
    "trend-v3": {"weights": (0.20, 0.25, 0.30, 0.25), "recent_short": 10, "recent_long": 30, "uniform_mix": 0.30},
    "trend-short": {"weights": (0.20, 0.25, 0.30, 0.25), "recent_short": 5, "recent_long": 20, "uniform_mix": 0.30},
    "trend-long": {"weights": (0.20, 0.25, 0.30, 0.25), "recent_short": 20, "recent_long": 50, "uniform_mix": 0.30},
    "stable-candidate": {"weights": (0.30, 0.25, 0.15, 0.30), "recent_short": 10, "recent_long": 30, "uniform_mix": 0.30},
}


def dump(obj, path):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text)


def load_records(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["records"] if isinstance(data, dict) else data


def validate(records):
    seen = set()
    for record in records:
        issue = record["issue"]
        if issue in seen:
            raise ValueError("重复期号: " + issue)
        seen.add(issue)
        rows = record.get("numbers", [])
        numbers = [row["number"] for row in rows]
        if len(numbers) != 7 or len(set(numbers)) != 7 or any(n < 1 or n > 49 for n in numbers):
            raise ValueError("无效开奖记录: " + issue)
        if [row.get("position") for row in rows] != POSITIONS:
            raise ValueError("位置顺序错误: " + issue)
        if any(row.get("zodiac") not in ANIMALS for row in rows):
            raise ValueError("生肖标签错误: " + issue)


def newest(records):
    validate(records)
    return sorted(records, key=lambda record: int(record["issue"]), reverse=True)


def analysis(records):
    desc = newest(records)
    all_numbers = [[row["number"] for row in record["numbers"]] for record in desc]
    special = [record["numbers"][6] for record in desc]
    frequency = lambda rows: dict(sorted(Counter(n for row in rows for n in row).items()))
    gaps = {str(n): next((i for i, row in enumerate(all_numbers) if n in row), len(desc)) for n in range(1, 50)}
    zodiac_special = Counter(row["zodiac"] for row in special)
    return {
        "issues": len(desc),
        "latest_issue": desc[0]["issue"],
        "latest_date": desc[0].get("date"),
        "frequency_all": frequency(all_numbers),
        "frequency_recent10": frequency(all_numbers[:10]),
        "frequency_recent30": frequency(all_numbers[:30]),
        "special_frequency": dict(sorted(Counter(row["number"] for row in special).items())),
        "special_zodiac_frequency": dict(zodiac_special),
        "gaps": gaps,
        "odd_even": {
            "odd": sum(n % 2 for row in all_numbers for n in row),
            "even": sum(n % 2 == 0 for row in all_numbers for n in row),
        },
        "zodiac": dict(Counter(row["zodiac"] for record in desc for row in record["numbers"])),
        "latest_numbers": all_numbers[0],
    }


def zodiac_map(records):
    mapping = {}
    for record in newest(records):
        for row in record["numbers"]:
            if row["number"] not in mapping and row.get("zodiac"):
                mapping[row["number"]] = row["zodiac"]
        if len(mapping) == 49:
            break
    return mapping


def trend_components(items, key, candidates, half_life=8, config=None):
    """Use observed rolling trends; never reward an outcome for being overdue."""
    config = config or MODEL_CONFIGS["trend-v3"]
    history_weight, long_weight, short_weight, ewma_weight = config["weights"]
    long_window = config["recent_long"]
    short_window = config["recent_short"]
    count = max(len(items), 1)
    full = Counter(key(item) for item in items)
    recent_long = Counter(key(item) for item in items[-long_window:])
    recent_short = Counter(key(item) for item in items[-short_window:])
    weights = [0.5 ** ((len(items) - 1 - i) / half_life) for i in range(len(items))]
    weight_total = max(sum(weights), 1e-12)
    decayed = Counter()
    for item, weight in zip(items, weights):
        decayed[key(item)] += weight
    result = {}
    for value in candidates:
        components = {
            "history": history_weight * full[value] / count,
            "recent_long": long_weight * recent_long[value] / max(min(long_window, len(items)), 1),
            "recent_short": short_weight * recent_short[value] / max(min(short_window, len(items)), 1),
            "ewma": ewma_weight * decayed[value] / weight_total,
            "overdue": 0.0,
        }
        result[value] = {"score": sum(components.values()), "components": components}
    return result


def weighted_random_choice(rng, candidates, scores, uniform_mix=0.30):
    score_total = sum(max(scores[value], 0.0) for value in candidates)
    count = max(len(candidates), 1)
    probabilities = {}
    for value in candidates:
        trend_share = max(scores[value], 0.0) / score_total if score_total else 1 / count
        probabilities[value] = (1 - uniform_mix) * trend_share + uniform_mix / count
    draw = rng.random()
    cumulative = 0.0
    selected = candidates[-1]
    for value in candidates:
        cumulative += probabilities[value]
        if draw <= cumulative:
            selected = value
            break
    return selected, probabilities, draw


def predict(records, seed=20260811, excluded_special_zodiac=None, excluded_special_number=None, model="trend-v3"):
    config = MODEL_CONFIGS[model]
    desc = newest(records)
    chronological = list(reversed(desc))
    mapping = zodiac_map(desc)
    all_rows = [row for record in chronological for row in record["numbers"]]
    special_rows = [record["numbers"][6] for record in chronological]
    number_rank = trend_components(all_rows, lambda row: row["number"], range(1, 50), config=config)
    regular_rng = random.Random(seed ^ 0x5A17)
    special_rng = random.Random(seed)
    number_scores = {n: number_rank[n]["score"] + regular_rng.random() * 1e-12 for n in range(1, 50)}
    regular = []
    for number in sorted(number_scores, key=number_scores.get, reverse=True):
        trial = regular + [number]
        if sum(x % 2 for x in trial) <= 5 and sum(x <= 24 for x in trial) <= 5 and sum(x % 10 == number % 10 for x in regular) < 2:
            regular.append(number)
        if len(regular) == 6:
            break
    zodiac_rank = trend_components(special_rows, lambda row: row["zodiac"], ANIMALS, config=config)
    raw_ranked_zodiacs = sorted(ANIMALS, key=lambda z: (zodiac_rank[z]["score"], z), reverse=True)
    ranked_zodiacs = [z for z in raw_ranked_zodiacs if z != excluded_special_zodiac]
    top_zodiac, zodiac_probabilities, zodiac_draw = weighted_random_choice(
        special_rng,
        ranked_zodiacs,
        {z: zodiac_rank[z]["score"] for z in ranked_zodiacs}, config["uniform_mix"],
    )
    candidates = [n for n in range(1, 50) if mapping.get(n) == top_zodiac]
    special_rank = trend_components(special_rows, lambda row: row["number"], candidates, config=config)
    ranked_numbers = [
        n for n in sorted(candidates, key=lambda n: (special_rank[n]["score"], n), reverse=True)
        if n != excluded_special_number
    ]
    special_number, number_probabilities, number_draw = weighted_random_choice(
        special_rng,
        ranked_numbers,
        {n: special_rank[n]["score"] for n in ranked_numbers}, config["uniform_mix"],
    )
    regular = [n for n in regular if n != special_number]
    for number in sorted(number_scores, key=number_scores.get, reverse=True):
        if number != special_number and number not in regular:
            regular.append(number)
        if len(regular) == 6:
            break

    def packed(row):
        return {
            "score": round(row["score"], 6),
            "components": {key: round(value, 6) for key, value in row["components"].items()},
        }

    regular_three = sorted(regular, key=lambda n: (-number_rank[n]["score"], n))[:3]

    return {
        "schema": "lottery-prediction/v6",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cutoff_issue": desc[0]["issue"],
        "target_issue": f"{int(desc[0]['issue']) + 1:03d}",
        "method_version": "trend-weighted-random-calibrated-no-repeat-v6",
        "ranking_method_version": model,
        "seed": seed,
        "regular": [{"number": n, "zodiac": mapping.get(n, "未知"), **packed(number_rank[n])} for n in sorted(regular)],
        "regular_three": [{"number": n, "zodiac": mapping.get(n, "未知"), **packed(number_rank[n])} for n in regular_three],
        "top_special_zodiac": {"zodiac": top_zodiac, **packed(zodiac_rank[top_zodiac])},
        "ranked_special_zodiacs": [{"zodiac": z, **packed(zodiac_rank[z])} for z in ranked_zodiacs[:3]],
        "special_zodiac_top3": ranked_zodiacs[:3],
        "special_number_top4": [
            n for n in sorted(range(1, 50), key=lambda n: (trend_components(special_rows, lambda row: row["number"], range(1, 50), config=config)[n]["score"], n), reverse=True)[:4]
        ],
        "special": {"number": special_number, "zodiac": top_zodiac, **packed(special_rank[special_number])},
        "numbers_in_top_zodiac": [
            {"number": n, "zodiac": top_zodiac, **packed(special_rank[n])}
            for n in [special_number] + [value for value in ranked_numbers if value != special_number][:3]
        ],
        "random_selection": {
            "uniform_mix": config["uniform_mix"],
            "zodiac_draw": round(zodiac_draw, 12),
            "zodiac_probabilities": {z: round(zodiac_probabilities[z], 6) for z in ranked_zodiacs},
            "number_draw": round(number_draw, 12),
            "number_probabilities": {str(n): round(number_probabilities[n], 6) for n in ranked_numbers},
        },
        "selection_constraints": {
            "no_repeat_after_previous_special_miss": bool(excluded_special_zodiac or excluded_special_number),
            "excluded_special_zodiac": excluded_special_zodiac,
            "excluded_special_number": excluded_special_number,
            "unconstrained_top_special_zodiac": raw_ranked_zodiacs[0],
        },
        "model_config": config,
        "disclaimer": "仅供统计娱乐；走势排名不是开奖概率，随机开奖无法被可靠预测。",
    }


def review(prediction, actual):
    predicted_regular = {row["number"] for row in prediction["regular"]}
    actual_regular = {row["number"] for row in actual["numbers"][:6]}
    predicted_regular_three = [row["number"] for row in prediction.get("regular_three", [])]
    regular_three_hits = sorted(set(predicted_regular_three) & actual_regular)
    predicted_special = prediction["special"]
    actual_special = actual["numbers"][6]
    return {
        "cutoff_issue": prediction.get("cutoff_issue"),
        "target_issue": prediction.get("target_issue", actual["issue"]),
        "actual_issue": actual["issue"],
        "method_version": prediction.get("method_version"),
        "seed": prediction.get("seed"),
        "prediction_created_at": prediction.get("created_at"),
        "predicted_special_number": predicted_special["number"],
        "actual_special_number": actual_special["number"],
        "special_number_hit": predicted_special["number"] == actual_special["number"],
        "predicted_special_zodiac": predicted_special.get("zodiac"),
        "actual_special_zodiac": actual_special.get("zodiac"),
        "special_zodiac_hit": predicted_special.get("zodiac") == actual_special.get("zodiac"),
        "special_zodiac_top3_hit": actual_special.get("zodiac") in prediction.get("special_zodiac_top3", []),
        "special_number_top4_hit": actual_special["number"] in prediction.get("special_number_top4", []),
        "special_pick_regular_hit": predicted_special["number"] in actual_regular,
        "regular_hits": sorted(predicted_regular & actual_regular),
        "regular_hit_count": len(predicted_regular & actual_regular),
        "predicted_regular_three": predicted_regular_three,
        "regular_three_hits": regular_three_hits,
        "regular_three_hit_count": len(regular_three_hits),
        "regular_three_exact_hit": len(predicted_regular_three) == 3 and len(regular_three_hits) == 3,
        "any_overlap": sorted((predicted_regular | {predicted_special["number"]}) & (actual_regular | {actual_special["number"]})),
        "special_abs_error": abs(predicted_special["number"] - actual_special["number"]),
    }


def backtest(records, min_train=30, model="trend-v3", no_repeat=True):
    chronological = sorted(records, key=lambda record: int(record["issue"]))
    rows = []
    previous_prediction = None
    previous_actual = None
    for i in range(min_train, len(chronological)):
        missed = no_repeat and previous_prediction is not None and previous_prediction["special"]["number"] != previous_actual["numbers"][6]["number"]
        prediction = predict(
            chronological[:i],
            seed=20260811 + i,
            excluded_special_zodiac=previous_prediction["special"].get("zodiac") if missed else None,
            excluded_special_number=previous_prediction["special"]["number"] if missed else None,
            model=model,
        )
        rows.append(review(prediction, chronological[i]))
        previous_prediction = prediction
        previous_actual = chronological[i]
    folds = len(rows)
    segment_size = max(folds // 3, 1)
    segments = []
    for index in range(3):
        start = index * segment_size
        end = folds if index == 2 else min((index + 1) * segment_size, folds)
        segment = rows[start:end]
        if not segment:
            continue
        segments.append({
            "name": ("early", "middle", "recent")[index],
            "first_target_issue": segment[0]["target_issue"],
            "last_target_issue": segment[-1]["target_issue"],
            "folds": len(segment),
            "special_zodiac_accuracy": sum(row["special_zodiac_hit"] for row in segment) / len(segment),
            "special_number_accuracy": sum(row["special_number_hit"] for row in segment) / len(segment),
            "special_zodiac_top3_accuracy": sum(row["special_zodiac_top3_hit"] for row in segment) / len(segment),
        })
    return {
        "schema": "lottery-backtest/v1",
        "method_version": model,
        "no_repeat_enabled": no_repeat,
        "folds": folds,
        "first_target_issue": rows[0]["target_issue"] if rows else None,
        "last_target_issue": rows[-1]["target_issue"] if rows else None,
        "special_zodiac_hits": sum(row["special_zodiac_hit"] for row in rows),
        "special_zodiac_accuracy": sum(row["special_zodiac_hit"] for row in rows) / max(folds, 1),
        "special_number_hits": sum(row["special_number_hit"] for row in rows),
        "special_number_accuracy": sum(row["special_number_hit"] for row in rows) / max(folds, 1),
        "special_zodiac_top3_hits": sum(row["special_zodiac_top3_hit"] for row in rows),
        "special_zodiac_top3_accuracy": sum(row["special_zodiac_top3_hit"] for row in rows) / max(folds, 1),
        "special_number_top4_hits": sum(row["special_number_top4_hit"] for row in rows),
        "special_number_top4_accuracy": sum(row["special_number_top4_hit"] for row in rows) / max(folds, 1),
        "average_regular_hits": sum(row["regular_hit_count"] for row in rows) / max(folds, 1),
        "regular_three_exact_hits": sum(row["regular_three_exact_hit"] for row in rows),
        "regular_three_exact_accuracy": sum(row["regular_three_exact_hit"] for row in rows) / max(folds, 1),
        "average_regular_three_hits": sum(row["regular_three_hit_count"] for row in rows) / max(folds, 1),
        "no_repeat_constraint_folds": sum(
            row_index > 0 and rows[row_index - 1]["special_number_hit"] is False
            for row_index in range(folds)
        ),
        "chronological_segments": segments,
        "rows": rows,
    }


def evaluate_models(records, min_train=30):
    """Compare fixed candidates on identical expanding-window targets; never tune on the final draw."""
    results = []
    for model in MODEL_CONFIGS:
        for no_repeat in (False, True):
            evidence = backtest(records, min_train, model, no_repeat)
            results.append({key: value for key, value in evidence.items() if key != "rows"})
    benchmark = next(row for row in results if row["method_version"] == "random-uniform" and not row["no_repeat_enabled"])
    for row in results:
        row["zodiac_top1_lift_vs_random"] = row["special_zodiac_accuracy"] - benchmark["special_zodiac_accuracy"]
        row["number_top1_lift_vs_random"] = row["special_number_accuracy"] - benchmark["special_number_accuracy"]
    return {
        "schema": "lottery-model-evaluation/v1",
        "evaluation": "expanding-window; identical targets and deterministic seeds",
        "min_train": min_train,
        "models": results,
        "promotion_rule": "Do not replace the production model unless a fixed candidate beats random and trend-v3 on zodiac Top-1, remains competitive on Top-3/number/regular metrics, and the result persists across multiple time segments and genuine saved reviews.",
    }


def wilson_interval(hits, trials, z=1.96):
    if trials <= 0:
        return [0.0, 1.0]
    rate = hits / trials
    denominator = 1 + z * z / trials
    centre = rate + z * z / (2 * trials)
    spread = z * sqrt(rate * (1 - rate) / trials + z * z / (4 * trials * trials))
    return [(centre - spread) / denominator, (centre + spread) / denominator]


def load_canonical_reviews(reviews_dir):
    if not reviews_dir:
        return []
    selected = {}
    for path in sorted(Path(reviews_dir).glob("review-*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        issue = row.get("target_issue") or row.get("actual_issue")
        if not issue:
            continue
        if issue not in selected or row.get("correction_of"):
            selected[issue] = row
    return [selected[issue] for issue in sorted(selected, key=int)]


def latest_missed_special_constraint(records, reviews_dir):
    reviews = load_canonical_reviews(reviews_dir)
    if not reviews:
        return None, None
    latest = reviews[-1]
    cutoff_issue = newest(records)[0]["issue"]
    if latest.get("actual_issue") != cutoff_issue or latest.get("special_number_hit") is not False:
        return None, None
    return latest.get("predicted_special_zodiac"), latest.get("predicted_special_number")


def forecast_assessment(records, prediction, reviews_dir=None, min_train=30):
    evidence = backtest(records, min_train)
    reviews = load_canonical_reviews(reviews_dir)
    folds = evidence["folds"]
    walk_hits = evidence["special_zodiac_hits"]
    saved_hits = sum(row.get("special_zodiac_hit", False) for row in reviews)
    saved_count = len(reviews)
    random_baseline = 1 / len(ANIMALS)
    walk_interval = wilson_interval(walk_hits, folds)
    saved_interval = wilson_interval(saved_hits, saved_count)
    ranked = prediction["ranked_special_zodiacs"]
    margin = ranked[0]["score"] - ranked[1]["score"] if len(ranked) > 1 else 0.0
    demonstrated = (
        folds >= 60
        and saved_count >= 20
        and walk_interval[0] > random_baseline
        and saved_interval[0] > random_baseline
    )
    return {
        "status": "demonstrated_edge" if demonstrated else "no_demonstrated_edge",
        "strong_pick": bool(demonstrated and margin >= 0.02),
        "ranking_margin": round(margin, 6),
        "random_zodiac_baseline": round(random_baseline, 6),
        "walk_forward": {
            "folds": folds,
            "hits": walk_hits,
            "accuracy": round(evidence["special_zodiac_accuracy"], 6),
            "wilson_95": [round(value, 6) for value in walk_interval],
        },
        "saved_reviews": {
            "count": saved_count,
            "hits": saved_hits,
            "accuracy": round(saved_hits / saved_count, 6) if saved_count else None,
            "wilson_95": [round(value, 6) for value in saved_interval],
        },
        "decision_rule": "Strong pick requires at least 60 walk-forward folds and 20 saved reviews, with both 95% lower bounds above the 1/12 random-zodiac baseline.",
    }


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="cmd", required=True)
    analyze_parser = commands.add_parser("analyze")
    analyze_parser.add_argument("records")
    analyze_parser.add_argument("--out")
    predict_parser = commands.add_parser("predict")
    predict_parser.add_argument("records")
    predict_parser.add_argument("--seed", type=int, default=20260811)
    predict_parser.add_argument("--reviews-dir")
    predict_parser.add_argument("--out")
    review_parser = commands.add_parser("review")
    review_parser.add_argument("records")
    review_parser.add_argument("prediction")
    review_parser.add_argument("--new-result", required=True)
    review_parser.add_argument("--out")
    backtest_parser = commands.add_parser("backtest")
    backtest_parser.add_argument("records")
    backtest_parser.add_argument("--min-train", type=int, default=30)
    backtest_parser.add_argument("--out")
    evaluate_parser = commands.add_parser("evaluate")
    evaluate_parser.add_argument("records")
    evaluate_parser.add_argument("--min-train", type=int, default=30)
    evaluate_parser.add_argument("--out")
    args = parser.parse_args()
    if args.cmd == "analyze":
        obj = analysis(load_records(args.records))
    elif args.cmd == "predict":
        records = load_records(args.records)
        excluded_zodiac, excluded_number = latest_missed_special_constraint(records, args.reviews_dir)
        obj = predict(records, args.seed, excluded_zodiac, excluded_number)
        obj["forecast_assessment"] = forecast_assessment(records, obj, args.reviews_dir)
    elif args.cmd == "backtest":
        obj = backtest(load_records(args.records), args.min_train)
    elif args.cmd == "evaluate":
        obj = evaluate_models(load_records(args.records), args.min_train)
    else:
        prediction = json.loads(Path(args.prediction).read_text(encoding="utf-8"))
        result = json.loads(Path(args.new_result).read_text(encoding="utf-8"))
        actual = result["records"][0] if isinstance(result, dict) and "records" in result else result
        obj = review(prediction, actual)
    dump(obj, args.out)


if __name__ == "__main__":
    main()
