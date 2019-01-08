import time
from Tkinter import *
from chesslib import board
from chesslib import gui_tkinter
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Play a game of chess')
parser.add_argument("--depth", type=int,
                    help='stockfish search depth',
                    default=10)
parser.add_argument("--n_player", type=int,
                    help='number of human players',
                    default=0)
args = parser.parse_args()
current_proc = None
depth = args.depth
n_player = args.n_player

def getEngine():
    global current_proc, depth
    if current_proc is not None:
        if current_proc.poll() is not None:
            raise ValueError('Engine died')
    if current_proc is None or current_proc.poll() is not None:
        current_proc = subprocess.Popen('stockfish', stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        current_proc.stdin.write('uci\n')
        depth += 1
    return current_proc


moves = []
def isEnPassent(move, piece):
    out = False
    ## pawn to blank space
    if piece.abbriviation.lower() != 'p' or game[move[2:4]] is not None:
        out = False
    elif move[1] == '5' and move[3] == '6' and move[0] != move[2]: ## white diag
        out = move[2] + '5'
    elif move[1] == '4' and move[3] == '3' and move[0] != move[2]: ## black diag
        out = move[2] + '3'
    return out

def isCastle(move, piece):
    '''return move for castle if it is else False'''
    move = move.upper()
    if piece.abbriviation.lower() != 'k':
        out = False
    elif move == 'E1G1' and piece.color == 'white':
        out = 'H1F1'
    elif move == 'E1C1' and piece.color == 'white':
        out = 'A1D1'
    elif move == 'E8G8' and piece.color == 'black':
        out = 'H8F8'
    elif move == 'E8C8' and piece.color == 'black':
        out = 'A8D8'
    else:
        out = False
    return out

def go():
    if n_player == 2:
        return
    elif n_player == 1 and game.export().split()[1] == 'w':
        r.after(1000, go)
        return
    engine = getEngine()
    fen = game.export()
    command = 'position fen %s\n' % fen
    # print '<<<', command
    engine.stdin.write(command)
    engine.stdin.write('go depth %d\n' % depth)
    line = ''
    while 'bestmove' not in line and engine.poll() is None:
        if line:
            pass
            # print '>>>', line.strip(), engine.poll()
        line = engine.stdout.readline()
        if line == '':
            break
    if 'bestmove' in line:
        # print '>>>', line
        words = line.split()
        move = words[1].upper()
        if move == '(NONE)':
            print 'Game Over!'
            return
        piece = gui.chessboard[move[:2]]
        if len(move) > 4:
            promote = move[4]
        else:
            promote = None
        gui.move(move[:2], move[2:4], promote=promote)

        enemy = gui.chessboard.get_enemy(piece.color)
        moves.append(move)
        # print move,
        if piece.color == 'black':
            gui.chessboard.fullmove_number += 1
            # print ''
        gui.chessboard.halfmove_clock +=1
        gui.chessboard.player_turn = enemy
        gui.refresh()
        gui.draw_pieces()
        gui.redraw_square(gui.from_square, 'tan1')
        gui.redraw_square(gui.to_square, 'tan1')
        if gui.chessboard.is_in_check(enemy):
            p = gui.chessboard.get_king_position(enemy)
            p = gui.chessboard.number_notation(p)
            gui.redraw_square(p, 'red')
    r.after(100, go)
            
game = board.Board()
r = Tk()
r.after(1000, go)
gui = gui_tkinter.BoardGuiTk(r, game)
gui.pack()
gui.draw_pieces()

r.mainloop()

