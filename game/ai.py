from game.board import is_valid_location, get_next_open_row, drop_piece, check_win, is_draw, ROWS, COLS

PLAYER = 1
AI = 2
EMPTY = 0

def score_window(window, piece):
    opponent = PLAYER if piece == AI else AI
    score = 0

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    if window.count(opponent) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score

def score_board(board, piece):
    score = 0

    # Mittelspalte bevorzugen
    center_col = [board[r][COLS // 2] for r in range(ROWS)]
    score += center_col.count(piece) * 3

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            window = [board[r][c + i] for i in range(4)]
            score += score_window(window, piece)

    # Vertikal
    for c in range(COLS):
        for r in range(ROWS - 3):
            window = [board[r + i][c] for i in range(4)]
            score += score_window(window, piece)

    # Diagonal (↘)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r + i][c + i] for i in range(4)]
            score += score_window(window, piece)

    # Diagonal (↙)
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            window = [board[r + i][c - i] for i in range(4)]
            score += score_window(window, piece)

    return score

def minimax(board, depth, alpha, beta, maximizing):
    valid_cols = [c for c in range(COLS) if is_valid_location(board, c)]

    if check_win(board, AI):
        return (None, 100000)
    if check_win(board, PLAYER):
        return (None, -100000)
    if is_draw(board) or depth == 0:
        return (None, score_board(board, AI))

    if maximizing:
        best = (None, float('-inf'))
        for col in valid_cols:
            row = get_next_open_row(board, col)
            # Kopie des Boards simulieren
            board[row][col] = AI
            _, score = minimax(board, depth - 1, alpha, beta, False)
            board[row][col] = EMPTY  # Zug rueckgaengig
            if score > best[1]:
                best = (col, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best

    else:
        best = (None, float('inf'))
        for col in valid_cols:
            row = get_next_open_row(board, col)
            board[row][col] = PLAYER
            _, score = minimax(board, depth - 1, alpha, beta, True)
            board[row][col] = EMPTY
            if score < best[1]:
                best = (col, score)
            beta = min(beta, score)
            if alpha >= beta:
                break
        return best

def get_ai_move(board, depth=5):
    col, _ = minimax(board, depth, float('-inf'), float('inf'), True)
    return col