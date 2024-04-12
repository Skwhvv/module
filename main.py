from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from abc import ABC, abstractmethod
import sqlite3
import uvicorn
import chess

conn = sqlite3.connect('results.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS matches
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   player1 TEXT,
                   player2 TEXT,
                   winner TEXT,
                   timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')


def save_match_result(player1, player2, winner):
    cursor.execute('''INSERT INTO matches (player1, player2, winner) VALUES (?, ?, ?)''', (player1, player2, winner))
    conn.commit()


def close_db_connection():
    conn.close()


app = FastAPI()
game = None


class Piece(ABC):
    def __init__(self, color):
        self.color = color

    @abstractmethod
    def validate_move(self, start, end):
        pass

    @abstractmethod
    def make_move(self, start, end):
        pass


class Pawn(Piece):
    def validate_move(self, start, end):
        if start[0] == end[0] and start[1] == end[1]:
            return False
        return True

    def make_move(self, start, end):
        pass


class Rook(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Knight(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Bishop(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Queen(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class King(Piece):
    def validate_move(self, start, end):
        return True

    def make_move(self, start, end):
        pass


class Board:
    def __init__(self):
        self.board = [
            [Rook("чорний"), Knight("чорний"), Bishop("чорний"), Queen("чорний"), King("чорний"), Bishop("чорний"),
             Knight("чорний"), Rook("чорний")],
            [Pawn("чорний"), Pawn("чорний"), Pawn("чорний"), Pawn("чорний"), Pawn("чорний"), Pawn("чорний"),
             Pawn("чорний"), Pawn("чорний")],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [Pawn("білий"), Pawn("білий"), Pawn("білий"), Pawn("білий"), Pawn("білий"), Pawn("білий"), Pawn("білий"),
             Pawn("білий")],
            [Rook("білий"), Knight("білий"), Bishop("білий"), Queen("білий"), King("білий"), Bishop("білий"),
             Knight("білий"), Rook("білий")]
        ]

        self.coordinates = []
        for row_num in range(8):
            for col_num in range(8):
                col_letter = chr(col_num + ord('a'))
                self.coordinates.append(f"{col_letter}{row_num}")

    def display_board(self):
        for row in self.board:
            print(row)

    def get_piece_at_position(self, position):
        row, col = int(position[1]), ord(position[0]) - ord('a')
        return self.board[row][col]


board = Board()
board.display_board()


class Game:
    def __init__(self):
        self.board = Board()
        self.history = []
        self.current_player = "Гравець1"

    def move(self, player, piece, start, end):
        if not self.validate_move(player, piece, start, end):
            raise HTTPException(status_code=400, detail="Невірний хід")

        start_index = self.board.coordinates.index(start)
        end_index = self.board.coordinates.index(end)

        if self.board.board[end_index // 8][end_index % 8] is not None:
            raise HTTPException(status_code=400, detail="Клітинка вже зайнята")

        piece.make_move(start, end)
        self.history.append((player, piece, start, end))
        self.switch_player()

        if self.check_pawns_eaten():
            self.end_game()

        print(f"Фігура на клітинці {start} переміщена на клітинку {end}")

    def switch_player(self):
        self.current_player = "Гравець2" if self.current_player == "Гравець1" else "Гравець1"

    def validate_move(self, player, piece, start, end):
        end_index = self.board.coordinates.index(end)
        if self.board.board[end_index // 8][end_index % 8] is not None:
            return False
        return piece.validate_move(start, end)

    def check_pawns_eaten(self):
        pawns_color = "білий" if self.current_player == "Гравець1" else "чорний"
        pawns_row = 6 if pawns_color == "білий" else 1
        for piece in self.board.board[pawns_row]:
            if isinstance(piece, Pawn) and piece.color == pawns_color:
                return False
        return True

    def end_game(self):
        winner = "Гравець1" if self.current_player == "Гравець2" else "Гравець2"
        save_match_result("Противник", "Противник", winner)
        raise HTTPException(status_code=200, detail=f"Гравець {winner} переміг!")



@app.post("/Початок гри")
async def start_game(гравець1: str, гравець2: str, номер_гравця_1: str, номер_гравця_2: str):
    global game
    game = Game()
    game.current_player = гравець1

    if номер_гравця_1 == "білий":
        game.board.board[6] = [Pawn("білий") for _ in range(8)]
    else:
        game.board.board[1] = [Pawn("чорний") for _ in range(8)]

    if номер_гравця_2 == "чорний":
        game.board.board[0] = [
            Rook("чорний"), Knight("чорний"), Bishop("чорний"), Queen("чорний"), King("чорний"),
            Bishop("чорний"), Knight("чорний"), Rook("чорний")
        ]
    else:
        game.board.board[7] = [
            Rook("білий"), Knight("білий"), Bishop("білий"), Queen("білий"), King("білий"),
            Bishop("білий"), Knight("білий"), Rook("білий")
        ]

    return {"message": "Гра успішно почалася", "гравець1": гравець1, "гравець2": гравець2}


@app.post("/Рух пішок", response_class=HTMLResponse)
async def move(player: str, start: str, end: str):
    if game is None:
        raise HTTPException(status_code=400, detail="Гра не розпочата")

    start_index = game.board.coordinates.index(start)
    piece = game.board.get_piece_at_position(start)

    if piece is None:
        raise HTTPException(status_code=400, detail="На клітинці немає фігури")

    if (game.current_player == "Гравець1" and "білий" not in piece) or (
            game.current_player == "Гравець2" and "чорний" not in piece):
        raise HTTPException(status_code=400, detail="не ваша фігура")

    if isinstance(piece, str) and "пішачок" in piece.lower():
        piece_instance = Pawn(piece)
    elif isinstance(piece, str) and "тура" in piece.lower():
        piece_instance = Rook(piece)
    elif isinstance(piece, str) and "король" in piece.lower():
        piece_instance = Knight(piece)
    else:
        piece_instance = piece

    if piece_instance is None:
        raise HTTPException(status_code=400, detail="Невірний хід")
    game.move(player, piece_instance, start, end)
    end_index = game.board.coordinates.index(end)
    if isinstance(piece, str) and "пішачок" in piece.lower() and game.board.board[end_index // 8][end_index % 8] is not None:
        game.board.board[end_index // 8][end_index % 8] = None
    return await get_piece_list()

@app.get("/дошка", response_class=HTMLResponse)#тільки для візуавлізації і не більше
async def get_piece_list():
    if game is None or game.board is None or game.board.board is None:
        return HTMLResponse(content="Гра ще не розпочалася.")
    board_html = "<table border='1' cellpadding='20'>"
    for row_num in range(7, -1, -1):
        board_html += f"<tr><td style='background-color: white; color: black; font-size: 24px;'>{row_num + 1}</td>"
        for col_num in range(8):
            piece = game.board.board[row_num][col_num]
            if piece is not None:
                piece_type = piece.__class__.__name__.lower()
                piece_color = piece.color
                text_color = "white" if piece_color == "black" else "black"
                background_color = "black" if piece_color == "black" else "white"
                board_html += f"<td style='background-color: {background_color}; color: {text_color}; font-size: 24px;'>{piece_type} ({piece_color})</td>"
            else:
                if (row_num + col_num) % 2 == 0:
                    board_html += "<td style='background-color: white;'></td>"
                else:
                    board_html += "<td style='background-color: white;'></td>"
        board_html += "</tr>"
    board_html += "<tr>"
    board_html += "<td></td>"
    for col_char in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        board_html += f"<td style='background-color: white; color: black; font-size: 24px;'>{col_char}</td>"
    board_html += "</tr>"
    board_html += "<tr><td colspan='9'></td></tr>"
    board_html += "</table>"
    return HTMLResponse(content=board_html)


@app.get("/result", response_class=HTMLResponse)
async def get_match_results():
    conn = sqlite3.connect('results.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches")
    results = cursor.fetchall()
    conn.close()

    table_content = "<h2>Результати матчів</h2><table border='1'><tr><th>ID</th><th>Гравець 1</th><th>Гравець 2</th><th>Переможець</th><th>Час</th></tr>"
    for row in results:
        table_content += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    table_content += "</table>"
    return HTMLResponse(content=table_content)


@app.post("/fast_win", response_class=HTMLResponse)
async def test_win(winner_name: str):
    if game is None:
        raise HTTPException(status_code=400, detail="Гра не розпочата")

    save_match_result(game.current_player, "програвший", winner_name)
    return HTMLResponse(content=f"переможець {winner_name}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)