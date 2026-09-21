#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
야추 (Yahtzee) - 터미널 1인용 게임
실행: python3 yahtzee.py

규칙:
  - 매 라운드마다 주사위 5개를 최대 3번 굴릴 수 있습니다.
  - 굴릴 때마다 유지하고 싶은 주사위 번호(1~5)를 골라 남기고 나머지만 다시 굴립니다.
  - 3번의 굴림이 끝나면(또는 원할 때 바로) 아직 사용하지 않은 점수 항목 하나를 선택해 점수를 기록합니다.
  - 13개 항목을 모두 채우면 게임이 끝나고 총점을 보여줍니다.
"""

import random
from collections import Counter

CATEGORIES = [
    ("1", "1 (Aces)"),
    ("2", "2 (Twos)"),
    ("3", "3 (Threes)"),
    ("4", "4 (Fours)"),
    ("5", "5 (Fives)"),
    ("6", "6 (Sixes)"),
    ("3kind", "3 of a Kind (같은 눈 3개)"),
    ("4kind", "4 of a Kind (같은 눈 4개)"),
    ("fullhouse", "Full House (3+2 조합)"),
    ("smallst", "Small Straight (연속 4개)"),
    ("largest", "Large Straight (연속 5개)"),
    ("yahtzee", "Yahtzee (같은 눈 5개)"),
    ("chance", "Chance (주사위 합)"),
]
UPPER_KEYS = {"1", "2", "3", "4", "5", "6"}


def roll_dice(n=5):
    return [random.randint(1, 6) for _ in range(n)]


def score_category(key, dice):
    counts = Counter(dice)
    total = sum(dice)

    if key in UPPER_KEYS:
        num = int(key)
        return counts[num] * num

    if key == "3kind":
        return total if any(c >= 3 for c in counts.values()) else 0

    if key == "4kind":
        return total if any(c >= 4 for c in counts.values()) else 0

    if key == "fullhouse":
        vals = sorted(counts.values())
        return 25 if vals == [2, 3] else 0

    if key == "smallst":
        s = set(dice)
        runs = [{1, 2, 3, 4}, {2, 3, 4, 5}, {3, 4, 5, 6}]
        return 30 if any(r <= s for r in runs) else 0

    if key == "largest":
        s = set(dice)
        return 40 if s in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6}) else 0

    if key == "yahtzee":
        return 50 if any(c == 5 for c in counts.values()) else 0

    if key == "chance":
        return total

    return 0


def print_dice(dice):
    faces = {
        1: ["┌───┐", "│   │", "│ ● │", "│   │", "└───┘"],
        2: ["┌───┐", "│●  │", "│   │", "│  ●│", "└───┘"],
        3: ["┌───┐", "│●  │", "│ ● │", "│  ●│", "└───┘"],
        4: ["┌───┐", "│● ●│", "│   │", "│● ●│", "└───┘"],
        5: ["┌───┐", "│● ●│", "│ ● │", "│● ●│", "└───┘"],
        6: ["┌───┐", "│● ●│", "│● ●│", "│● ●│", "└───┘"],
    }
    for row in range(5):
        print("  ".join(faces[d][row] for d in dice))
    print("  ".join(f"  {i+1}  " for i in range(len(dice))))


def print_scorecard(scores):
    print("\n--- 점수표 ---")
    upper_sum = 0
    for key, label in CATEGORIES:
        val = scores.get(key)
        display = str(val) if val is not None else "-"
        print(f"  {label:<28}: {display}")
        if key in UPPER_KEYS and val is not None:
            upper_sum += val
    bonus = 35 if upper_sum >= 63 else 0
    total = sum(v for v in scores.values() if v is not None) + bonus
    print(f"  {'상단 합계(1~6)':<28}: {upper_sum} {'(보너스 +35 획득!)' if bonus else '(63 이상이면 +35 보너스)'}")
    print(f"  {'총점':<28}: {total}")
    print("-" * 30)


def choose_keep(dice, roll_num):
    while True:
        raw = input(
            f"[{roll_num}/3번째 굴림] 유지할 주사위 번호를 공백으로 구분해 입력 "
            f"(전부 다시 굴리려면 그냥 엔터): "
        ).strip()
        if raw == "":
            return []
        try:
            nums = [int(x) for x in raw.split()]
            if all(1 <= n <= len(dice) for n in nums):
                return sorted(set(nums))
        except ValueError:
            pass
        print("→ 1~5 사이 숫자를 공백으로 구분해서 입력해주세요.")


def play_turn(scores):
    dice = roll_dice()
    print("\n=== 새 라운드 ===")
    print_dice(dice)

    for roll_num in range(1, 3):
        keep = choose_keep(dice, roll_num)
        reroll_count = len(dice) - len(keep)
        if reroll_count == 0:
            break
        new_vals = roll_dice(reroll_count)
        it = iter(new_vals)
        dice = [dice[i - 1] if i in keep else next(it) for i in range(1, len(dice) + 1)]
        print(f"\n[{roll_num + 1}번째 결과]")
        print_dice(dice)

    # 남은 카테고리 표시 및 선택
    available = [(k, l) for k, l in CATEGORIES if scores.get(k) is None]
    print("\n선택 가능한 항목:")
    for i, (k, l) in enumerate(available, 1):
        preview = score_category(k, dice)
        print(f"  {i}. {l}  (이 주사위로 받으면 {preview}점)")

    while True:
        try:
            choice = int(input("기록할 항목 번호를 입력하세요: "))
            if 1 <= choice <= len(available):
                key, label = available[choice - 1]
                break
        except ValueError:
            pass
        print("→ 목록에 있는 번호를 입력해주세요.")

    points = score_category(key, dice)
    scores[key] = points
    print(f"→ '{label}'에 {points}점을 기록했습니다.")


def main():
    print("=" * 40)
    print("야추 (Yahtzee) - 1인용")
    print("=" * 40)

    scores = {key: None for key, _ in CATEGORIES}

    for round_num in range(1, len(CATEGORIES) + 1):
        print(f"\n########## 라운드 {round_num}/{len(CATEGORIES)} ##########")
        play_turn(scores)
        print_scorecard(scores)

    print("\n게임 종료! 최종 점수표입니다.")
    print_scorecard(scores)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n게임을 종료합니다.")