#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
던전 탐험 로그라이크
실행: python3 dungeon.py

조작법:
  방향키 : 이동 (벽에 부딪히면 안 움직임, 몬스터가 있으면 공격)
  q      : 종료

목표:
  '>' 계단을 찾아 내려가며 최대한 깊이 내려가세요.
  몬스터('g','o','T' 등)에게 부딪히면 전투가 시작됩니다.
  'HP' 물약('!')을 밟으면 체력을 회복합니다.
  체력이 0이 되면 게임 오버.
"""

import curses
import random

W, H = 50, 18  # 던전 크기


class Monster:
    def __init__(self, name, symbol, hp, atk_lo, atk_hi, xp):
        self.name = name
        self.symbol = symbol
        self.hp = hp
        self.max_hp = hp
        self.atk_lo = atk_lo
        self.atk_hi = atk_hi
        self.xp = xp

    def attack(self):
        return random.randint(self.atk_lo, self.atk_hi)


def monster_pool(depth):
    """깊이에 따라 등장 가능한 몬스터 종류와 스탯을 반환"""
    pool = [
        ("고블린", "g", 6 + depth, 1, 3 + depth // 2, 5),
        ("오크", "o", 10 + depth * 2, 2, 4 + depth // 2, 10),
    ]
    if depth >= 3:
        pool.append(("트롤", "T", 18 + depth * 2, 3, 6 + depth // 2, 20))
    if depth >= 6:
        pool.append(("드래곤", "D", 30 + depth * 3, 5, 9 + depth // 2, 50))
    return pool


class Player:
    def __init__(self):
        self.hp = 25
        self.max_hp = 25
        self.atk_lo = 3
        self.atk_hi = 6
        self.depth = 1
        self.kills = 0
        self.score = 0

    def attack(self):
        return random.randint(self.atk_lo, self.atk_hi)


def carve_room(grid, x, y, w, h):
    for ry in range(y, y + h):
        for rx in range(x, x + w):
            grid[ry][rx] = '.'


def carve_corridor(grid, x1, y1, x2, y2):
    x, y = x1, y1
    if random.random() < 0.5:
        while x != x2:
            grid[y][x] = '.'
            x += 1 if x2 > x else -1
        while y != y2:
            grid[y][x] = '.'
            y += 1 if y2 > y else -1
    else:
        while y != y2:
            grid[y][x] = '.'
            y += 1 if y2 > y else -1
        while x != x2:
            grid[y][x] = '.'
            x += 1 if x2 > x else -1
    grid[y2][x2] = '.'


def generate_level(depth):
    grid = [['#'] * W for _ in range(H)]
    rooms = []
    attempts = 0
    room_count = random.randint(5, 8)

    while len(rooms) < room_count and attempts < 200:
        attempts += 1
        rw, rh = random.randint(4, 8), random.randint(3, 5)
        rx, ry = random.randint(1, W - rw - 2), random.randint(1, H - rh - 2)
        new_room = (rx, ry, rw, rh)
        overlap = any(
            rx < ox + ow + 1 and rx + rw + 1 > ox and
            ry < oy + oh + 1 and ry + rh + 1 > oy
            for (ox, oy, ow, oh) in rooms
        )
        if not overlap:
            carve_room(grid, rx, ry, rw, rh)
            rooms.append(new_room)

    centers = [(rx + rw // 2, ry + rh // 2) for (rx, ry, rw, rh) in rooms]
    for i in range(len(centers) - 1):
        carve_corridor(grid, centers[i][0], centers[i][1], centers[i + 1][0], centers[i + 1][1])

    start = centers[0]
    stairs = centers[-1]
    grid[stairs[1]][stairs[0]] = '>'

    floor_tiles = [
        (x, y) for y in range(H) for x in range(W)
        if grid[y][x] == '.' and (x, y) not in (start, stairs)
    ]
    random.shuffle(floor_tiles)

    monsters = {}
    pool = monster_pool(depth)
    n_monsters = min(len(floor_tiles), 3 + depth)
    for _ in range(n_monsters):
        if not floor_tiles:
            break
        pos = floor_tiles.pop()
        name, sym, hp, alo, ahi, xp = random.choice(pool)
        monsters[pos] = Monster(name, sym, hp, alo, ahi, xp)

    items = {}
    n_items = min(len(floor_tiles), 2 + depth // 2)
    for _ in range(n_items):
        if not floor_tiles:
            break
        pos = floor_tiles.pop()
        items[pos] = '!'

    return grid, start, stairs, monsters, items


MESSAGES = []


def log(msg):
    MESSAGES.append(msg)
    if len(MESSAGES) > 6:
        MESSAGES.pop(0)


def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    max_len = w - x
    if max_len <= 0:
        return
    try:
        stdscr.addstr(y, x, text[:max_len], attr)
    except curses.error:
        pass


def draw(stdscr, grid, player_pos, player, monsters, items):
    stdscr.erase()
    px, py = player_pos

    for y in range(H):
        row_chars = []
        for x in range(W):
            if (x, y) == (px, py):
                row_chars.append('@')
            elif (x, y) in monsters:
                row_chars.append(monsters[(x, y)].symbol)
            elif (x, y) in items:
                row_chars.append(items[(x, y)])
            else:
                row_chars.append(grid[y][x])
        safe_addstr(stdscr, y + 1, 1, "".join(row_chars))

    panel_x = W + 4
    safe_addstr(stdscr, 1, panel_x, "== 던전 탐험 ==", curses.A_BOLD)
    safe_addstr(stdscr, 3, panel_x, f"깊이: {player.depth}")
    hp_bar = "♥" * max(0, player.hp) 
    safe_addstr(stdscr, 4, panel_x, f"HP: {player.hp}/{player.max_hp}")
    safe_addstr(stdscr, 5, panel_x, f"공격력: {player.atk_lo}-{player.atk_hi}")
    safe_addstr(stdscr, 6, panel_x, f"처치: {player.kills}  점수: {player.score}")

    safe_addstr(stdscr, 8, panel_x, "조작: 방향키 이동, q 종료")
    safe_addstr(stdscr, 9, panel_x, "'>' 계단, '!' 물약")

    safe_addstr(stdscr, 11, panel_x, "--- 메시지 ---")
    for i, msg in enumerate(MESSAGES[-6:]):
        safe_addstr(stdscr, 12 + i, panel_x, msg[:30])

    stdscr.refresh()


def combat(player, monster):
    dmg = player.attack()
    monster.hp -= dmg
    log(f"{monster.name}에게 {dmg} 피해!")
    if monster.hp <= 0:
        log(f"{monster.name}을(를) 처치했습니다! (+{monster.xp}점)")
        player.kills += 1
        player.score += monster.xp
        return True  # 몬스터 사망
    mdmg = monster.attack()
    player.hp -= mdmg
    log(f"{monster.name}이(가) {mdmg} 피해를 입혔습니다.")
    return False


def game_over_screen(stdscr, player):
    stdscr.erase()
    lines = [
        "=== GAME OVER ===",
        f"도달 깊이: {player.depth}",
        f"처치한 몬스터: {player.kills}",
        f"최종 점수: {player.score}",
        "",
        "아무 키나 누르면 종료합니다.",
    ]
    for i, line in enumerate(lines):
        safe_addstr(stdscr, 2 + i, 4, line, curses.A_BOLD)
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()

    player = Player()
    grid, start, stairs, monsters, items = generate_level(player.depth)
    pos = start
    log("던전에 입장했습니다. 조심하세요!")

    while True:
        draw(stdscr, grid, pos, player, monsters, items)

        if player.hp <= 0:
            log("당신은 쓰러졌습니다...")
            draw(stdscr, grid, pos, player, monsters, items)
            game_over_screen(stdscr, player)
            break

        key = stdscr.getch()
        dx, dy = 0, 0
        if key == ord('q'):
            break
        elif key == curses.KEY_LEFT:
            dx = -1
        elif key == curses.KEY_RIGHT:
            dx = 1
        elif key == curses.KEY_UP:
            dy = -1
        elif key == curses.KEY_DOWN:
            dy = 1
        else:
            continue

        nx, ny = pos[0] + dx, pos[1] + dy
        if not (0 <= nx < W and 0 <= ny < H):
            continue
        if grid[ny][nx] == '#':
            continue

        target = (nx, ny)

        if target in monsters:
            dead = combat(player, monsters[target])
            if dead:
                del monsters[target]
            continue  # 전투 턴에는 이동하지 않음

        pos = target

        if pos in items:
            player.hp = min(player.max_hp, player.hp + 8)
            log("물약을 마셔 체력을 회복했습니다! (+8)")
            del items[pos]

        if pos == stairs:
            player.depth += 1
            log(f"계단을 내려갑니다. (깊이 {player.depth})")
            grid, start, stairs, monsters, items = generate_level(player.depth)
            pos = start


if __name__ == "__main__":
    curses.wrapper(main)