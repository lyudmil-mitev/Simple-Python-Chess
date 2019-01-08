import pieces
import sys

ABBRIVIATIONS = {
 'R':'Rook',
 'N':'Knight',
 'B':'Bishop',
 'Q':'Queen',
 'K':'King',
 'P':'Pawn'
}

class InvalidPiece(Exception): pass
class InvalidColor(Exception): pass

def piece(piece, color='white'):
    ''' Takes a piece name or abbriviation and returns the corresponding piece instance '''
    if piece in (None, ' '): return
    if len(piece) == 1:
        # We have an abbriviation
        if piece.isupper(): color = 'white'
        else: color = 'black'
        piece = ABBRIVIATIONS[piece.upper()]
    module = sys.modules[__name__]
    return module.__dict__[piece](color)

class Piece(object):
    __slots__ = ('abbriviation', 'color')

    def __init__(self, color):
        self.can_castle = False
        if color == 'white':
            self.abbriviation = self.abbriviation.upper()
        elif color == 'black':
            self.abbriviation = self.abbriviation.lower()

        try:
            self.color = color
        except KeyError:
            raise InvalidColor

    @property
    def name(self): return self.__class__.__name__
    def place(self, board):
        ''' Keep a reference to the board '''
        self.board = board

    def possible_moves(self, position, orthogonal, diagonal, distance):
        board = self.board
        legal_moves = []
        orth  = ((-1,0),(0,-1),(0,1),(1,0))
        diag  = ((-1,-1),(-1,1),(1,-1),(1,1))
        piece = self

        from_ = board.number_notation(position)
        if orthogonal and diagonal:
            directions = diag+orth
        elif diagonal:
            directions = diag
        elif orthogonal:
            directions = orth

        for x,y in directions:
            collision = False
            for step in range(1, distance+1):
                if collision: break
                dest = from_[0]+step*x, from_[1]+step*y
                if self.board.letter_notation(dest) not in board.occupied('white') + board.occupied('black'):
                    legal_moves.append(dest)
                elif self.board.letter_notation(dest) in board.occupied(piece.color):
                    collision = True
                else:
                    legal_moves.append(dest)
                    collision = True

        legal_moves = filter(board.is_in_bounds, legal_moves)
        return map(board.letter_notation, legal_moves)

    def __str__(self):
        return self.abbriviation

    def __repr__(self):
        return "<" + self.color.capitalize() + " " + self.__class__.__name__ + ">"

class Pawn(Piece):
    abbriviation = 'p'
    def possible_moves(self, position):
        board = self.board
        position = position.upper()
        piece = self
        if self.color == 'white':
            homerow, direction, enemy = 1, 1, 'black'
        else:
            homerow, direction, enemy = 6, -1, 'white'

        legal_moves = []

        # Moving

        blocked = board.occupied('white') + board.occupied('black')
        from_   = board.number_notation(position)
        forward = from_[0] + direction, from_[1]

        # Can we move forward?
        if board.letter_notation(forward) not in blocked:
            legal_moves.append(forward)
            if from_[0] == homerow:
                # If pawn in starting position we can do a double move
                double_forward = (forward[0] + direction, forward[1])
                if board.letter_notation(double_forward) not in blocked:
                    legal_moves.append(double_forward)

        # Attacking
        for a in range(-1, 2, 2):
            attack = from_[0] + direction, from_[1] + a
            if board.letter_notation(attack) in board.occupied(enemy):
                legal_moves.append(attack)

        ## TJS: check for en passent
        en_passent = board.can_en_passent()
        if en_passent != '-':
            if self.color == 'white' and position[1] == '5':
                if abs(ord(position[0].lower()) - ord(en_passent[0].lower())) == 1:
                    legal_moves.append((int(en_passent[1]) - 1, ord(en_passent[0].lower()) - ord('a')))
            if self.color == 'black' and position[1] == '4':
                if abs(ord(position[0].lower()) - ord(en_passent[0].lower())) == 1:
                    legal_moves.append((int(en_passent[1]) - 1, ord(en_passent[0].lower()) - ord('a')))
        legal_moves = filter(board.is_in_bounds, legal_moves)
        return map(board.letter_notation, legal_moves)


class Knight(Piece):
    abbriviation = 'n'
    def possible_moves(self,position):
        board = self.board
        position = position.upper()
        legal_moves = []
        from_ = board.number_notation(position)
        piece = board.get(position)
        deltas = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))

        for x,y in deltas:
            dest = from_[0]+x, from_[1]+y
            if(board.letter_notation(dest) not in board.occupied(piece.color)):
                legal_moves.append(dest)

        legal_moves = filter(board.is_in_bounds, legal_moves)
        return map(board.letter_notation, legal_moves)


class Rook(Piece):
    abbriviation = 'r'
    def __init__(self, color):
        Piece.__init__(self, color)
        self.can_castle = True
    def possible_moves(self,position):
        position = position.upper()
        return super(Rook, self).possible_moves(position, True, False, 8)

class Bishop(Piece):
    abbriviation = 'b'
    def possible_moves(self,position):
        position = position.upper()
        return super(Bishop,self).possible_moves(position, False, True, 8)

class Queen(Piece):
    abbriviation = 'q'
    def possible_moves(self,position):
        position = position.upper()
        return super(Queen, self).possible_moves(position, True, True, 8)

class King(Piece):
    abbriviation = 'k'
    move_length = 1
    def __init__(self, color):
        Piece.__init__(self, color)
        self.can_castle = True
        
    def possible_moves(self,position):
        position = position.upper()
        out = super(King, self).possible_moves(position, True, True, 1)
        ## check castling
        if self.can_castle:
            if self.color == 'white':
                if self.board['H1'] is not None and self.board['H1'].can_castle:
                    if self.board['F1'] is None and self.board['G1'] is None:
                        out.append('G1')
                if self.board['A1'] is not None and self.board['A1'].can_castle:
                    if (self.board['B1'] is None and
                        self.board['C1'] is None and
                        self.board['D1'] is None):
                        out.append('C1')
            else:
                if self.board['H8'] is not None and self.board['H8'].can_castle:
                    if self.board['F8'] is None and self.board['G8'] is None:
                        out.append('G8')
                if self.board['A8'] is not None and self.board['A8'].can_castle:
                    if (self.board['B8'] is None and
                        self.board['C8'] is None and
                        self.board['D8'] is None):
                        out.append('C8')
        return out
Pieces = {
    'P':Pawn,
    'R':Rook,
    'N':Knight,
    'B':Bishop,
    'Q':Queen,
    'K':King
}
