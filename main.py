from game.board import (create_board, drop_piece, is_valid_location,
                         get_next_open_row, print_board, check_win, is_draw)

def main():
    board = create_board()
    current_piece = 1  # 1 = Spieler, 2 = KI (später)

    print("=== Vier Gewinnt ===")
    print_board(board)

    while True:
        try:
            col = int(input(f"\nSpieler {current_piece} – Spalte wählen (1-7): ")) - 1
        except ValueError:
            print("Bitte eine Zahl eingeben.")
            continue

        if col < 0 or col >= 7:
            print("Ungültige Spalte.")
            continue

        if not is_valid_location(board, col):
            print("Spalte voll – andere wählen.")
            continue

        row = get_next_open_row(board, col)
        drop_piece(board, row, col, current_piece)
        print_board(board)

        if check_win(board, current_piece):
            print(f"\n pieler {current_piece} gewinnt!")
            break

        if is_draw(board):
            print("\nUnentschieden!")
            break

        current_piece = 2 if current_piece == 1 else 1

if __name__ == "__main__":
    main()