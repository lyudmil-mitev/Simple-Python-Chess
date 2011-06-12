import board

__cache = {}
COLORS = { 'white': 0, 'black': 1 }
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

def piece(type, color='white'):
 if type in (None, ' '): return
 if len(type) == 1:
  letter = type
  type = ABBRIVIATIONS[type.upper()]
  if letter.isupper(): color = 'white'
  else: color = 'black'
 try:
   if type not in __cache:
     import sys
     import pieces
     module = sys.modules['pieces']
     __cache[type+' '+color] = module.__dict__[type](color)
     return __cache[type+' '+color]
   else: return __cache[type+' '+color]
 except KeyError:
   raise InvalidPiece

class Piece(object):
 __slots__ = ('abbriviation', 'color', 'move_length')
 move_length = 0 # No limit

 def __init__(self, color):
  try:
    self.color = COLORS[color]
  except KeyError:
    raise InvalidColor	

 def abbriviate(self):
  if self.color == COLORS['white']: return self.abbriviation.upper()
  elif self.color == COLORS['black']: return self.abbriviation.lower()
 
 @property
 def name(self): return self.__class__.__name__

 def possible_moves(self, position, orthogonal, diagonal, distance):
   legal_moves = []
   orth= ((-1,0),(0,-1),(0,1),(1,0))
   diag= ((-1,-1),(-1,1),(1,-1),(1,1))
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
         if dest not in board.occupied('white') + board.occupied('black'):
            legal_moves.append(dest)
         elif dest in board.occupied(piece.get_color()):
            collision = True
         else:
            legal_moves.append(dest)
            collision = True

   legal_moves = filter(board.is_in_bounds, legal_moves)
   return map(board.letter_notation, legal_moves)

 def __str__(self):
  return self.abbriviation
 
 def get_color(self):
  return COLORS.keys()[COLORS.values().index(self.color)]

 def __repr__(self):
  return "<" + self.get_color().capitalize() + " " + self.__class__.__name__ + ">"

class Pawn(Piece):
 abbriviation = 'p'
 def possible_moves(self, position):
   position = position.upper()
   piece = self
   if self.color == COLORS['white']:
      homerow, direction, enemy = 1, 1, 'black'
   else:
      homerow, direction, enemy = 6, -1, 'white'
   
   legal_moves = []

   # Moving

   blocked = board.occupied('white') + board.occupied('black')
   from_   = board.number_notation(position)
   forward = from_[0] + direction, from_[1]

   # Can we move forward?
   if forward not in blocked:
      legal_moves.append(forward)
      if from_[0] == homerow:
         # If pawn in starting position we can do a double move
         double_forward = forward[0] + direction, forward[1]
         if double_forward not in blocked:
            legal_moves.append(double_forward)

   # Attacking
   for a in range(-1, 2, 2):
      attack = from_[0] + direction, from_[1] + a
      if attack in board.occupied(enemy):
         legal_moves.append(attack)

   # TODO: En passant
   legal_moves = filter(board.is_in_bounds, legal_moves)
   return map(board.letter_notation, legal_moves)


class Knight(Piece):
 abbriviation = 'n'
 def possible_moves(self,position):
   position = position.upper()
   legal_moves = []
   from_ = board.number_notation(position)
   piece = board.get(position)
   deltas = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))

   for x,y in deltas:
       dest = from_[0]+x, from_[1]+y
       if(dest not in board.occupied(piece.get_color())):
          legal_moves.append(dest)

   legal_moves = filter(board.is_in_bounds, legal_moves)
   return map(board.letter_notation, legal_moves)


class Rook(Piece):
 abbriviation = 'r'
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
 def possible_moves(self,position):
    position = position.upper()
    return super(King, self).possible_moves(position, True, True, 1)
