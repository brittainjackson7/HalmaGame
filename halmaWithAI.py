import tkinter as tk
import sys
import time
import threading

class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position
    def get_position(self):
        return self.position
    def get_color(self):
        return self.color

class HalmaBoard(tk.Canvas):
    # initialize the board
    def __init__(self, parent, board_size, size = 640, player_type = 1):
        tk.Canvas.__init__(self, parent, width=size, height=size, background='white')
        self.pack()
        self.rows = board_size
        self.columns = board_size
        self.cell_size = size // self.columns
        self.pieces = [] # list to keep track of pieces
        self.green_start_positions = []
        self.red_start_positions = []
        self.ai_depth = 3
        self.initialize_pieces()
        self.draw_board()
        self.draw_pieces()
        self.move_count = 0
        self.which_player = 'green'
        self.ai_player = 'red' if player_type == 1 else None
        self.selected = None
        self.win = None
        self.start_time = time.time()
        self.elapsed_time_red = 0
        self.elapsed_time_green = 0
        self.side_bar = tk.Canvas(parent, width=200, height=size, background='white')
        self.side_bar.pack(side=tk.RIGHT)
        self.update_sidebar()
        # bind clicks to a method
        self.bind("<Button-3>", self.select)
        self.bind("<Button-1>", self.move)
    def select(self, event):
        x, y = event.x, event.y
        row, col = y // self.cell_size, x // self.cell_size
        # Deselect the currently selected piece if clicked again
        if self.selected is not None and self.selected.get_position() == (row, col):
            self.selected = None
            self.remove_arrows()
            return
        for piece in self.pieces:
            r, c = piece.get_position()
            if r == row and c == col:
                self.selected = piece
                self.remove_arrows()
                self.show_next_moves()
                return
    def move(self, event):
        if self.selected is not None and self.selected.get_color() == self.which_player:
            # get the x, y coordinates of the click
            x, y = event.x, event.y
            # convert x, y to row, column
            row, col = y // self.cell_size, x // self.cell_size
            # check if the clicked position is a legal move
            legal_moves = self.get_legal_moves(self.selected)
            if (row, col) in legal_moves:
                # move the selected piece
                self.selected.position = (row, col)
                self.selected = None
                # redraw the board and pieces
                self.delete('all')
                self.draw_board()
                self.draw_pieces()
                if(self.check_for_win()):
                    self.display_winner()
                    threading.Timer(10,self.reset_board).start()
                self.update_turn()
    def ai_move(self):
        depth = self.ai_depth  # Adjust the depth for the desired difficulty level
        best_move = self.minimax(self.ai_player, depth, float('-inf'), float('inf'))
        selected_piece, move = best_move
        # Move the selected piece
        piece, new_position = selected_piece
        piece.position = new_position
        # Redraw the board and pieces
        self.delete('all')
        self.draw_board()
        self.draw_pieces()
        if self.check_for_win():
            self.display_winner()
            threading.Timer(10, self.reset_board).start()
        self.update_turn()
    def heuristic(self, player):
        player_pieces = [piece for piece in self.pieces if piece.get_color() == player]
        opponent_pieces = [piece for piece in self.pieces if piece.get_color() != player]
        if player == 'green':
            target_positions = self.red_start_positions
            opposite_corner = (self.rows - 1, self.columns - 1)
        else:
            target_positions = self.green_start_positions
            opposite_corner = (0, 0)
        # Calculate the average Euclidean distance between each piece and its target cell
        player_distance = sum(min(sum((piece.get_position()[i] - target[i]) ** 2 for i in range(2)) for target in target_positions) for piece in player_pieces) / len(player_pieces)
        opponent_distance = sum(min(sum((piece.get_position()[i] - target[i]) ** 2 for i in range(2)) for target in target_positions) for piece in opponent_pieces) / len(opponent_pieces)
        # Add a bonus for each piece that has reached the opposite corner
        player_bonus = sum(piece.get_position() == opposite_corner for piece in player_pieces)
        opponent_bonus = sum(piece.get_position() == opposite_corner for piece in opponent_pieces)
        # Check if a winning piece is blocking another piece from getting in
        blocking_penalty = 0
        for piece in player_pieces:
            if piece.get_position() in target_positions:
                for target in target_positions:
                    if target not in [p.get_position() for p in player_pieces]:
                        blocking_penalty += 1
                        break
        score = (opponent_distance - player_distance) + (player_bonus - opponent_bonus) * 50 - blocking_penalty
        print(f"AI tested move score for {piece.position}:{score}")
        return score
    def evaluate_moves(self, player):
        player_pieces = [piece for piece in self.pieces if piece.get_color() == player]
        moves = []
        for piece in player_pieces:
            legal_moves = self.get_legal_moves(piece)
            for move in legal_moves:
                moves.append((piece, move))
        return moves
    def minimax(self, player, depth, alpha, beta):
        if depth == 0 or self.check_for_win():
            return None, self.heuristic(player)
        moves = []
        player_pieces = [piece for piece in self.pieces if piece.get_color() == player]
        for piece in player_pieces:
            legal_moves = self.get_legal_moves(piece)
            for move in legal_moves:
                moves.append((piece, move))
        if not moves:  # If there are no legal moves, end the search
            return None, self.heuristic(player)
        if player == self.ai_player:
            best_move = None
            max_eval = float('-inf')
            for move in moves:
                piece, new_position = move
                old_position = piece.get_position()
                piece.position = new_position
                _, eval = self.minimax(self.which_player, depth - 1, alpha, beta)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                piece.position = old_position
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return best_move, max_eval
        else:
            best_move = None
            min_eval = float('inf')
            for move in moves:
                piece, new_position = move
                old_position = piece.get_position()
                piece.position = new_position
                _, eval = self.minimax(self.ai_player, depth - 1, alpha, beta)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                piece.position = old_position
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return best_move, min_eval          
    def reset_board(self):
        self.move_count = 0
        self.delete('winner')
        self.pieces = []
        self.initialize_pieces()
        self.draw_board()
        self.draw_pieces()
        self.start_time = time.time()
        self.update_sidebar()
    def display_winner(self):
        winner_text = f"Winner: {self.winner.capitalize()}"
        self.create_text(self.cell_size * self.columns // 2, self.cell_size * self.rows // 2, text=winner_text, font=("Arial", 24), fill='blue', tag='winner')
    def get_legal_moves(self, piece):
        legal_moves = []
        stack = [(piece.position, False, None)]
        visited = set()
        while stack:
            current_pos, jumped, prev_position = stack.pop()
            if current_pos in visited:
                continue
            visited.add(current_pos)
            row, col = current_pos
            directions = [(row-1, col), (row+1, col), (row, col-1), (row, col+1),
                        (row-1, col-1), (row-1, col+1), (row+1, col-1), (row+1, col+1)]
            for r, c in directions:
                if r < 0 or r >= self.rows or c < 0 or c >= self.columns:
                    continue
                if (r, c) in [p.get_position() for p in self.pieces]:
                    r_diff = r - row
                    c_diff = c - col
                    new_r, new_c = r + r_diff, c + c_diff
                    if new_r < 0 or new_r >= self.rows or new_c < 0 or new_c >= self.columns:
                        continue
                    if (new_r, new_c) not in [p.get_position() for p in self.pieces] and (new_r, new_c) != prev_position:
                        stack.append(((new_r, new_c), True, (row, col)))
                        legal_moves.append((new_r, new_c))
                elif not jumped:
                    legal_moves.append((r, c))
        return legal_moves
    def show_next_moves(self):
        if self.selected is not None:
            self.remove_arrows()  # Remove existing arrows before drawing new ones
            legal_moves = self.get_legal_moves(self.selected)
            print(legal_moves)
            for move in legal_moves:
                # get the coordinates of the starting and ending squares
                start_x, start_y = self.selected.position
                end_x, end_y = move
                # calculate the center coordinates of the starting and ending squares
                start_center_x = (start_y * self.cell_size) + (self.cell_size // 2)
                start_center_y = (start_x * self.cell_size) + (self.cell_size // 2)
                end_center_x = (end_y * self.cell_size) + (self.cell_size // 2)
                end_center_y = (end_x * self.cell_size) + (self.cell_size // 2)
                # calculate the direction of the arrow
                dx = end_center_x - start_center_x
                dy = end_center_y - start_center_y
                length = (dx ** 2 + dy ** 2) ** 0.5
                dx /= length
                dy /= length
                # calculate the position of the arrowhead
                arrowhead_x = end_center_x - 10 * dx
                arrowhead_y = end_center_y - 10 * dy
                # draw the arrow
                self.create_line(start_center_x, start_center_y, arrowhead_x, arrowhead_y, arrow=tk.LAST, arrowshape=(16,20,6), fill='blue')
    def remove_arrows(self):
        self.delete('arrow')
    def draw_pieces(self):
        for piece in self.pieces:
            x, y = piece.position
            color = piece.color
            x0 = (y * self.cell_size) + (self.cell_size // 2)
            y0 = (x * self.cell_size) + (self.cell_size // 2)
            self.create_oval(x0 - 20, y0 - 20, x0 + 20, y0 + 20, fill=color)
    # draw the board
    def draw_board(self):
        color1 = '#DDB88C'
        color2 = '#A66D4F'
        for row in range(self.rows):
            for col in range(self.columns):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                if (row + col) % 2 == 0:
                    self.create_rectangle(x1, y1, x2, y2, fill=color1)
                else:
                    self.create_rectangle(x1, y1, x2, y2, fill=color2)
    def initialize_pieces(self):
        corner_size = (self.rows + 1) // 2
        self.green_start_positions = []
        self.red_start_positions = []
        for row in range(self.rows):
            for col in range(self.columns):
                if row < corner_size and col < corner_size:
                    if row + col < corner_size:
                        green_piece = Piece('green', (row, col))
                        self.pieces.append(green_piece)
                        self.green_start_positions.append((row, col))
                if row >= self.rows - corner_size and col >= self.columns - corner_size:
                    if row + col >= self.rows + self.columns - corner_size - 1:
                        red_piece = Piece('red', (row, col))
                        self.pieces.append(red_piece)
                        self.red_start_positions.append((row, col))
    def update_turn(self):
        if self.which_player == 'green':
            self.elapsed_time_green += time.time() - self.start_time
        else:
            self.elapsed_time_red += time.time() - self.start_time
        if self.which_player == 'green':
            self.which_player = 'red'
        else:
            self.which_player = 'green'
        self.start_time = time.time()
        print(f"\n{self.which_player}'s Turn!")
        self.update_sidebar()
        if self.which_player == self.ai_player:
            self.after(1000, self.ai_move)
    def check_for_win(self):
        #if self.move_count < 2:  # Do not check for a win before both players have made at least one move
            #return False
        corner_size = (self.rows + 1) // 2
        green_win_positions = set(self.red_start_positions)
        for row in range(corner_size):
            for col in range(corner_size):
                if row + col < corner_size:
                    green_win_positions.add((self.rows - 1 - row, self.columns - 1 - col))
        red_win_positions = set(self.green_start_positions)
        for row in range(corner_size):
            for col in range(corner_size):
                if row + col < corner_size:
                    red_win_positions.add((row, col))
        green_win = all(any(piece.get_color() == 'green' and piece.get_position() == pos for piece in self.pieces) for pos in green_win_positions)
        red_win = all(any(piece.get_color() == 'red' and piece.get_position() == pos for piece in self.pieces) for pos in red_win_positions)
        if green_win:
            self.winner = 'green'
        elif red_win:
            self.winner = 'red'
        else:
            self.winner = None
        return self.winner is not None
    def update_sidebar(self):
        self.side_bar.delete('all')
        self.side_bar.create_text(100, 30, text="Halma", font=("Arial", 20))
        self.side_bar.create_text(100, 80, text=f"{self.which_player.capitalize()}'s Turn", font=("Arial", 14))
        if self.which_player == 'green':
            self.elapsed_time_green += time.time() - self.start_time
        else:
            self.elapsed_time_red += time.time() - self.start_time
        self.startTime = time.time()
        self.side_bar.create_text(100, 150, text="Time Taken", font=("Arial", 14))
        self.side_bar.create_text(100, 180, text=f"Green: {int(self.elapsed_time_green)} s", font=("Arial", 12))
        self.side_bar.create_text(100, 210, text=f"Red: {int(self.elapsed_time_red)} s", font=("Arial", 12))
class Game():
    def __init__(self, board_size, size, player_type):
        self.size = size
        self.player_type = player_type
        root = tk.Tk()
        board = HalmaBoard(root, board_size, size, player_type)
        root.mainloop()
if len(sys.argv) > 1:
    board_size = int(sys.argv[1])  # convert the input size to an integer
else:
    board_size = 8
Game( board_size, 640, 1)