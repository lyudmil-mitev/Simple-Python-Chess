# -*- encoding: utf-8 -*-
from copy import copy, deepcopy
from itertools import groupby

import pieces
import re

class ChessError(Exception): pass
class InvalidCoord(ChessError): pass
class InvalidMove(ChessError): pass
class Check(ChessError): pass
class CheckMate(ChessError): pass
class Draw(ChessError): pass
class NotYourTurn(ChessError): pass

class Board(object):
    '''
       Board

       A simple chessboard class

       TODO:

        * PGN export
        * En passant
        * Castling
        * Promoting pawns
        * Fifty-move rule

    '''

    axis_y = ('A','B','C','D','E','F','G','H')
    axis_x = tuple(range(1,9)) # (1,2,3,...8)

    captured_pieces = { 'white': [], 'black': [] }
    player_turn = None
    castling = '-'
    en_passant = '-'
    halfmove_clock = 0
    fullmove_number = 1
    table = {}
    history = []

    unicode_pieces = {
      'r': u'♜', 'n': u'♞', 'b': u'♝', 'q': u'♛',
      'k': u'♚', 'p': u'♟', 'R': u'♖', 'N': u'♘',
      'B': u'♗', 'Q': u'♕', 'K': u'♔', 'P': u'♙',
      None: ' '
    }

    FEN_starting = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def __init__(self, fen = None):
        if fen is None:
            self.load(self.FEN_starting)
        else:
            self.load(fen)

    def __getitem__(self, coord):
        if isinstance(coord, str):
            coord = coord.upper()
            regex = re.compile(r"^[A-Z][1-8]$")
            if not re.match(regex, coord.upper()): raise KeyError
        elif isinstance(coord, tuple):
            coord = self.letter_notation(coord)

        try:
            return self.table[coord]
        except KeyError:
            return None

    def move(self, p1, p2):
        p1, p2 = p1.upper(), p2.upper()
        piece = self[p1]
        dest  = self[p2]

        if self.player_turn != piece.color:
            raise NotYourTurn("Not " + piece.get_color() + "'s turn!")

        enemy = self.get_enemy(piece.color)
        # 0. Check if p2 is in the possible moves
        if p2 not in piece.possible_moves(p1):
            raise InvalidMove

        self._do_move(p1, p2)
        '''
        # 1. Filter possible moves: remove the ones that will make you in check
         # if no possible moves and not in check -- Draw
         # if no possible moves and in check -- Checkmate
        if enemy_moves:
           # Save current state
           temporary_board = Board(self.export())

           if p2 in piece.possible_moves(p1):
              _do_move(p1, p2)
           elif not piece.possible_moves(p1):
              raise CheckMate(enemy + " wins!")

           if is_in_check(piece.get_color()):
              # Restore table
              table = current_table
              raise Check

           _finish_move(piece,dest,p1,p2)

        elif p2 in piece.possible_moves(p1):
           _do_move(p1, p2)
           _finish_move(piece,dest,p1,p2)
        elif not piece.possible_moves(p1):
           raise Draw
        '''

    def get_enemy(self, color):
        if color == "white":
            return "black"
        else:
            return "white"

    def _do_move(self, p1, p2):
        ''' Move a piece without validation '''
        piece = self[p1]
        dest  = self[p2]
        p1c = number_notation(p1)
        p2c = number_notation(p2)
        del self[p1]
        self[p2] = piece

    def _finish_move(self, piece, dest,p1,p2):
        ''' Set next player turn, count moves, log moves '''
        global player_turn, fullmove_number, history, halfmove_clock
        enemy = get_enemy(piece.get_color())
        player_turn = pieces.COLORS[enemy]
        if piece.get_color() == 'black':
            fullmove_number += 1
        halfmove_clock +=1

        abbr = piece.abbriviation.upper()
        if abbr == 'P':
            # Pawn has no letter
            abbr = ''
            # Pawn resets halfmove_clock
            halfmove_clock = 0
        if dest is None:
            # No capturing
            movetext = abbr +  p2.lower()
        else:
            # Capturing
            movetext = abbr + 'x' + p2.lower()
            # Capturing resets halfmove_clock
            halfmove_clock = 0

        history.append(movetext)


    def all_possible_moves(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        result = []
        for x in range(0,len(table)):
            for y in range(0,len(table[x])):
                if (table[x][y] is not None) and table[x][y].get_color() == color:
                    moves = table[x][y].possible_moves(letter_notation((x,y)))
                    if moves: result += moves
        return result

    def occupied(self, color):
        result = []
        if(color not in ("black", "white")): raise InvalidColor

        for x in range(0,len(table)):
            for y in range(0,len(table[x])):
                if (table[x][y] is not None) and (table[x][y].color == color):
                    result.append((x, y))
        return result

    def get_king_position(self, color):
        for x in range(0,len(table)):
            for y in range(0,len(table[x])):
                piece = table[x][y]
                if (piece is not None) and\
                   isinstance(piece, pieces.King) and\
                   (piece.color == pieces.COLORS[color]):
                    return letter_notation((x,y))

    def get_king(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        return get(get_king_position(color))

    def is_in_check(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        king = self.get_king(color)
        enemy = self.get_enemy(color)
        return king in map(get, all_possible_moves(enemy))

    def number_notation(self, coord):
        return int(coord[1])-1, axis_y.index(coord[0])

    def unicode_representation(self):
        for number in self.axis_x[::-1]:
            print " " + str(number) + " ",
            for letter in self.axis_y:
                piece = self[letter+str(number)]
                if piece is not None:
                    print self.unicode_pieces[piece.abbriviation] + ' ',
                else: print '  ',
            print "\n"
        print "    " + "  ".join(self.axis_y)

    def is_in_bounds(self, coord):
        if coord[1] < 0 or coord[1] > 7 or\
           coord[0] < 0 or coord[0] > 7:
            return False
        else: return True

    def load(self, fen):
        ''' Import state from FEN notation '''
        # Split data
        fen = fen.split(' ')
        # Expand blanks
        def expand(match): return ' ' * int(match.group(0))

        fen[0] = re.compile(r'\d').sub(expand, fen[0])

        for x, row in enumerate(fen[0].split('/')):
            for y, letter in enumerate(row):
                if letter == ' ': continue
                coord = self.letter_notation((7-x,y))
                self.table[coord] = pieces.piece(letter)
                self.table[coord].place(self)

        if fen[1] == 'w': self.player_turn = 'white'
        else: self.player_turn = 'black'

        self.castling = fen[2]
        self.en_passant = fen[3]
        self.halfmove_clock = int(fen[4])
        self.fullmove_number = int(fen[5])

    def export(self):
        ''' Export state to FEN notation '''
        def join(k, g):
            if k == ' ': return str(len(g))
            else: return "".join(g)

        def replace_spaces(row):
            # replace spaces with their count
            result = [join(k, list(g)) for k,g in groupby(row)]
            return "".join(result)


        result = ''
        for number in self.axis_x[::-1]:
            for letter in self.axis_y:
                piece = self[letter+str(number)]
                if piece is not None:
                    result += piece.abbriviation
                else: result += ' '
            result += '/'

        result = result[:-1] # remove trailing "/"
        result = replace_spaces(result)
        result += " " + (" ".join([self.player_turn[0],
                         self.castling,
                         self.en_passant,
                         str(self.halfmove_clock),
                         str(self.fullmove_number)]))
        return result

    def letter_notation(self,coord):
        if not self.is_in_bounds(coord):
            raise InvalidCoord

        try:
            return self.axis_y[coord[1]] + str(self.axis_x[coord[0]])
        except IndexError:
            raise InvalidCoord
