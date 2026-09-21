#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블랙잭 (Blackjack) - 터미널 게임 (코인 시스템 포함)
실행: python3 blackjack.py

규칙:
  - 처음 시작하면 코인 1000개를 지급받습니다.
  - 매 판마다 코인을 걸고(베팅) 플레이합니다.
  - 카드 합이 21에 가까우면서 21을 넘지 않으면 승리.
  - 블랙잭(처음 두 장으로 21)은 1.5배 배당.
  - 코인은 같은 폴더의 balance.json 파일에 저장되어, 다음에 실행해도 이어집니다.
  - 코인이 0이 되면 게임 오버. 'reset'을 입력하면 코인을 초기화할 수 있습니다.

조작:
  h : 히트 (카드 한 장 더 받기)
  s : 스탠드 (그만 받고 딜러 차례로)
"""

import json
import os
import random

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "balance.json")
STARTING_BALANCE = 1000

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def load_balance():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("balance", STARTING_BALANCE))
        except (json.JSONDecodeError, ValueError):
            pass
    return STARTING_BALANCE


def save_balance(balance):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump({"balance": balance}, f)


def new_deck():
    deck = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def card_str(card):
    rank, suit = card
    return f"[{rank}{suit}]"


def hand_str(hand, hide_first=False):
    if hide_first:
        return "[??] " + " ".join(card_str(c) for c in hand[1:])
    return " ".join(card_str(c) for c in hand)


def hand_value(hand):
    total = 0
    aces = 0
    for rank, _ in hand:
        if rank == "A":
            total += 11
            aces += 1
        elif rank in ("J", "Q", "K"):
            total += 10
        else:
            total += int(rank)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def is_blackjack(hand):
    return len(hand) == 2 and hand_value(hand) == 21


def draw_card(deck):
    if not deck:
        deck.extend(new_deck())
    return deck.pop()


def ask_bet(balance):
    while True:
        raw = input(f"\n현재 코인: {balance}\n베팅할 금액을 입력하세요 (그만두려면 'q'): ").strip()
        if raw.lower() == "q":
            return None
        try:
            bet = int(raw)
            if 1 <= bet <= balance:
                return bet
        except ValueError:
            pass
        print("→ 1 이상, 보유 코인 이하의 숫자를 입력해주세요.")


def play_round(balance):
    deck = new_deck()
    player = [draw_card(deck), draw_card(deck)]
    dealer = [draw_card(deck), draw_card(deck)]

    bet = ask_bet(balance)
    if bet is None:
        return balance, False  # 종료 신호

    print(f"\n딜러: {hand_str(dealer, hide_first=True)}")
    print(f"플레이어: {hand_str(player)}  (합계: {hand_value(player)})")

    player_blackjack = is_blackjack(player)
    dealer_blackjack = is_blackjack(dealer)

    if not player_blackjack:
        while True:
            if hand_value(player) >= 21:
                break
            action = input("h(히트) / s(스탠드) ? ").strip().lower()
            if action == "h":
                player.append(draw_card(deck))
                print(f"플레이어: {hand_str(player)}  (합계: {hand_value(player)})")
                if hand_value(player) > 21:
                    print("→ 버스트! 21을 초과했습니다.")
                    break
            elif action == "s":
                break
            else:
                print("→ 'h' 또는 's'를 입력해주세요.")

    player_total = hand_value(player)

    # 딜러 차례 (플레이어가 버스트해도 카드는 공개)
    print(f"\n딜러 카드 공개: {hand_str(dealer)}  (합계: {hand_value(dealer)})")

    if player_total <= 21 and not player_blackjack:
        while hand_value(dealer) < 17:
            dealer.append(draw_card(deck))
            print(f"딜러 히트: {hand_str(dealer)}  (합계: {hand_value(dealer)})")

    dealer_total = hand_value(dealer)

    # 결과 판정
    print("\n--- 결과 ---")
    print(f"플레이어: {player_total} ({'블랙잭' if player_blackjack else '버스트' if player_total > 21 else ''})")
    print(f"딜러: {dealer_total} ({'블랙잭' if dealer_blackjack else '버스트' if dealer_total > 21 else ''})")

    if player_blackjack and dealer_blackjack:
        print("결과: 둘 다 블랙잭 → 무승부 (베팅금 반환)")
    elif player_blackjack:
        winnings = int(bet * 1.5)
        balance += winnings
        print(f"결과: 블랙잭 승리! +{winnings} 코인")
    elif dealer_blackjack:
        balance -= bet
        print(f"결과: 딜러 블랙잭 → 패배. -{bet} 코인")
    elif player_total > 21:
        balance -= bet
        print(f"결과: 버스트 → 패배. -{bet} 코인")
    elif dealer_total > 21:
        balance += bet
        print(f"결과: 딜러 버스트 → 승리! +{bet} 코인")
    elif player_total > dealer_total:
        balance += bet
        print(f"결과: 승리! +{bet} 코인")
    elif player_total < dealer_total:
        balance -= bet
        print(f"결과: 패배. -{bet} 코인")
    else:
        print("결과: 무승부 (푸시). 베팅금 반환")

    return balance, True


def main():
    print("=" * 40)
    print("블랙잭 (Blackjack)")
    print("=" * 40)

    balance = load_balance()
    print(f"보유 코인: {balance}")

    if balance <= 0:
        choice = input("코인이 0입니다. 초기화하시겠습니까? (y/n): ").strip().lower()
        if choice == "y":
            balance = STARTING_BALANCE
            save_balance(balance)
            print(f"코인이 {STARTING_BALANCE}로 초기화되었습니다.")
        else:
            print("코인이 없어 게임을 시작할 수 없습니다.")
            return

    while True:
        if balance <= 0:
            print("\n코인을 모두 잃었습니다. 게임 오버!")
            choice = input("코인을 초기화하고 다시 시작할까요? (y/n): ").strip().lower()
            if choice == "y":
                balance = STARTING_BALANCE
                save_balance(balance)
                continue
            else:
                break

        balance, keep_playing = play_round(balance)
        save_balance(balance)

        if not keep_playing:
            print(f"\n게임을 종료합니다. 최종 코인: {balance}")
            break

        print(f"\n[현재 코인: {balance}]")
        again = input("한 판 더? (엔터: 계속, q: 종료): ").strip().lower()
        if again == "q":
            print(f"\n게임을 종료합니다. 최종 코인: {balance}")
            break


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n게임을 종료합니다.")