"""Connect Four as a game in the form of AIMA Section 5.1.

The textbook defines a game by:
    S0 (initial state), TO-MOVE(s), ACTIONS(s), RESULT(s, a),
    IS-TERMINAL(s) and UTILITY(s, p).
`ConnectFour` implements exactly those six parts. The board is 6 rows by
7 columns. Player 1 ('X') moves first, player 2 ('O') second. An action is
a column number 0..6; the piece drops to the lowest empty row.
"""

ROWS, COLS = 6, 7
EMPTY, P1, P2 = 0, 1, 2
DRAW = 3  # value stored in State.winner when the board fills with no winner
SYMBOLS = {EMPTY: ".", P1: "X", P2: "O"}


def other(player):
    return P2 if player == P1 else P1


def _index(col, row):
    """Cell index in the flat board list. Row 0 is the bottom row."""
    return col * ROWS + row


# All 69 lines of four cells (horizontal, vertical and both diagonals).
# Used by the objective (rule based) evaluation.
WINDOWS = []
for _c in range(COLS):
    for _r in range(ROWS):
        for _dc, _dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
            cells = [(_c + k * _dc, _r + k * _dr) for k in range(4)]
            if all(0 <= x < COLS and 0 <= y < ROWS for x, y in cells):
                WINDOWS.append(tuple(_index(x, y) for x, y in cells))
assert len(WINDOWS) == 69


class State:
    """A Connect Four position. `play` changes it in place; RESULT copies first."""

    __slots__ = ("board", "heights", "to_move", "winner", "moves")

    def __init__(self, board=None, heights=None, to_move=P1, winner=None, moves=0):
        self.board = board if board is not None else [EMPTY] * (ROWS * COLS)
        self.heights = heights if heights is not None else [0] * COLS
        self.to_move = to_move
        self.winner = winner  # None while the game is running, P1, P2 or DRAW
        self.moves = moves

    def copy(self):
        return State(self.board[:], self.heights[:], self.to_move, self.winner, self.moves)

    def legal_columns(self):
        return [c for c in range(COLS) if self.heights[c] < ROWS]

    def play(self, col):
        """Drop a piece for the player to move into `col` (in place)."""
        if self.winner is not None:
            raise ValueError("game is already over")
        row = self.heights[col]
        if row >= ROWS:
            raise ValueError(f"column {col} is full")
        player = self.to_move
        self.board[_index(col, row)] = player
        self.heights[col] = row + 1
        self.moves += 1
        if self._wins_at(col, row, player):
            self.winner = player
        elif self.moves == ROWS * COLS:
            self.winner = DRAW
        self.to_move = other(player)

    def _wins_at(self, col, row, player):
        """Only lines through the last piece can be new wins."""
        b = self.board
        for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                c, r = col + sign * dc, row + sign * dr
                while 0 <= c < COLS and 0 <= r < ROWS and b[_index(c, r)] == player:
                    count += 1
                    c += sign * dc
                    r += sign * dr
            if count >= 4:
                return True
        return False

    def key(self):
        return (tuple(self.board), self.to_move)

    def __eq__(self, other_state):
        return isinstance(other_state, State) and self.key() == other_state.key()

    def __hash__(self):
        return hash(self.key())

    def __str__(self):
        lines = []
        for r in range(ROWS - 1, -1, -1):
            lines.append(" ".join(SYMBOLS[self.board[_index(c, r)]] for c in range(COLS)))
        lines.append(" ".join(str(c) for c in range(COLS)))
        return "\n".join(lines)


def from_moves(moves):
    """Build a position by playing a sequence of columns from the empty board."""
    s = State()
    for col in moves:
        s.play(int(col))
    return s


class ConnectFour:
    """The game, with the six components from AIMA Section 5.1."""

    rows, cols = ROWS, COLS

    def __init__(self):
        self.initial = State()  # S0

    def to_move(self, state):  # TO-MOVE(s)
        return state.to_move

    def actions(self, state):  # ACTIONS(s)
        return [] if state.winner is not None else state.legal_columns()

    def result(self, state, action):  # RESULT(s, a)
        s = state.copy()
        s.play(action)
        return s

    def is_terminal(self, state):  # IS-TERMINAL(s)
        return state.winner is not None

    def utility(self, state, player):  # UTILITY(s, p): +1 win, -1 loss, 0 draw
        if state.winner == player:
            return 1
        if state.winner in (None, DRAW):
            return 0
        return -1

    # ---- Objective part of the selection utility (from the rules of the game) ----
    @staticmethod
    def evaluate(state, player):
        """Rule based score of `state` for `player`.

        Every line of four that contains only one player's pieces is still a
        possible win for that player. Lines with 3 pieces and 1 empty cell
        score 5, lines with 2 pieces score 2, and pieces in the centre column
        score 3 each (the centre column belongs to the most lines).
        The opponent's lines count against the player.
        A won game scores +1000 (or -1000 if lost).
        """
        if state.winner == player:
            return 1000
        if state.winner == other(player):
            return -1000
        if state.winner == DRAW:
            return 0
        b = state.board
        opp = other(player)
        score = 0
        for w in WINDOWS:
            mine = theirs = 0
            for i in w:
                v = b[i]
                if v == player:
                    mine += 1
                elif v == opp:
                    theirs += 1
            if theirs == 0:
                if mine == 3:
                    score += 5
                elif mine == 2:
                    score += 2
            elif mine == 0:
                if theirs == 3:
                    score -= 5
                elif theirs == 2:
                    score -= 2
        centre = 3
        for r in range(ROWS):
            v = b[_index(centre, r)]
            if v == player:
                score += 3
            elif v == opp:
                score -= 3
        return score
