
import math
from random import randint

# Board dimensions and ship description
large_w = 5
large_h = 5
large_shipdescr = (2,3,4)

# Actual Battleship dimensions (extremely complex)
battleship_w = 10
battleship_h = 10
battleship_shipdescr = (2,3,3,4,5)

# Number of boards to skip when evaluating performance
subsample = 10

# Affects output logging
verbose = True
extra_verbose = False

class game:
	
	'''
	One instance of a Battleship game 
	'''
	
	def __init__(self, w, h, shipdescr, ships, bf, strategy=0):
		# dimensions and ships
		self.w = w
		self.h = h
		self.shipdescr = shipdescr
		
		# "actual" board being guessed
		self.ships = ships
		
		# trace of guesses
		self.trace = {}
		
		# board factory object 
		self.bf = bf
		
		# initial candidate boards (very large)
		self.candidate_boards = bf.default_boards
		
		# strategy (see get_best_guess())
		self.strategy = strategy
		
		# antitrace equivalent to beliefs about the board space
		self.antitrace = {}
		
		# create and fill with initial beliefs
		self.update_antitrace()

	def test_hit(self, coord):
		'''
		Reveal whether guess is a hit
		'''
		return coord in self.ships
		
	def real_hit(self, coord):
		'''
		Make a guess; update trace; filter candidates by new information
		'''
		self.trace[coord] = self.test_hit(coord)
		self.candidate_boards = self.filter_boards_by_guess(coord, self.trace[coord])
		self.update_antitrace()

	def num_satisfying_boards(self):
		return len(self.candidate_boards)
		
	def filter_boards_by_guess(self, coord, success):
		return list(filter(
			lambda cb : self.bf.board_satisfies_trace(cb,{coord : success}), 
			self.candidate_boards))

	def guess_data(self, coord):
		'''
		calculate proportions of hits and misses
		'''
		n = self.num_satisfying_boards()
		n_hits = len(self.filter_boards_by_guess(coord,True))
		n_misses = n - n_hits
		return (n, n_hits, n_misses)
		
	def guess_chance(self, coord):
		'''
		Return an integer (0 <= x <= 100) percentage chance of hit at coord
		'''
		n, n_hits, n_misses = self.guess_data(coord)
		pct = int((n_hits / n) * 100)
		return pct
	
	def update_antitrace(self):
		'''
		fill antitrace with guess probabilities
		'''
		for g in [c for c in range(self.w * self.h)]:
			self.antitrace[g] = self.guess_chance(g)
			
	def get_best_guess(self):
		'''
		Strategy function which returns a guess
		By default (via constructor) returns coord with closest hit% to 50
		'''
		if self.strategy==0:
			# Default strategy: hit% closest to 50
			best_g = -1
			best_q = 50
			for g,p in self.antitrace.items():
				quality = abs(p - 50)
				if quality < best_q:
					best_q = quality
					best_g = g
			return best_g
			
		elif self.strategy==1:
			# Comparison strategy: hit% highest
			best_g = -1
			best_q = -1
			for g,p in self.antitrace.items():
				quality = p
				if quality > best_q and quality < 100:
					best_q = quality
					best_g = g
			return best_g
			
		elif self.strategy==2:
			# Guess a random square not yet guessed
			squares = [g for g,p in self.antitrace.items() 
								if g not in self.trace.keys()]
			return squares[randint(0,len(squares)-1)]
			
		else:
			print("Incompatible strategy, try again...")
		
	def detect_il_win(self):
		'''
		True if all squares have known (deduced) contents
		'''
		for g,p in self.antitrace.items():
			if p > 0 and p < 100:
				return False
		return True
		
	def detect_hit_win(self):
		'''
		True if all ships have been destroyed
		'''
		return (sum(self.shipdescr) 
			== len([i for i in self.trace.items() if i[1]]))
		
	def autoplay(self):
		'''
		Loops making guesses and adjusting beliefs until win condition
		'''
		guesses=0
		while not (self.detect_il_win() or self.detect_hit_win()):
			self.real_hit(self.get_best_guess())
			guesses+=1
		if extra_verbose:
			self.show_board_beliefs()
			print(f'Guesses = {guesses}')
		return guesses
	
	def show_board_beliefs(self):
		'''
		Print a board with beliefs
		'''
		
		best_guess = self.get_best_guess()
		
		i = 0
		while (i < self.w):
			print("__"+str(i)+"__", end="")
			i+= 1
		print()
		
		i = 0 
		
		while (i < self.w * self.h):
			printchar = "  ?  "
			if i in self.trace.keys():
				if self.trace[i]:
					printchar="  X  "
				else:
					printchar="  O  "
			else:
				pct = self.antitrace[i]
				if i != best_guess:
					printchar=f' {pct:3d} '
				else:
					printchar=f'>{pct:3d}<'
					
			print(printchar,end="")
			if i % self.w == self.w - 1:
				print(f'| {math.floor(i/self.w)}')
			i += 1
		i=0
		while (i < self.w):
			print("-----",end="")
			i += 1
		print()
		
		print("Best guess:", best_guess)
			
		
		
		
		
	
def db(dbstr):
	if (verbose):
		print("---", dbstr)



class board_factory:
	
	def __init__(self,w,h,shipdescr):
		
		self.w = w
		self.h = h
		self.shipdescr = shipdescr
		self.default_boards = self.get_all_boards_from_shipdescr(
			self.shipdescr)
		
	def show_board(self, board):
		'''
		Print a board (for debugging)
		'''
		i = 0
		while (i < self.w):
			print("_"+str(i)+"_", end="")
			i+= 1
		print()
		i = 0 
		while (i < self.w * self.h):
			hit=False
			root=False
			if i in board:
				hit=True
			if ((i + 1) % self.w == 0):
				if hit:
					print(" o |",(math.floor(i/self.w)))
				else:
					print(" ~ |",(math.floor(i/self.w)))
			elif hit:
				print(" o ", end="")
			else:
				print(" ~ ", end="")
			i += 1
		i=0
		while (i < self.w):
			print("---",end="")
			i += 1
		print()
		print()
		
	def xy_to_coord(self, t):
		return (t[1] * self.h) + t[0]
		
	def coord_to_xy(self, coord):
		x = coord % self.w
		y = math.floor(coord / self.w)
		return (x,y)
	
	def evaluate_placement(self, ship, board, root, direction, trace={}):
		'''
		Return true if the placement is valid; in-bounds and not colliding
		'''
		
		if ( root > self.w * self.h - 1 ):
			# db("Out of bounds completely")
			return False
		if ( self.coord_to_xy(root)[1] != self.coord_to_xy(root+ship-1)[1] 
			and direction==0 ):
			# db("Out of x bounds")
			return False
		if ( self.coord_to_xy(root + (self.w * (ship-1)))[1] > self.h - 1 
			and direction==1 ):
			# db("Out of y bounds")
			return False
		
		for i in range(0,ship):
			if direction==0:
				coord = root + i
			elif direction==1:
				coord = root + (i * self.w)
			else:
				# db("Invalid direction")
				return False
			
			if coord in trace.keys() and not trace[coord]:
				# db("Trace contradiction")
				return False
			
			if coord in board:
					# db(f'Ship collided with {b}')
				return False
		
		# db("No issues, ship OK")
		return True
		
	
	def find_all_fits(self, ship, board, trace={}):
		'''
		Given a board and a ship, return all positions where it is 
		feasible to add the ship
		'''
		fits = []
		for r in range(0, self.w * self.h):
			for d in (0,1):
				if self.evaluate_placement(ship, board, r, d, trace):
					fits.append((r,d))
		return fits


	def board_repr(self, root, ship, direction):
		'''
		Given a root, length, dir, return an array of coordinate positions
		'''
		if direction==0:
			return [root + i for i in range(0,ship)]
		if direction==1:
			return [root + (i * self.w) for i in range(0,ship)]
			
	def add_to_board(self, bship, board):
		return board + bship
			
	def get_all_resulting_boards(self, ship, board, trace={}):
		'''
		Accepts a ship and a board
		Returns a list of boards which are possible placements for the ship
		'''
		
		boards = []
		
		for f in self.find_all_fits(ship, board, trace):
			bship = self.board_repr( f[0], ship, f[1] )
			boards += [self.add_to_board(bship, board)]
		
		# db(f'{len(boards)} boards generated.')
		
		return boards
		
	def get_all_boards_from_shipdescr(self, shipdescr, trace={}):
		
		boards = [[]]
		
		for s in shipdescr:
			boards_new = []
			
			for b in boards:
				boards_new += self.get_all_resulting_boards(s,b,trace)
				
			boards = boards_new
			
		return boards
		
		
	def get_all_boards_from_trace(self, shipdescr, trace={}):
		
		boards = self.get_all_boards_from_shipdescr(shipdescr,trace)
		sat_boards = []
		for b in boards:
			if self.board_satisfies_trace(b, trace):
				sat_boards += [b]
		return sat_boards


	def board_satisfies_trace(self, board, trace):
		
		# print("Boardsat")
		
		for c,v in trace.items():
			
			# Test if miss is satisfied; possibly spurious, to investigate
			if not v:
				if c in board:
					return False
						
			# Test if hit is satisfied
			else:
				if c not in board:
					return False
		
		return True
		
		
		
def test(width,height,shipdescr,coverage_pct=50, randomise=False, strategy=0):

	bf = board_factory(width,height,shipdescr)
	print(f'Generating with w={width},h={height},ships={shipdescr},'
		+f'coverage={coverage_pct}%,rand={randomise},strat={strategy}')
	all_boards = bf.get_all_boards_from_shipdescr(shipdescr)
	num_boards = len(all_boards)
	print(f'{num_boards} boards generated. '
		+f'{int(num_boards * (coverage_pct/100))} to test.')
	performance_list = []
	subsample = int(100 / coverage_pct)

	for i in range(0,num_boards,subsample):
		print(f'Evaluating board {i:>8d}...',end="")
		
		if randomise:
			i = randint(0,num_boards-1)
			
		try:
			b = all_boards[i]
			the_game = game(width,height,shipdescr,b,bf,strategy)
			perf = the_game.autoplay()
			performance_list.append(perf)
			print(f'({perf:>2d})')
			i += 1
		
		except KeyboardInterrupt:
			print("Terminated by user.")
			break
		except IndexError:
			print("IndexError resulted from board number ",i)
			break
	
	print("Mean number of guesses:", 
		round((sum(performance_list)/len(performance_list)),2))






















