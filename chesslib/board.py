from itertools import groupby
from copy import deepcopy

import pieces
import re

class ChessError(Exception): pass
class InvalidCoord(ChessError): pass
class InvalidColor(ChessError): pass
class InvalidMove(ChessError): pass
class Check(ChessError): pass
class CheckMate(ChessError): pass
class Draw(ChessError): pass
class NotYourTurn(ChessError): pass

FEN_STARTING = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
RANK_REGEX = re.compile(r"^[A-Z][1-8]$")

class Board(dict):
    '''
       Board

       A simple chessboard class

       TODO:

        * PGN export
        * En passant (Done TJS)
        * Castling (Done TJS)
        * Promoting pawns (Done TJS)
        * 3-time repition (Done TJS)
        * Fifty-move rule
        * Take-backs
        * row/column lables
        * captured piece imbalance (show how many pawns pieces player is up)
    '''

    axis_y = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    axis_x = tuple(range(1,9)) # (1,2,3,...8)

    captured_pieces = { 'white': [], 'black': [] }
    player_turn = None
    castling = '-'
    en_passant = '-'
    halfmove_clock = 0
    fullmove_number = 1
    def __init__(self, fen = None):
        if fen is None: self.load(FEN_STARTING)
        else: self.load(fen)
        self.last_move = None ## to support en passent
        self.positions = [None]
        
    def __getitem__(self, coord):
        if isinstance(coord, str):
            coord = coord.upper()
            if not re.match(RANK_REGEX, coord.upper()): raise KeyError
        elif isinstance(coord, tuple):
            coord = self.letter_notation(coord)
        try:
            return super(Board, self).__getitem__(coord)
        except KeyError:
            return None

    def save_to_file(self): pass

    def is_in_check_after_move(self, p1, p2):
        # Create a temporary board
        tmp = deepcopy(self)
        tmp._do_move(p1,p2)
        return tmp.is_in_check(self[p1].color)

    def move(self, p1, p2, promote='q'):
        p1, p2 = p1.upper(), p2.upper()
        piece = self[p1]
        dest  = self[p2]

        if self.player_turn != piece.color:
            raise NotYourTurn("Not " + piece.color + "'s turn!")

        enemy = self.get_enemy(piece.color)
        possible_moves = piece.possible_moves(p1)
        # 0. Check if p2 is in the possible moves
        if p2 not in possible_moves:
            raise InvalidMove
        
        # If enemy has any moves look for check
        if self.all_possible_moves(enemy):
            if self.is_in_check_after_move(p1,p2):
                raise Check
        if not possible_moves and self.is_in_check(piece.color):
            raise CheckMate
        elif not possible_moves:
            raise Draw
        else:
            self._do_move(p1, p2, promote)
            self._finish_move(piece, dest, p1,p2)
            if self.positions[-1] in self.positions[:-1]:
                count = 1
                for position in self.positions[:-1]:
                    count += (position == self.positions[-1])
                print 'repetition count:', count
                if count >= 3:
                    raise Draw

    def get_enemy(self, color):
        if color == "white": return "black"
        else: return "white"

    def is_en_passent(self, p1, p2, piece):
        '''
        return False if move is not an en passent, otherwise return square to capture on
        '''
        out = False
        ## pawn to blank space
        move = p1 + p2
        if not self.is_pawn(piece) or self[move[2:4]] is not None:
            out = False
        elif move[1] == '5' and move[3] == '6' and move[0] != move[2]: ## white diag
            out = move[2] + '5'
        elif move[1] == '4' and move[3] == '3' and move[0] != move[2]: ## black diag
            out = move[2] + '4'
        return out

    def is_castle(self, p1, p2, piece):
        '''return move for castle if it is else False'''
        move = p1.upper() + p2.upper()
        if not self.is_king(piece):
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

    def _do_move(self, p1, p2, promote='q'):
        '''
            Move a piece without validation
        '''
        piece = self[p1]
        if self.is_king(piece):
            piece.can_castle = False
        if self.is_rook(piece):
            piece.can_castle = False

        dest  = self[p2]
        ## if piece is a king and move is a castle, move the rook too
        castle = self.is_castle(p1, p2, piece)
        if castle:
            move = castle
            self._do_move(move[:2], move[2:])
        en_passent = self.is_en_passent(p1, p2, piece)
        if en_passent:
            del self[en_passent]
        del self[p1]
        self.last_move = (p1, p2)
        ## check pawn promotion
        if self.is_pawn(piece) and p2[1] in '18':
            piece = pieces.Pieces[promote.upper()](piece.color)
            piece.board = self
        self[p2] = piece

        ## for three-fold repetiion
        fen = self.export().split()
        self.positions.append(fen[0] + fen[1])

    def _finish_move(self, piece, dest, p1, p2):
        '''
            Set next player turn, count moves, log moves, etc.
        '''
        enemy = self.get_enemy(piece.color)
        if piece.color == 'black':
            self.fullmove_number += 1
        self.halfmove_clock +=1
        self.player_turn = enemy
        abbr = piece.abbriviation
        if abbr == 'P':
            # Pawn has no letter
            abbr = ''
            # Pawn resets halfmove_clock
            self.halfmove_clock = 0
        if dest is None:
            # No capturing
            movetext = abbr +  p2.lower()
        else:
            # Capturing
            movetext = abbr + 'x' + p2.lower()
            # Capturing resets halfmove_clock
            self.halfmove_clock = 0

    def all_possible_moves(self, color):
        '''
            Return a list of `color`'s possible moves.
            Does not check for check.
        '''
        if(color not in ("black", "white")): raise InvalidColor
        result = []
        for coord in self.keys():
            if (self[coord] is not None) and self[coord].color == color:
                moves = self[coord].possible_moves(coord)
                if moves: result += moves
        return result

    def occupied(self, color):
        '''
            Return a list of coordinates occupied by `color`
        '''
        result = []
        if(color not in ("black", "white")): raise InvalidColor

        for coord in self:
            if self[coord].color == color:
                result.append(coord)
        return result

    def is_king(self, piece):
        return isinstance(piece, pieces.King)

    def is_rook(self, piece):
        return isinstance(piece, pieces.Rook)

    def is_pawn(self, piece):
        return isinstance(piece, pieces.Pawn)


    def get_king_position(self, color):
        for pos in self.keys():
            if self.is_king(self[pos]) and self[pos].color == color:
                return pos

    def get_king(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        return self[self.get_king_position(color)]

    def is_in_check(self, color):
        if(color not in ("black", "white")): raise InvalidColor
        king = self.get_king(color)
        enemy = self.get_enemy(color)
        return king in map(self.__getitem__, self.all_possible_moves(enemy))

    def letter_notation(self,coord):
        if not self.is_in_bounds(coord): return
        try:
            return self.axis_y[coord[1]] + str(self.axis_x[coord[0]])
        except IndexError:
            raise InvalidCoord

    def number_notation(self, coord):
        return int(coord[1])-1, self.axis_y.index(coord[0])

    def is_in_bounds(self, coord):
        if coord[1] < 0 or coord[1] > 7 or\
           coord[0] < 0 or coord[0] > 7:
            return False
        else: return True
    def clear(self):
        dict.clear(self)
        self.poistions = [None]
        
    def load(self, fen):
        '''
            Import state from FEN notation
        '''
        self.clear()
        # Split data
        fen = fen.split(' ')
        # Expand blanks
        def expand(match): return ' ' * int(match.group(0))

        fen[0] = re.compile(r'\d').sub(expand, fen[0])
        self.positions = [None]
        for x, row in enumerate(fen[0].split('/')):
            for y, letter in enumerate(row):
                if letter == ' ': continue
                coord = self.letter_notation((7-x,y))
                self[coord] = pieces.piece(letter)
                self[coord].place(self)

        if fen[1] == 'w': self.player_turn = 'white'
        else: self.player_turn = 'black'

        self.castling = fen[2]
        self.en_passant = fen[3]
        self.halfmove_clock = int(fen[4])
        self.fullmove_number = int(fen[5])

    def can_en_passent(self):
        out = '-'
        if self.last_move and abs(int(self.last_move[1][1]) - int(self.last_move[0][1])) == 2:
            if self.is_pawn(self[self.last_move[1]]): ### yes we can
                out = self.last_move[1][0].lower()
                if self.last_move[1][1] == '4':
                    out += '3'
                else:
                    out += '6'
        return out
        
    def export(self):
        '''
            Export state to FEN notation
        '''
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

        castling = ''
        if self.is_king(self['E1']) and self.is_rook(self['H1']):
            king = self['E1']
            rook = self['H1']
            if king.can_castle and rook.can_castle:
                castling += 'K'
        if self.is_king(self['E1']) and self.is_rook(self['A1']):
            king = self['E1']
            rook = self['A1']
            if king.can_castle and rook.can_castle:
                castling += 'Q'
        if self.is_king(self['E8']) and self.is_rook(self['H8']):
            king = self['E8']
            rook = self['H8']
            if king.can_castle and rook.can_castle:
                castling += 'k'
        if self.is_king(self['E8']) and self.is_rook(self['A8']):
            king = self['E8']
            rook = self['A8']
            if king.can_castle and rook.can_castle:
                castling += 'q'
        if castling == '':
            castling = '-'

        en_passent = self.can_en_passent()

        result = result[:-1] # remove trailing "/"
        result = replace_spaces(result)
        result += " " + (" ".join([self.player_turn[0],
                         castling,
                         en_passent,
                         str(self.halfmove_clock),
                         str(self.fullmove_number)]))
        return result
