"""
Dots & Boxes (multi-player) - Boilerplate
Author: ChatGPT
Requirements:
 - Python 3.8+
 - pygame

How it works (short):
 - Grid of (rows x cols) dots. Cells/boxes are the spaces between 4 dots.
 - Players take turns drawing orthogonal edges between adjacent dots.
 - When a player draws the final edge of a box, that box is claimed and filled with that player's initial.
 - Score = number of boxes claimed by each player.
 - If a player completes >=1 box on their move they get another turn.
"""

import pygame
import sys
from typing import Tuple, List, Dict, Set

# ----------------------------- CONFIG -------------------------------- #
ROWS = 4            # number of dot rows (m)
COLS = 6            # number of dot cols (n)
DOT_RADIUS = 6
CELL_SIZE = 80      # pixels between adjacent dots (size of cell)
MARGIN = 60         # margin around the grid
LINE_WIDTH = 6      # width of drawn edges
BG_COLOR = (245, 245, 245)
DOT_COLOR = (30, 30, 30)
GRID_LINE_COLOR = (200, 200, 200)  # faint guides (optional)
TEXT_COLOR = (10, 10, 10)
FPS = 60

# Players configuration:
# Provide a list of player initials (strings, single char preferable).
PLAYERS = ["A", "B", "C"]  # example: three players. Change to 2+ initials as needed.

# Window size computed from grid + margin
WIDTH = MARGIN * 2 + (COLS - 1) * CELL_SIZE
HEIGHT = MARGIN * 2 + (ROWS - 1) * CELL_SIZE + 100  # extra space for UI at top/bottom

# ----------------------------- GAME STATE ----------------------------- #
# Represent dots as (r, c) with r in [0..ROWS-1], c in [0..COLS-1]
# Edges stored as frozenset of two dot tuples: frozenset({(r1,c1),(r2,c2)})
# Claimed boxes stored as dict mapping box (r,c) to player_idx who claimed it
# Box coordinates represent the top-left dot of the cell; valid box rows = 0..ROWS-2, cols=0..COLS-2

# Initialize structures
edges: Set[frozenset] = set()
claimed_boxes: Dict[Tuple[int,int], int] = {}
scores: List[int] = [0] * len(PLAYERS)
current_player_idx = 0
selected_dot: Tuple[int,int] or None = None

# ----------------------------- HELPERS -------------------------------- #
def dot_to_pixel(dot: Tuple[int,int]) -> Tuple[int,int]:
    """Convert grid dot (r,c) to screen pixel coordinates (x,y)."""
    r, c = dot
    x = MARGIN + c * CELL_SIZE
    y = MARGIN + r * CELL_SIZE + 80  # shift grid down to leave room for UI at top
    return x, y

def are_adjacent(d1: Tuple[int,int], d2: Tuple[int,int]) -> bool:
    """Return True if d1 and d2 are orthogonally adjacent (no diagonal)."""
    dr = abs(d1[0] - d2[0])
    dc = abs(d1[1] - d2[1])
    return (dr == 1 and dc == 0) or (dr == 0 and dc == 1)

def normalized_edge(d1: Tuple[int,int], d2: Tuple[int,int]) -> frozenset:
    """Return an immutable normalized representation of an edge between two dots."""
    return frozenset([d1, d2])

def boxes_adjacent_to_edge(edge: frozenset) -> List[Tuple[int,int]]:
    """Return up to two box positions (top-left coords) adjacent to a given edge."""
    # Convert frozenset to two endpoints
    pts = list(edge)
    (r1, c1), (r2, c2) = pts[0], pts[1]
    boxes = []
    if r1 == r2:  # horizontal edge, boxes above and below
        r = r1
        c_left = min(c1, c2)
        # box above uses top-left at (r-1, c_left)
        if r - 1 >= 0 and r - 1 <= ROWS - 2:
            boxes.append((r - 1, c_left))
        # box below uses top-left at (r, c_left)
        if r >= 0 and r <= ROWS - 2:
            boxes.append((r, c_left))
    elif c1 == c2:  # vertical edge, boxes left and right
        c = c1
        r_top = min(r1, r2)
        # box to left uses top-left at (r_top, c-1)
        if c - 1 >= 0 and c - 1 <= COLS - 2:
            boxes.append((r_top, c - 1))
        # box to right uses top-left at (r_top, c)
        if c >= 0 and c <= COLS - 2:
            boxes.append((r_top, c))
    return boxes

def box_edges(top_left: Tuple[int,int]) -> List[frozenset]:
    """Return the 4 edges (as frozenset pairs) that surround a box whose top-left dot is given."""
    r, c = top_left
    # corners: (r,c), (r,c+1), (r+1,c), (r+1,c+1)
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
    """
    Check boxes adjacent to the newly placed edge.
    If a box has all 4 edges and is unclaimed, claim it for player_idx.
    Return number of boxes claimed this move.
    """
    claimed = 0
    for box in boxes_adjacent_to_edge(edge):
        if box in claimed_boxes:
            continue  # already claimed
        needed = box_edges(box)
        if all(e in edges for e in needed):
            claimed_boxes[box] = player_idx
            scores[player_idx] += 1
            claimed += 1
    return claimed

# ----------------------------- PYGAME UI -------------------------------- #
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dots & Boxes - Multi Player")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont(None, 28)
BIG_FONT = pygame.font.SysFont(None, 40)

def draw_grid():
    # optional faint grid lines (helpful visually). Comment out to hide
    for r in range(ROWS):
        for c in range(COLS):
            x, y = dot_to_pixel((r, c))
            # draw dot
            pygame.draw.circle(screen, DOT_COLOR, (x, y), DOT_RADIUS)
    # Draw existing edges
    for e in edges:
        pts = list(e)
        p1 = dot_to_pixel(pts[0])
        p2 = dot_to_pixel(pts[1])
        # color by player who drew it (we store no owner for edges; we can infer by searching which move created it
        # For simplicity we color edges black. If you want colored edges per player, you'd store edge -> owner mapping.
        pygame.draw.line(screen, DOT_COLOR, p1, p2, LINE_WIDTH)

    # Draw claimed boxes (show player's initial centered in the cell)
    for (r, c), pidx in claimed_boxes.items():
        # compute center of cell
        x_tl, y_tl = dot_to_pixel((r, c))
        x_br, y_br = dot_to_pixel((r+1, c+1))
        center_x = (x_tl + x_br) // 2
        center_y = (y_tl + y_br) // 2
        # Draw a faint rectangle background to make the initial visible
        rect_w = CELL_SIZE - 10
        rect_h = CELL_SIZE - 10
        rect = pygame.Rect(center_x - rect_w//2, center_y - rect_h//2, rect_w, rect_h)
        # fill lightly with a translucent color for the player (derive color from index)
        col = player_color(pidx)
        s = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        s.fill((*col, 60))  # 60 alpha
        screen.blit(s, (rect.x, rect.y))
        # Draw initial
        txt = BIG_FONT.render(PLAYERS[pidx], True, TEXT_COLOR)
        txt_rect = txt.get_rect(center=(center_x, center_y))
        screen.blit(txt, txt_rect)

    # If the player selected a dot, highlight it
    if selected_dot is not None:
        x, y = dot_to_pixel(selected_dot)
        pygame.draw.circle(screen, (255, 0, 0), (x, y), DOT_RADIUS + 3, 2)

def player_color(idx: int) -> Tuple[int,int,int]:
    """Return a distinct color for a player index (deterministic)."""
    # simple color palette - extend or randomize if many players
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

def draw_sidebar():
    # top UI: current player, scores
    header = FONT.render("Dots & Boxes", True, TEXT_COLOR)
    screen.blit(header, (10, 10))

    # show players and scores
    x = 10
    y = 40
    for i, initial in enumerate(PLAYERS):
        # highlight current player
        is_current = (i == current_player_idx)
        label = f"{initial} : {scores[i]}"
        txt = FONT.render(label, True, TEXT_COLOR)
        screen.blit(txt, (x, y))
        # small colored square
        pygame.draw.rect(screen, player_color(i), (x + 80, y + 4, 18, 18))
        if is_current:
            cur_txt = FONT.render("<-- turn", True, TEXT_COLOR)
            screen.blit(cur_txt, (x + 110, y))
        y += 28

    # instructions
    inst = [
        "Click one dot then an adjacent dot to draw a line.",
        "No diagonal lines allowed.",
        "Completing a box assigns it to you (initial shown) and gives you another turn."
    ]
    y += 6
    for line in inst:
        txt = FONT.render(line, True, TEXT_COLOR)
        screen.blit(txt, (10, y))
        y += 22

def nearest_dot_from_pos(pos: Tuple[int,int]) -> Tuple[int,int] or None:
    """Return the (r,c) of the nearest dot to the mouse pos, if within a tolerance."""
    mx, my = pos
    # convert screen y back to grid coords
    # grid top-left y is MARGIN + 80
    grid_top = MARGIN + 80
    # compute approximate
    for r in range(ROWS):
        for c in range(COLS):
            x, y = dot_to_pixel((r, c))
            dx = mx - x
            dy = my - y
            if dx*dx + dy*dy <= (CELL_SIZE//4)**2:  # tolerance radius (quarter cell)
                return (r, c)
    return None

def is_game_over() -> bool:
    """Game ends when all possible boxes are claimed."""
    total_boxes = (ROWS - 1) * (COLS - 1)
    return len(claimed_boxes) >= total_boxes

# ----------------------------- MAIN LOOP ------------------------------- #
def main():
    global selected_dot, current_player_idx

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                clicked = nearest_dot_from_pos(pos)
                if clicked is not None:
                    # If no dot selected yet, set selection
                    if selected_dot is None:
                        selected_dot = clicked
                    else:
                        # if same dot clicked -> deselect
                        if clicked == selected_dot:
                            selected_dot = None
                        elif are_adjacent(selected_dot, clicked):
                            edge = normalized_edge(selected_dot, clicked)
                            if edge not in edges:
                                # Place edge
                                edges.add(edge)
                                # Check boxes completed
                                claimed = check_and_claim_boxes(edge, current_player_idx)
                                # If no box claimed, pass turn
                                if claimed == 0:
                                    current_player_idx = (current_player_idx + 1) % len(PLAYERS)
                                # else same player goes again
                            # reset selection for next move
                            selected_dot = None
                        else:
                            # If not adjacent, treat clicked dot as new selection
                            selected_dot = clicked

        # Drawing
        screen.fill(BG_COLOR)
        draw_sidebar()
        draw_grid()

        # If game over, show message
        if is_game_over():
            # determine winner(s)
            max_score = max(scores)
            winners = [PLAYERS[i] for i, s in enumerate(scores) if s == max_score]
            if len(winners) == 1:
                msg = f"Winner: {winners[0]} (score {max_score})"
            else:
                msg = f"Draw between {', '.join(winners)} (score {max_score})"
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((200, 200, 200, 120))
            screen.blit(overlay, (0,0))
            text = BIG_FONT.render(msg, True, (0,0,0))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
