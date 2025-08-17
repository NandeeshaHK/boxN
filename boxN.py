"""
Dots & Boxes - Improved UI Boilerplate
- Python 3.8+
- pygame

Features (UI improvements):
 - Dedicated right sidebar for scores and controls (prevents overlay on grid).
 - Header area clear and padded.
 - Player-colored edges and faint filled claimed boxes.
 - Hover/preview line for selection feedback.
 - Centered non-obtrusive game-over modal + Restart (press R).
 - Click one dot then a neighboring dot (no diagonals).
 - Extra turn if you complete any box.

Usage:
    pip install pygame
    python dots_and_boxes_ui.py
"""

import pygame
import sys
from typing import Tuple, List, Dict, Set

# ----------------------------- CONFIG -------------------------------- #
ROWS = 4            # number of dot rows (m)
COLS = 6            # number of dot cols (n)
DOT_RADIUS = 7
CELL_SIZE = 90      # pixel distance between adjacent dots (cell size)
GRID_PADDING_TOP = 110  # space for header
SIDEBAR_WIDTH = 260  # right sidebar width
MARGIN = 40         # outer margin around grid area
LINE_WIDTH = 8
BG_COLOR = (250, 250, 250)
DOT_COLOR = (40, 40, 40)
TEXT_COLOR = (22, 22, 22)
UI_BG = (245, 245, 245)
FPS = 60

# Players: single-character initials are best
PLAYERS = ["A", "B", "C"]

# Compute window size
GRID_WIDTH = (COLS - 1) * CELL_SIZE
GRID_HEIGHT = (ROWS - 1) * CELL_SIZE
WIDTH = MARGIN * 2 + GRID_WIDTH + SIDEBAR_WIDTH
HEIGHT = MARGIN + GRID_PADDING_TOP + GRID_HEIGHT + MARGIN

# ----------------------------- STATE --------------------------------- #
# Dots are (r, c) with ranges r:0..ROWS-1, c:0..COLS-1
edges: Set[frozenset] = set()                    # set of frozenset({dot1, dot2})
edge_owner: Dict[frozenset, int] = {}           # edge -> player index
claimed_boxes: Dict[Tuple[int,int], int] = {}   # box top-left -> owner player idx
scores: List[int] = [0] * len(PLAYERS)
current_player_idx = 0
selected_dot = None  # type: Tuple[int,int] | None

# ----------------------------- HELPERS -------------------------------- #
def dot_to_pixel(dot: Tuple[int,int]) -> Tuple[int,int]:
    """Map grid dot (r,c) to screen pixel (x,y). Grid is placed left with margin."""
    r, c = dot
    x = MARGIN + c * CELL_SIZE
    y = GRID_PADDING_TOP + r * CELL_SIZE
    return x, y

def are_adjacent(d1: Tuple[int,int], d2: Tuple[int,int]) -> bool:
    dr = abs(d1[0] - d2[0])
    dc = abs(d1[1] - d2[1])
    return (dr == 1 and dc == 0) or (dr == 0 and dc == 1)

def normalized_edge(d1: Tuple[int,int], d2: Tuple[int,int]) -> frozenset:
    return frozenset([d1, d2])

def boxes_adjacent_to_edge(edge: frozenset) -> List[Tuple[int,int]]:
    pts = list(edge)
    (r1, c1), (r2, c2) = pts[0], pts[1]
    boxes = []
    if r1 == r2:  # horizontal: boxes above and below
        r = r1
        c_left = min(c1, c2)
        if 0 <= r-1 <= ROWS-2:
            boxes.append((r-1, c_left))
        if 0 <= r <= ROWS-2:
            boxes.append((r, c_left))
    elif c1 == c2:  # vertical: boxes left and right
        c = c1
        r_top = min(r1, r2)
        if 0 <= c-1 <= COLS-2:
            boxes.append((r_top, c-1))
        if 0 <= c <= COLS-2:
            boxes.append((r_top, c))
    return boxes

def box_edges(top_left: Tuple[int,int]) -> List[frozenset]:
    r, c = top_left
    tl = (r, c)
    tr = (r, c+1)
    bl = (r+1, c)
    br = (r+1, c+1)
    return [
        normalized_edge(tl, tr),  # top
        normalized_edge(bl, br),  # bottom
        normalized_edge(tl, bl),  # left
        normalized_edge(tr, br),  # right
    ]

def check_and_claim_boxes(edge: frozenset, player_idx: int) -> int:
    """Claim any newly completed boxes adjacent to the placed edge. Return number claimed."""
    claimed = 0
    for box in boxes_adjacent_to_edge(edge):
        if box in claimed_boxes:
            continue
        needed = box_edges(box)
        if all(e in edges for e in needed):
            claimed_boxes[box] = player_idx
            scores[player_idx] += 1
            claimed += 1
    return claimed

def is_game_over() -> bool:
    return len(claimed_boxes) >= (ROWS - 1) * (COLS - 1)

def reset_game():
    global edges, edge_owner, claimed_boxes, scores, current_player_idx, selected_dot
    edges = set()
    edge_owner = {}
    claimed_boxes = {}
    scores = [0] * len(PLAYERS)
    current_player_idx = 0
    selected_dot = None

# ----------------------------- PYGAME & UI ----------------------------- #
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dots & Boxes - Improved UI")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)
BIG = pygame.font.SysFont("Arial", 36, bold=True)
SMALL = pygame.font.SysFont("Arial", 14)

def player_color(idx: int) -> Tuple[int,int,int]:
    palette = [
        (66, 135, 245),   # blue
        (235, 77, 75),    # red
        (72, 187, 120),   # green
        (245, 190, 66),   # yellow
        (144, 72, 199),   # purple
        (255, 129, 0),    # orange
        (41, 156, 165),   # teal
    ]
    return palette[idx % len(palette)]

def draw_ui():
    # Header bar
    header_rect = pygame.Rect(0, 0, WIDTH - SIDEBAR_WIDTH, GRID_PADDING_TOP)
    pygame.draw.rect(screen, UI_BG, header_rect)
    title = BIG.render("Dots & Boxes", True, TEXT_COLOR)
    screen.blit(title, (MARGIN, 18))
    subtitle = FONT.render("Multi-player • Click a dot, then an adjacent dot", True, TEXT_COLOR)
    screen.blit(subtitle, (MARGIN, 18 + 44))

    # Sidebar
    sidebar_x = MARGIN + GRID_WIDTH + 20
    sidebar_rect = pygame.Rect(sidebar_x - 12, GRID_PADDING_TOP - 12, SIDEBAR_WIDTH, GRID_HEIGHT + 24)
    pygame.draw.rect(screen, UI_BG, sidebar_rect, border_radius=6)

    # Scores and players
    y = GRID_PADDING_TOP + 8
    label = FONT.render("Players", True, TEXT_COLOR)
    screen.blit(label, (sidebar_x, y))
    y += 34
    for i, initial in enumerate(PLAYERS):
        col = player_color(i)
        # colored box
        pygame.draw.rect(screen, col, (sidebar_x, y+2, 36, 24), border_radius=4)
        # initial and score
        text = FONT.render(f"{initial}  —  {scores[i]}", True, TEXT_COLOR)
        screen.blit(text, (sidebar_x + 46, y))
        if i == current_player_idx:
            turn_txt = SMALL.render("Your turn", True, TEXT_COLOR)
            screen.blit(turn_txt, (sidebar_x + 46, y + 22))
        y += 46

    # Instructions
    y += 6
    inst_title = FONT.render("Controls", True, TEXT_COLOR)
    screen.blit(inst_title, (sidebar_x, y))
    y += 26
    insts = [
        "Click one dot then an adjacent dot to draw a line.",
        "No diagonal lines allowed.",
        "Completing a box assigns it to you and gives an extra turn.",
        "Press R to restart."
    ]
    for line in insts:
        txt = SMALL.render(line, True, TEXT_COLOR)
        screen.blit(txt, (sidebar_x, y))
        y += 20

def draw_grid(mouse_pos=None):
    # Grid area background
    grid_rect = pygame.Rect(MARGIN - 8, GRID_PADDING_TOP - 8, GRID_WIDTH + 16, GRID_HEIGHT + 16)
    pygame.draw.rect(screen, (250,250,250), grid_rect)

    # Draw filled claimed boxes (light tint)
    for (r, c), pidx in claimed_boxes.items():
        x_tl, y_tl = dot_to_pixel((r, c))
        cell_rect = pygame.Rect(x_tl + 10, y_tl + 10, CELL_SIZE - 20, CELL_SIZE - 20)
        s = pygame.Surface((cell_rect.w, cell_rect.h), pygame.SRCALPHA)
        col = player_color(pidx)
        s.fill((*col, 55))  # alpha for subtle fill
        screen.blit(s, cell_rect.topleft)
        # draw initial centered
        txt = BIG.render(PLAYERS[pidx], True, (30,30,30))
        txt_rect = txt.get_rect(center=cell_rect.center)
        screen.blit(txt, txt_rect)

    # Draw edges (player-colored)
    for e in edges:
        pts = list(e)
        p1 = dot_to_pixel(pts[0])
        p2 = dot_to_pixel(pts[1])
        owner = edge_owner.get(e, None)
        color = player_color(owner) if owner is not None else DOT_COLOR
        pygame.draw.line(screen, color, p1, p2, LINE_WIDTH)
        # small rounded caps by drawing circles on endpoints (makes lines look nicer)
        pygame.draw.circle(screen, color, p1, LINE_WIDTH//2)
        pygame.draw.circle(screen, color, p2, LINE_WIDTH//2)

    # Draw dots on top
    for r in range(ROWS):
        for c in range(COLS):
            x, y = dot_to_pixel((r, c))
            pygame.draw.circle(screen, DOT_COLOR, (x, y), DOT_RADIUS)

    # Draw selected dot highlight
    if selected_dot is not None:
        sx, sy = dot_to_pixel(selected_dot)
        pygame.draw.circle(screen, (200, 30, 30), (sx, sy), DOT_RADIUS + 4, 2)

    # Draw preview line if selected and mouse hovering an adjacent dot
    if selected_dot is not None and mouse_pos is not None:
        hovered = nearest_dot_from_pos(mouse_pos)
        if hovered is not None and hovered != selected_dot and are_adjacent(selected_dot, hovered):
            # draw preview in current player's color
            p1 = dot_to_pixel(selected_dot)
            p2 = dot_to_pixel(hovered)
            color = player_color(current_player_idx)
            # dashed/transparent preview: draw thinner semi-transparent line
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(s, (*color, 180), p1, p2, max(3, LINE_WIDTH//2))
            screen.blit(s, (0,0))

def nearest_dot_from_pos(pos: Tuple[int,int]) -> Tuple[int,int] or None:
    mx, my = pos
    tolerance = CELL_SIZE // 4
    for r in range(ROWS):
        for c in range(COLS):
            x, y = dot_to_pixel((r, c))
            if (mx - x) ** 2 + (my - y) ** 2 <= tolerance ** 2:
                return (r, c)
    return None

def draw_game_over():
    # Small centered modal within grid area (not covering sidebar)
    modal_w = min(520, GRID_WIDTH - 20)
    modal_h = 120
    center_x = MARGIN + GRID_WIDTH // 2
    center_y = GRID_PADDING_TOP + GRID_HEIGHT // 2
    modal_rect = pygame.Rect(center_x - modal_w // 2, center_y - modal_h // 2, modal_w, modal_h)

    # translucent surround over grid only
    s = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
    s.fill((245, 245, 245, 240))
    screen.blit(s, modal_rect.topleft)
    pygame.draw.rect(screen, (200,200,200), modal_rect, width=2, border_radius=6)

    # compute winners
    max_score = max(scores)
    winners = [PLAYERS[i] for i, sc in enumerate(scores) if sc == max_score]
    if len(winners) == 1:
        msg = f"Winner: {winners[0]}  —  Score: {max_score}"
    else:
        msg = f"Draw: {', '.join(winners)}  —  Score: {max_score}"

    txt = BIG.render(msg, True, TEXT_COLOR)
    txt_rect = txt.get_rect(center=(modal_rect.centerx, modal_rect.centery - 14))
    screen.blit(txt, txt_rect)

    info = SMALL.render("Press R to restart.", True, TEXT_COLOR)
    info_rect = info.get_rect(center=(modal_rect.centerx, modal_rect.centery + 30))
    screen.blit(info, info_rect)

# ---------------------------- MAIN LOOP -------------------------------- #
def main():
    global selected_dot, current_player_idx

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                # optional: add undo / other keys here

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                clicked = nearest_dot_from_pos(pos)
                if clicked is not None:
                    if selected_dot is None:
                        selected_dot = clicked
                    else:
                        if clicked == selected_dot:
                            selected_dot = None
                        elif are_adjacent(selected_dot, clicked):
                            edge = normalized_edge(selected_dot, clicked)
                            if edge not in edges:
                                # place edge
                                edges.add(edge)
                                edge_owner[edge] = current_player_idx
                                # check completed boxes
                                claimed = check_and_claim_boxes(edge, current_player_idx)
                                if claimed == 0:
                                    current_player_idx = (current_player_idx + 1) % len(PLAYERS)
                            # reset selection after move
                            selected_dot = None
                        else:
                            # clicked a new dot -> select it
                            selected_dot = clicked

        # Drawing
        screen.fill(BG_COLOR)
        draw_ui()
        draw_grid(mouse_pos)

        if is_game_over():
            draw_game_over()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
