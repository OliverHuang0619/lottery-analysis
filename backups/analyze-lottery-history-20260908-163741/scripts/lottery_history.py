#!/usr/bin/env python3
import argparse
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ANIMALS = list("鼠牛虎兔龙蛇马羊猴鸡狗猪")
POSITIONS = ["平一", "平二", "平三", "平四", "平五", "平六", "特码"]


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


def trend_components(items, key, candidates, half_life=8):
    """Use observed rolling trends; never reward an outcome for being overdue."""
    count = max(len(items), 1)
    full = Counter(key(item) for item in items)
    recent30 = Counter(key(item) for item in items[-30:])
    recent10 = Counter(key(item) for item in items[-10:])
    weights = [0.5 ** ((len(items) - 1 - i) / half_life) for i in range(len(items))]
    weight_total = max(sum(weights), 1e-12)
    decayed = Counter()
    for item, weight in zip(items, weights):
        decayed[key(item)] += weight
    result = {}
    for value in candidates:
        components = {
            "history": 0.20 * full[value] / count,
            "recent30": 0.25 * recent30[value] / max(min(30, len(items)), 1),
            "recent10": 0.30 * recent10[value] / max(min(10, len(items)), 1),
            "ewma": 0.25 * decayed[value] / weight_total,
            "overdue": 0.0,
        }
        result[value] = {"score": sum(components.values()), "components": components}
    return result


def predict(records, seed=20260811):
    desc = newest(records)
    chronological = list(reversed(desc))
    mapping = zodiac_map(desc)
    all_rows = [row for record in chronological for row in record["numbers"]]
    special_rows = [record["numbers"][6] for record in chronological]
    number_rank = trend_components(all_rows, lambda row: row["number"], range(1, 50))
    rng = random.Random(seed)
    number_scores = {n: number_rank[n]["score"] + rng.random() * 1e-12 for n in range(1, 50)}
    regular = []
    for number in sorted(number_scores, key=number_scores.get, reverse=True):
        trial = regular + [number]
        if sum(x % 2 for x in trial) <= 5 and sum(x <= 24 for x in trial) <= 5 and sum(x % 10 == number % 10 for x in regular) < 2:
            regular.append(number)
        if len(regular) == 6:
            break
    zodiac_rank = trend_components(special_rows, lambda row: row["zodiac"], ANIMALS)
    ranked_zodiacs = sorted(ANIMALS, key=lambda z: (zodiac_rank[z]["score"], z), reverse=True)
    top_zodiac = ranked_zodiacs[0]
    candidates = [n for n in range(1, 50) if mapping.get(n) == top_zodiac]
    special_rank = trend_components(special_rows, lambda row: row["number"], candidates)
    ranked_numbers = sorted(candidates, key=lambda n: (special_rank[n]["score"], n), reverse=True)
    special_number = ranked_numbers[0]
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

    return {
        "schema": "lottery-prediction/v3",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cutoff_issue": desc[0]["issue"],
        "target_issue": f"{int(desc[0]['issue']) + 1:03d}",
        "method_version": "trend-zodiac-first-v3",
        "seed": seed,
        "regular": [{"number": n, "zodiac": mapping.get(n, "未知"), **packed(number_rank[n])} for n in sorted(regular)],
        "top_special_zodiac": {"zodiac": top_zodiac, **packed(zodiac_rank[top_zodiac])},
        "ranked_special_zodiacs": [{"zodiac": z, **packed(zodiac_rank[z])} for z in ranked_zodiacs[:3]],
        "special": {"number": special_number, "zodiac": top_zodiac, **packed(special_rank[special_number])},
        "numbers_in_top_zodiac": [{"number": n, "zodiac": top_zodiac, **packed(special_rank[n])} for n in ranked_numbers[:4]],
        "weights": {"history": 0.20, "recent30": 0.25, "recent10": 0.30, "ewma_half_life_8": 0.25, "overdue": 0.0},
        "disclaimer": "仅供统计娱乐；走势排名不是开奖概率，随机开奖无法被可靠预测。",
    }


def review(prediction, actual):
    predicted_regular = {row["number"] for row in prediction["regular"]}
    actual_regular = {row["number"] for row in actual["numbers"][:6]}
    predicted_special = prediction["special"]
    actual_special = actual["numbers"][6]
    return {
        "cutoff_issue": prediction.get("cutoff_issue"),
        "target_issue": prediction.get("target_issue", actual["issue"]),
        "actual_issue": actual["issue"],
        "method_version": prediction.get("method_version"),
        "prediction_created_at": prediction.get("created_at"),
        "predicted_special_number": predicted_special["number"],
        "actual_special_number": actual_special["number"],
        "special_number_hit": predicted_special["number"] == actual_special["number"],
        "predicted_special_zodiac": predicted_special.get("zodiac"),
        "actual_special_zodiac": actual_special.get("zodiac"),
        "special_zodiac_hit": predicted_special.get("zodiac") == actual_special.get("zodiac"),
        "special_pick_regular_hit": predicted_special["number"] in actual_regular,
        "regular_hits": sorted(predicted_regular & actual_regular),
        "regular_hit_count": len(predicted_regular & actual_regular),
        "any_overlap": sorted((predicted_regular | {predicted_special["number"]}) & (actual_regular | {actual_special["number"]})),
        "special_abs_error": abs(predicted_special["number"] - actual_special["number"]),
    }


def backtest(records, min_train=30):
    chronological = sorted(records, key=lambda record: int(record["issue"]))
    rows = []
    for i in range(min_train, len(chronological)):
        rows.append(review(predict(chronological[:i], seed=20260811 + i), chronological[i]))
    folds = len(rows)
    return {
        "schema": "lottery-backtest/v1",
        "method_version": "trend-zodiac-first-v3",
        "folds": folds,
        "first_target_issue": rows[0]["target_issue"] if rows else None,
        "last_target_issue": rows[-1]["target_issue"] if rows else None,
        "special_zodiac_hits": sum(row["special_zodiac_hit"] for row in rows),
        "special_zodiac_accuracy": sum(row["special_zodiac_hit"] for row in rows) / max(folds, 1),
        "special_number_hits": sum(row["special_number_hit"] for row in rows),
        "special_number_accuracy": sum(row["special_number_hit"] for row in rows) / max(folds, 1),
        "average_regular_hits": sum(row["regular_hit_count"] for row in rows) / max(folds, 1),
        "rows": rows,
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
    args = parser.parse_args()
    if args.cmd == "analyze":
        obj = analysis(load_records(args.records))
    elif args.cmd == "predict":
        obj = predict(load_records(args.records), args.seed)
    elif args.cmd == "backtest":
        obj = backtest(load_records(args.records), args.min_train)
    else:
        prediction = json.loads(Path(args.prediction).read_text(encoding="utf-8"))
        result = json.loads(Path(args.new_result).read_text(encoding="utf-8"))
        actual = result["records"][0] if isinstance(result, dict) and "records" in result else result
        obj = review(prediction, actual)
    dump(obj, args.out)


if __name__ == "__main__":
    main()
