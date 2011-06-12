# -*- encoding: utf-8 -*-
from copy import copy, deepcopy
from itertools import groupby
import pieces
import re

'''
   Board

   This module implements a singleton chessboard class

   TODO:

    * PGN export
    * En passant
    * Castling
    * Promoting pawns
    * Fifty-move rule

'''

class InvalidCoord(Exception): pass
class InvalidMove(Exception): pass
class Check(Exception): pass
class CheckMate(Exception): pass
class Draw(Exception): pass
class NotYourTurn(Exception): pass

axis_y = ('A','B','C','D','E','F','G','H')
axis_x = tuple(range(1,9)) # (1,2,3,...8)
player_turn = None
captured_pieces = { 'white': [], 'black': [] }
castling = ''
en_passant = ''
halfmove_clock = 0
fullmove_number = 1
history = []

unicode_pieces = {
  'R': u'♜', 'N': u'♞', 'B': u'♝', 'Q': u'♛',
  'K': u'♚', 'P': u'♟', 'r': u'♖', 'n': u'♘',
  'b': u'♗', 'q': u'♕', 'k': u'♔', 'p': u'♙',
  None: ' '
}

FEN_starting = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

def init():
  load(FEN_starting)
	
def get(coord):
   coord = coord.upper()
   regex = re.compile(r"^[A-Z][1-8]$")
   if not re.match(regex, coord.upper()): raise KeyError

   x,y = number_notation(coord)
   return table[x][y]

def move(p1, p2):
  p1, p2 = p1.upper(), p2.upper()
  piece = get(p1)
  dest  = get(p2)
  global player_turn
  if player_turn != piece.color:
     raise NotYourTurn("Not " + piece.get_color() + "'s turn!")

  if piece.get_color() == "white":
     enemy = "black"
  else:
     enemy = "white"

  if p2 not in piece.possible_moves(p1):
     raise InvalidMove

  enemy_moves = all_possible_moves(enemy)
  if enemy_moves:
     # Save current state
     global table
     current_table = deepcopy(table)

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

def get_enemy(color):
  if color == "white":
     return "black"
  else:
     return "white"


def _do_move(p1, p2):
  ''' Move a piece without validation '''
  piece = get(p1)
  dest  = get(p2)
  p1c = number_notation(p1)
  p2c = number_notation(p2)
  table[p1c[0]][p1c[1]] = None
  table[p2c[0]][p2c[1]] = piece

def _finish_move(piece, dest,p1,p2):
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

  
def all_possible_moves(color):
  result = []
  for x in range(0,len(table)):
     for y in range(0,len(table[x])):
         if (table[x][y] is not None) and table[x][y].get_color() == color:
             moves = table[x][y].possible_moves(letter_notation((x,y)))
             if moves: result += moves
  return result

def occupied(color):
   result = []
   try:
      color = pieces.COLORS[color]
   except KeyError:
      raise pieces.InvalidColor

   for x in range(0,len(table)):
      for y in range(0,len(table[x])):
         if (table[x][y] is not None) and (table[x][y].color == color):
          result.append((x, y))
   return result

def get_king_position(color):
   for x in range(0,len(table)):
      for y in range(0,len(table[x])):
         piece = table[x][y]
         if (piece is not None) and\
            isinstance(piece, pieces.King) and\
            (piece.color == pieces.COLORS[color]):
            return letter_notation((x,y))

def get_king(color):
   return get(get_king_position(color))

def is_in_check(color):
    king = get_king(color)
    if color == 'white': enemy = 'black'
    else: enemy = 'white'
    return king in map(get, all_possible_moves(enemy))

def number_notation(coord):
  return int(coord[1])-1, axis_y.index(coord[0])

def unicode_representation():
 for number in axis_x[::-1]:
  print " " + str(number) + " ",
  for letter in axis_y:
   piece = get(letter+str(number))
   if piece is not None:
    print unicode_pieces[piece.abbriviate()] + ' ',
   else: print '  ',
  print "\n"
 print "    " + "  ".join(axis_y)

def is_in_bounds(coord):
  if coord[1] < 0 or coord[1] > 7 or\
     coord[0] < 0 or coord[0] > 7:
        return False
  else: return True

def save_to_file():
  with open("state.fen", "w") as savefile:
	savefile.write(export())

def load(fen):
   ''' Import state from FEN notation '''
   global table, castling, en_passant,\
          halfmove_clock, fullmove_number, player_turn
   # Split data
   fen = fen.split(' ')
   # Expand blanks
   def expand(match): return ' ' * int(match.group(0))

   fen[0] = re.compile(r'\d').sub(expand, fen[0])
   table = [map(pieces.piece,list(row)) for row in fen[0].split('/')]
   table.reverse()
   if fen[1] == 'w': player_turn = pieces.COLORS['white']
   else: player_turn = pieces.COLORS['black']
   castling = fen[2]
   en_passant = fen[3]
   halfmove_clock = int(fen[4])
   fullmove_number = int(fen[5])

def export():
   ''' Export state to FEN notation '''
   def join(k, g):
      if k == ' ': return str(len(g))
      else: return "".join(g)

   def stringify(row):
    result = ''
    for piece in row:
      if piece is not None:
         result += piece.abbriviate()
      else: result += ' '
    # replace spaces with their count
    result = [join(k, list(g)) for k,g in groupby(result)]
    return "".join(result)

   if player_turn == 0: turn = 'w'
   else: turn = 'b'

   result = "/".join([stringify(row) for row in table][::-1])
   result +=  " " + turn +\
              " " + castling +\
              " " + en_passant +\
              " " + str(halfmove_clock) +\
              " " + str(fullmove_number)
   return result

def letter_notation(coord):
  if not is_in_bounds(coord):
     raise InvalidCoord

  try:
   return axis_y[coord[1]] + str(axis_x[coord[0]])
  except IndexError:
   raise InvalidCoord
