# Import python libraries
import sys
import copy
import random as rnd

# Import our own files
import config as cfg					# Experiment Configuration
import placeit_helpers as hlp			# Helpers 
import highspeed_proxies as hspx		# Performance proxies
from chiplet import Chiplet				# Chiplet-Class
from placement import Placement			# Placement-Class

# Placement Representation for Heterogeneous Chiplets
class HeteroPlacement:	

	# Constructor
	def __init__(self, params, types = None, rotations = None):
		self.params = params
		self.placement = None
		# Parameterized initialization: This can result in an invalid placement
		if types != None and rotations != None:
			self.types = types
			self.rotations = rotations
			network = self.get_network()
			self.is_valid = network.validate()
			self.hash = self.compute_hash()
			self.cost = float("NaN")
			if self.is_valid:
				(cost, evaluation) = hspx.compute_highspeed_proxies(self.get_area(), network, params)
				self.cost = cost
				self.eval = evaluation
		# Random Initialization: Always produces a valid placement
		else:
			n_compute = params["n_compute"]	
			n_memory = params["n_memory"]	
			n_io = params["n_io"]	
			valid = False
			# Randomly generate placements until a valid one was found
			while not valid:
				self.placement = None
				types = ["C"] * n_compute + ["M"] * n_memory + ["I"] * n_io
				rnd.shuffle(types)		
				rotations = []
				for typ in types:
					rb = params["rotation_behaviour"][typ]
					valid_rotations = [0]
					if rb == "hybrid":
						valid_rotations += [90]
					if rb == "sensitive":
						valid_rotations += [90,180,270]
					rotations.append(rnd.choice(valid_rotations))
				self.types = types	
				self.rotations = rotations
				network = self.get_network()	
				valid = network.validate()
			self.valid = valid
			(cost, evaluation) = hspx.compute_highspeed_proxies(self.get_area(), network, params)
			self.cost = cost
			self.eval = evaluation
			self.origin = "random"
			self.hash = self.compute_hash()
			
	# Construct and return a placement based on this placement representation 
	def construct_placement(self):
		# Initialize grid
		rows = 1
		cols = 1
		grid = [["x","x","x"],["x", " "," "],["x", " "," "]]
		chiplets = []
		# Iterate through the chiplets
		for (i, (typ, rot)) in enumerate(zip(self.types, self.rotations)):
			# Construct chiplet with wrong location, rotate it and extract size from it 
			chiplet = Chiplet((0, 0), self.params["dimensions"][typ], typ, self.params["phys"][typ])
			chiplet.rotate(rot)
			(w,h) = chiplet.size
			# Find Candidate corners
			cand_corners = []
			for r in range(1,rows+1,1):
				for c in range(1,cols+1,1):
					if grid[r-1][c] == "x" and grid[r][c-1] == "x" and grid[r][c] == " ":
						cand_corners.append((r,c))							
			# Only keep corners that are either free to the top or right
			corners = []
			for (r,c) in cand_corners:
				topfree = sum([0 if grid[rr][c] == " " else 1 for rr in range(r, rows+1,1)]) == 0
				rightfree = sum([0 if grid[r][cc] == " " else 1 for cc in range(c, cols+1,1)]) == 0
				if topfree or rightfree:
					corners.append((r,c))
			# Find the corner with longest distance to square-perimeter	
			max_dist = -1 * float("inf")
			selected_corner = None
			square_size = max(rows, cols)
			for (r,c) in corners:
				dist = min(square_size - r, square_size - c)
				if dist > max_dist:
					max_dist = dist
					selected_corner = (r,c)
			row, col = selected_corner
			# Check if the chiplet can be placed at the corner, if not, move the chiplet
			top_free = sum([0 if grid[rr][col] == " " else 1 for rr in range(row, rows+1,1)]) == 0
			right_free = sum([0 if grid[row][cc] == " " else 1 for cc in range(col, cols+1,1)]) == 0
			collision = sum([1 if grid[rr][cc] == "x" else 0 for rr in range(row, min(row+h, rows+2), 1) for cc in range(col, min(col+w, cols+2), 1)]) > 0
			while right_free and collision:
				col += 1
				collision = sum([1 if grid[rr][cc] == "x" else 0 for rr in range(row, min(row+h, rows+2), 1) for cc in range(col, min(col+w, cols+2), 1)]) > 0
			while top_free and collision:
				row += 1
				collision = sum([1 if grid[rr][cc] == "x" else 0 for rr in range(row, min(row+h, rows+2), 1) for cc in range(col, min(col+w, cols+2), 1)]) > 0
			# Enlarge grid if necessary
			rows_missing = row + h - rows
			cols_missing = col + w - cols
			if rows_missing > 0:
				for j in range(rows_missing):
					grid.append(["x"] + [" " for k in range(cols + 1)])
				rows += rows_missing
			if cols_missing > 0:
				for j in range(rows+2):
					grid[j] += ([" " for k in range(cols_missing)] if j > 0 else ["x" for k in range(cols_missing)])
				cols += cols_missing
			# Add chiplet to placement and to grid
			chiplet.move_to((col, row))
			chiplets.append(chiplet)
			for r in range(row, row + h, 1):
				for c in range(col, col + w, 1):
					grid[r][c] = "x"
		# Create and return placement:	
		self.placement = Placement(self.params, chiplets)

	# Construct placement if not yet done and return it.
	def get_placement(self):
		if self.placement == None:
			self.construct_placement()
		return self.placement
			
	# Translate the placement to json
	def to_json(self):
		json = {
			"types" : self.types,
			"rotations" : self.rotations,
			"cost" : self.cost,
			"eval" : self.eval,
		}
		return json

	# Visualize the placement 
	def visualize(self, fig_name = None):
		self.get_placement().visualize(fig_name)

	# Return the network topology
	def get_network(self):
		return self.get_placement().get_network()

	# Return the total area
	def get_area(self):
		return self.get_placement().get_area()

	# Perform a mutation
	def mutate(self):
		tmp = [self.params["rotation_behaviour"][typ] for typ in self.types]
		can_rotate = (tmp.count("sensitive") + tmp.count("hybrid")) > 0
		bias = self.params["mutation_bias"]
		n = len(self.types)
		valid = False
		while not valid:
			new_types = copy.deepcopy(self.types)
			new_rotations = copy.deepcopy(self.rotations)
			rand_num = rnd.random()
			# Swap chiplets
			if "both" in self.params["mutation_mode"] or (rand_num >= bias) or (not can_rotate):
				if "any" in self.params["mutation_mode"]:
					idx1 = rnd.choice(list(range(n))) 
					idx2 = rnd.choice([x for x in range(n) if new_types[x] != new_types[idx1]])
				elif "neighbors" in self.params["mutation_mode"]:
					(idx1, idx2) = rnd.choice([(i,i+1) for i in range(n-1) if new_types[i] != new_types[i+1]])
				else:
					print("ERROR: Invalid mutation mode: \"%s\"" % self.params["mutation_mode"])
					sys.exit()
				tmp_type = new_types[idx1]
				new_types[idx1] = new_types[idx2]
				new_types[idx2] = tmp_type
				tmp_rot = new_rotations[idx1]
				new_rotations[idx1] = new_rotations[idx2]
				new_rotations[idx2] = tmp_rot
			# Rotate chiplet
			if ("both" in self.params["mutation_mode"] or (rand_num < bias)) and can_rotate:
				# Select which chiplet to rotate
				idx = rnd.choice([x for x in range(n) if self.params["rotation_behaviour"][new_types[x]] != "invariant"])
				# Create list of valid rotations
				valid_rotations = [0,90] if self.params["rotation_behaviour"][new_types[idx]] == "hybrid" else [0,90,180,270]
				if new_rotations[idx] in valid_rotations:
					valid_rotations.remove(new_rotations[idx])
				new_rotations[idx] = rnd.choice(valid_rotations)
			mutant = HeteroPlacement(self.params, new_types, new_rotations)	
			valid = mutant.is_valid
		mutant.origin = "mutate"
		return mutant

	# Merge two placement
	def merge(self, other):
		n = len(self.types)	
		tmp_types = [None for i in range(n)]
		tmp_rotations = [None for i in range(n)]
		# Set locations that match in this and the other placement
		for i in range(n):
			if self.types[i] == other.types[i]:
				tmp_types[i] = self.types[i]
			if self.rotations[i] == other.rotations[i]:
				tmp_rotations[i] = self.rotations[i]
		# Randomly set the remaining locations - repeat until the resulting placement is valid
		valid = False
		while not valid:
			new_types = copy.deepcopy(tmp_types)
			new_rotations = copy.deepcopy(tmp_rotations)
			n_comp_missing = self.types.count("C") - new_types.count("C")
			n_mem_missing = self.types.count("M") - new_types.count("M")
			n_io_missing = self.types.count("I") - new_types.count("I")
			to_place = n_comp_missing * ["C"] + n_mem_missing * ["M"] + n_io_missing * ["I"]
			rnd.shuffle(to_place)
			for i in range(n):
				if new_types[i] == None:
					new_types[i] = to_place.pop()
				if new_rotations[i] == None:
					valid_rotations = [0]
					if self.params["rotation_behaviour"][new_types[i]] == "hybrid":
						valid_rotations += [90]
					elif self.params["rotation_behaviour"][new_types[i]] == "sensitive": 
						valid_rotations += [90,180,270]
					new_rotations[i] = rnd.choice(valid_rotations)
			# Sanity Check
			if len(to_place) > 0:
				print("ERROR: Merging of Placements seems to contain a Bug: Not all chiplets have been placed")
				sys.exit()
			merger = HeteroPlacement(self.params, new_types, new_rotations)	
			valid = merger.is_valid
		merger.origin = "merge"
		return merger

	# Compute a unique hash of this placement
	def compute_hash(self):
		return "".join([self.types[i] + str(int(self.rotations[i] // 90)) for i in range(min(len(self.types), len(self.rotations)))])

	# Export this placement to RapidChiplet
	def export(self, path, algo):
		return self.get_placement().export(path, algo)

