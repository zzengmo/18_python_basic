#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
터미널 테트리스 (curses 기반)
실행: python3 tetris.py

조작법:
  ← / →   : 좌우 이동
  ↓       : 소프트 드롭 (한 칸 빠르게 내리기)
  ↑       : 회전
  space   : 하드 드롭 (즉시 바닥까지 떨어뜨리기)
  p       : 일시정지
  q       : 종료
"""

import curses
import random
import time

# ----------------------------------------------------------------------
# 보드 크기
BOARD_W = 10
BOARD_H = 20

# 테트로미노 정의 (각 회전 상태를 4x4 좌표 리스트로 정의)
SHAPES = {
    'I': [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    'O': [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    'T': [
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (0, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
    ],
    'S': [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    'Z': [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    'J': [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 0)],
    ],
    'L': [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

COLOR_MAP = {
    'I': 1, 'O': 2, 'T': 3, 'S': 4, 'Z': 5, 'J': 6, 'L': 7,
}


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.rot = 0
        self.row = 0
        self.col = BOARD_W // 2 - 2

    def cells(self, rot=None, row=None, col=None):
        rot = self.rot if rot is None else rot
        row = self.row if row is None else row
        col = self.col if col is None else col
        shape = SHAPES[self.kind]
        rot = rot % len(shape)
        return [(row + r, col + c) for (r, c) in shape[rot]]


def new_bag():
    bag = list(SHAPES.keys())
    random.shuffle(bag)
    return bag


class Game:
    def __init__(self):
        self.board = [[None] * BOARD_W for _ in range(BOARD_H)]
        self.bag = new_bag()
        self.next_kind = self.bag.pop()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.spawn_piece()

    def spawn_piece(self):
        if not self.bag:
            self.bag = new_bag()
        kind = self.next_kind
        self.next_kind = self.bag.pop()
        self.current = Piece(kind)
        if not self.valid(self.current.cells()):
            self.game_over = True

    def valid(self, cells):
        for r, c in cells:
            if c < 0 or c >= BOARD_W or r >= BOARD_H:
                return False
            if r >= 0 and self.board[r][c] is not None:
                return False
        return True

    def lock_piece(self):
        for r, c in self.current.cells():
            if r >= 0:
                self.board[r][c] = self.current.kind
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_H - len(new_board)
        if cleared:
            self.lines += cleared
            self.score += [0, 100, 300, 500, 800][cleared] * self.level
            self.level = 1 + self.lines // 10
            for _ in range(cleared):
                new_board.insert(0, [None] * BOARD_W)
            self.board = new_board

    def move(self, dr, dc):
        cells = self.current.cells(row=self.current.row + dr, col=self.current.col + dc)
        if self.valid(cells):
            self.current.row += dr
            self.current.col += dc
            return True
        return False

    def rotate(self):
        new_rot = self.current.rot + 1
        for kick in (0, -1, 1, -2, 2):
            cells = self.current.cells(rot=new_rot, col=self.current.col + kick)
            if self.valid(cells):
                self.current.rot = new_rot % len(SHAPES[self.current.kind])
                self.current.col += kick
                return

    def hard_drop(self):
        while self.move(1, 0):
            self.score += 2
        self.lock_piece()

    def soft_drop_step(self):
        if not self.move(1, 0):
            self.lock_piece()
        else:
            self.score += 1

    def ghost_row(self):
        piece = self.current
        r = piece.row
        while self.valid(piece.cells(row=r + 1)):
            r += 1
        return r

    def drop_interval(self):
        return max(0.08, 0.6 - (self.level - 1) * 0.05)


def draw(stdscr, game):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    board_left = 2
    board_top = 1

    # 테두리
    for r in range(BOARD_H + 2):
        stdscr.addstr(board_top + r, board_left, "#" + " " * (BOARD_W * 2) + "#")
    for c in range(BOARD_W * 2 + 2):
        try:
            stdscr.addch(board_top, board_left + c, '#')
            stdscr.addch(board_top + BOARD_H + 1, board_left + c, '#')
        except curses.error:
            pass

    # 고정된 블록
    for r in range(BOARD_H):
        for c in range(BOARD_W):
            kind = game.board[r][c]
            if kind:
                attr = curses.color_pair(COLOR_MAP[kind])
                try:
                    stdscr.addstr(board_top + 1 + r, board_left + 1 + c * 2, "[]", attr)
                except curses.error:
                    pass

    # 고스트 피스
    if not game.game_over:
        ghost_r = game.ghost_row()
        for r, c in game.current.cells(row=ghost_r):
            if 0 <= r < BOARD_H and 0 <= c < BOARD_W:
                try:
                    stdscr.addstr(board_top + 1 + r, board_left + 1 + c * 2, "..",
                                  curses.color_pair(COLOR_MAP[game.current.kind]) | curses.A_DIM)
                except curses.error:
                    pass

        # 현재 피스
        attr = curses.color_pair(COLOR_MAP[game.current.kind]) | curses.A_BOLD
        for r, c in game.current.cells():
            if 0 <= r < BOARD_H and 0 <= c < BOARD_W:
                try:
                    stdscr.addstr(board_top + 1 + r, board_left + 1 + c * 2, "[]", attr)
                except curses.error:
                    pass

    # 사이드 패널
    panel_x = board_left + BOARD_W * 2 + 5
    stdscr.addstr(board_top, panel_x, "TETRIS", curses.A_BOLD)
    stdscr.addstr(board_top + 2, panel_x, f"점수: {game.score}")
    stdscr.addstr(board_top + 3, panel_x, f"라인: {game.lines}")
    stdscr.addstr(board_top + 4, panel_x, f"레벨: {game.level}")

    stdscr.addstr(board_top + 6, panel_x, "다음 블록:")
    next_shape = SHAPES[game.next_kind][0]
    attr = curses.color_pair(COLOR_MAP[game.next_kind])
    for (r, c) in next_shape:
        try:
            stdscr.addstr(board_top + 7 + r, panel_x + c * 2, "[]", attr)
        except curses.error:
            pass

    controls_y = board_top + 13
    lines_help = [
        "조작법:",
        " ←/→ : 이동",
        " ↓   : 소프트드롭",
        " ↑   : 회전",
        " space: 하드드롭",
        " p   : 일시정지",
        " q   : 종료",
    ]
    for i, line in enumerate(lines_help):
        try:
            stdscr.addstr(controls_y + i, panel_x, line)
        except curses.error:
            pass

    if game.paused:
        msg = "-- 일시정지 (p로 재개) --"
        try:
            stdscr.addstr(board_top + BOARD_H // 2, board_left + 1, msg, curses.A_REVERSE)
        except curses.error:
            pass

    if game.game_over:
        msg = "GAME OVER - q로 종료"
        try:
            stdscr.addstr(board_top + BOARD_H // 2, board_left + 1, msg, curses.A_REVERSE)
        except curses.error:
            pass

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, 8):
        curses.init_pair(i, i, -1)

    game = Game()
    last_drop = time.time()

    while True:
        key = stdscr.getch()

        if key == ord('q'):
            break
        elif key == ord('p'):
            game.paused = not game.paused

        if not game.game_over and not game.paused:
            if key == curses.KEY_LEFT:
                game.move(0, -1)
            elif key == curses.KEY_RIGHT:
                game.move(0, 1)
            elif key == curses.KEY_DOWN:
                game.soft_drop_step()
            elif key == curses.KEY_UP:
                game.rotate()
            elif key == ord(' '):
                game.hard_drop()

            now = time.time()
            if now - last_drop > game.drop_interval():
                if not game.move(1, 0):
                    game.lock_piece()
                last_drop = now

        draw(stdscr, game)
        time.sleep(0.02)


if __name__ == "__main__":
    curses.wrapper(main)