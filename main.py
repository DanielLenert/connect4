from game.board import (create_board, drop_piece, is_valid_location,
                         get_next_open_row, print_board, check_win, is_draw)
from game.ai import get_ai_move

def main():
    board = create_board()
    print("=== Vier Gewinnt – Mensch vs. KI ===")
    print_board(board)

    while True:
       # Spieler
        while True:
            try:
                col = int(input("\nDeine Spalte (1-7): ")) - 1
                if 0 <= col < 7 and is_valid_location(board, col):
                    break
                print("Ungültige Spalte – nochmal.")
            except ValueError:
                print("Bitte eine Zahl eingeben.")

        row = get_next_open_row(board, col)
        drop_piece(board, row, col, 1)
        print_board(board)

        if check_win(board, 1):
            print("\n Du gewinnst!")
            break
        if is_draw(board):
            print("\nUnentschieden!")
            break

        # KI
        print("\nKI denkt...")
        col = get_ai_move(board, depth=5)
        row = get_next_open_row(board, col)
        drop_piece(board, row, col, 2)
        print(f"KI spielt Spalte {col + 1}")
        print_board(board)

        if check_win(board, 2):
            print("\nKI gewinnt!")
            break
        if is_draw(board):
            print("\nUnentschieden!")
            break

if __name__ == "__main__":
    main()