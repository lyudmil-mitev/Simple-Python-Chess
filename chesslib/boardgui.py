import board as chessboard
import pieces
import Tkinter as tk
from PIL import Image, ImageTk

class BoardGUI(tk.Frame):
    def __init__(self, parent, rows=8, columns=8, size=32, color1="white", color2="grey"):
        ''' size is the size of a square, in pixels '''

        self.rows = rows
        self.columns = columns
        self.size = size
        self.color1 = color1
        self.color2 = color2
        self.pieces = {}
        self.selected = None
        self.selected_piece = None
        self.hilighted = None
        self.icons = {}
        self.parent = parent

        canvas_width = columns * size
        canvas_height = rows * size

        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0,
                                width=canvas_width, height=canvas_height, background="grey")
        self.canvas.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        # this binding will cause a refresh if the user interactively
        # changes the window size
        self.canvas.bind("<Configure>", self.refresh)
        self.canvas.bind("<Button-1>", self.click)

        self.button_quit = tk.Button(self, text="New", fg="black", command=self.reset)
        self.button_quit.pack(side=tk.LEFT)
        self.button_save = tk.Button(self, text="Save", fg="black", command=chessboard.save_to_file)
        self.button_save.pack(side=tk.LEFT)

        self.label_status = tk.Label(self, text="   White's turn  ", fg="black")
        self.label_status.pack(side=tk.LEFT)
        self.button_quit = tk.Button(self, text="Quit", fg="black", command=self.close)
        self.button_quit.pack(side=tk.RIGHT)


        #self.button_load = tk.Button(self, text="Load", fg="black")
        #self.button_load.pack(side=tk.RIGHT)

        #self.button_save = tk.Button(self, text="Save", fg="black")
        #self.button_save.pack(side=tk.RIGHT)

    def close(self):
        self.parent.destroy()

    def click(self, event):
        col_pix, row_pix = self.ysize, self.ysize
        col = event.x / col_pix
        row = 7-(event.y / row_pix)
        # self.label_status["text"] = "%s, %s, %s, %s" % (event.x, event.y, col, row)
        self.selected = (row, col)
        pos = chessboard.letter_notation(self.selected)
        piece = chessboard.get(pos)
        if piece is not None and (piece.color == chessboard.player_turn):
            self.selected_piece = (piece, pos)
            self.hilighted = map(chessboard.number_notation, (chessboard.get(pos).possible_moves(pos)))

        if self.selected_piece and ((piece is None) or\
              (piece.color != self.selected_piece[0].color)):
            # making a move
            try:
                chessboard.move(self.selected_piece[1], pos)
            except chessboard.Check:
                self.label_status["text"] = " You are in check!"
            except chessboard.CheckMate:
                self.label_status["text"] = " Check!"
            except chessboard.InvalidMove:
                self.label_status["text"] = " Invalid move!"
            except chessboard.Draw:
                self.label_status["text"] = " Draw!"
            except Exception as e:
                self.label_status["text"] = e.__class__.__name__
            else:
                self.label_status["text"] = " " + self.selected_piece[0].get_color().capitalize() +": "+ self.selected_piece[1]+pos


            self.selected_piece = None
            self.hilighted = None
            self.pieces = {}
            self.refresh(event)
            self.draw_pieces()
            self.refresh(event)
        self.refresh(event)

    def addpiece(self, name, image, row=0, column=0):
        '''Add a piece to the playing board'''
        self.canvas.create_image(0,0, image=image, tags=(name, "piece"), anchor="c")
        self.placepiece(name, row, column)

    def placepiece(self, name, row, column):
        '''Place a piece at the given row/column'''
        self.pieces[name] = (row, column)
        x0 = (column * self.size) + int(self.size/2)
        y0 = ((7-row) * self.size) + int(self.size/2)
        self.canvas.coords(name, x0, y0)

    def refresh(self, event={}):
        '''Redraw the board, possibly in response to window being resized'''
        try:
            self.xsize = int((event.width-1) / self.columns)
            self.ysize = int((event.height-1) / self.rows)
        except Exception:
            pass

        self.size = min(self.xsize, self.ysize)
        self.canvas.delete("square")
        color = self.color2
        for row in range(self.rows):
            color = self.color1 if color == self.color2 else self.color2
            for col in range(self.columns):
                x1 = (col * self.size)
                y1 = ((7-row) * self.size)
                x2 = x1 + self.size
                y2 = y1 + self.size
                if (self.selected is not None) and (row, col) == self.selected:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="orange", tags="square")
                elif(self.hilighted is not None and (row, col) in self.hilighted):
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="spring green", tags="square")
                else:
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill=color, tags="square")
                color = self.color1 if color == self.color2 else self.color2
        for name in self.pieces:
            self.placepiece(name, self.pieces[name][0], self.pieces[name][1])
        self.canvas.tag_raise("piece")
        self.canvas.tag_lower("square")

    def draw_pieces(self):
        self.canvas.delete("piece")
        for x in range(0,len(chessboard.table)):
            for y in range(0,len(chessboard.table[x])):
                piece = chessboard.table[x][y]
                if piece is not None:
                    filename = "img/%s%s.png" % (piece.color, piece.abbriviation)
                    piecename = "%s%s%s" % (piece.abbriviation, x, y)

                    if(filename not in self.icons):
                        self.icons[filename] = ImageTk.PhotoImage(file=filename, width=32, height=32)

                    self.addpiece(piecename, self.icons[filename], x, y)
                    self.placepiece(piecename, x, y)
        #print chessboard.unicode_representation()

    def reset(self):
        chessboard.init()
        self.refresh()
        self.draw_pieces()
        self.refresh()

def display():
    root = tk.Tk()
    root.title("Simply Chess")
    b= BoardGUI(root)
    b.pack(side="top", fill="both", expand="false", padx=4, pady=4)
    b.draw_pieces()
    #b.placepiece("bishop", 6, 6)

    #b.addpiece("player2", player2, 3,5)
    root.resizable(0,0)
    root.mainloop()

if __name__ == "__main__":
    display()
