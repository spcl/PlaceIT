# Import python libraries
import sys
import copy
import random as rnd
import matplotlib.pyplot as plt

# Import our own files
import config as cfg
import placeit_helpers as hlp
import highspeed_proxies as hspx	# Our implementation of the performance proxies from RapidChiplet
from network import Network

# Placement representation for homogeneous chiplets
class HomoPlacement:
	# If no grid is passed, initialize a random grid
	# Grid: 2D-array with entries C, M, I, (compute, memory, io) or X (no chiplet)
	# PHYs: 2D-array with entries A (phys of four sides) or N,E,S,W (north, east, south, west)
	def __init__(self, params, grid = None, phys = None):
		self.params = params
		# Parameterized initialization: This can create an invalid placement
		if grid != None and phys != None:
			self.grid = grid
			self.phys= phys
			network = self.get_network()
			valid = network.validate()
			self.is_valid = valid
			self.hash = self.compute_hash()
			if valid:
				(cost, evaluation) = hspx.compute_highspeed_proxies(self.get_area(), network, params)
				self.cost = cost
				self.eval = evaluation
		# Random initialization: This always produces a valid placement
		else:
			# Gather information
			rows = params["rows"]
			cols = params["cols"]
			n_compute = params["n_compute"]
			n_memory = params["n_memory"]
			n_io = params["n_io"]
			relay_types = params["relay_chiplets"]
			# Check if parameters are valid
			if n_compute + n_memory + n_io > rows * cols:	
				print("ERROR: Too many chiplet for given size")
			# Continue generating random placements until one is valid
			valid = False
			while not valid:
				# Construct an empty grid
				self.grid = [["X" for col in range(cols)] for row in range(rows)]	
				empty_pos = [(row,col) for row in range(rows) for col in range(cols)]	
				# Randomly place IO chiplets
				for i in range(n_io):
					pos = empty_pos.pop(rnd.randrange(len(empty_pos)))		
					self.grid[pos[0]][pos[1]] = "I"
				# Randomly place memory chiplets
				for i in range(n_memory):
					pos = empty_pos.pop(rnd.randrange(len(empty_pos)))		
					self.grid[pos[0]][pos[1]] = "M"
				# Randomly place compute chiplets
				for i in range(n_compute):
					pos = empty_pos.pop(rnd.randrange(len(empty_pos)))		
					self.grid[pos[0]][pos[1]] = "C"
				# Randomly determine rotation of each chiplet (on which side is the PHY for 1-PHY chiplets?)
				self.phys= [["X" for col in range(cols)] for row in range(rows)]	
				for row in range(rows):
					for col in range(cols):
						if self.grid[row][col] == "X":
							continue
						if len(self.params["phys"][self.grid[row][col]]) == 4:
							self.phys[row][col] = "A"
						elif len(self.params["phys"][self.grid[row][col]]) == 1:
							valid_choices = ["N","E","S","W"]
							if row == 0:
								valid_choices.remove("S")
							if row == (rows-1):
								valid_choices.remove("N")
							if col == 0:
								valid_choices.remove("W")
							if col == (cols-1):
								valid_choices.remove("E")
							self.phys[row][col] = rnd.choice(valid_choices)
						else:
							print("ERROR: Chiplets in the homogeneous placement can only have 1 or four PHYs")
							sys.exit()
				network = self.get_network()
				valid = network.validate()
			# Once a valid grid was found: Compute its cost and store it
			self.is_valid = valid
			(cost, evaluation) = hspx.compute_highspeed_proxies(self.get_area(), network, params)
			self.cost = cost
			self.eval = evaluation
			self.origin = "random"
			self.hash = self.compute_hash()

	# Store grid as JSON
	def to_json(self):
		json = {
			"grid" : self.grid,
			"phys" : self.phys,
			"cost" : self.cost,
			"eval" : self.eval,
		}
		return json

	# Create a visualization of the placement
	def visualize(self, fig_name = "homogeneous_placement"):
		# Fetch data
		grid = self.grid
		phys = self.phys
		rows = len(self.grid)
		cols = len(self.grid[0])

		# Create plot
		(fig, ax) = plt.subplots(1, 1, figsize = (3, 3 * rows / cols))
		plt.subplots_adjust(left=0.01, right = 0.99, top = 0.99, bottom = 0.0)
		for row in range(rows):
			for col in range(cols):
				if self.grid[row][col] != "X":
					# Plot Chiplet	
					c = cfg.plotting_color_map[self.grid[row][col]]
					rectangle = plt.Rectangle((col+0.03,row+0.03), 0.94, 0.94, fc = c, fill = True, alpha = 1.0)
					ax.add_patch(rectangle)
					ax.text(col + 0.5, row + 0.5, grid[row][col], ha = "center", va = "center", fontweight = "bold", fontsize = 6)
					# Plot PHYs
					tmp = {"A" : [(0.15,0.5),(0.85,0.5),(0.5,0.15),(0.5,0.85)], "N" : [(0.5,0.85)], "E" : [(0.85,0.5)], "S" : [(0.5,0.15)], "W" : [(0.15,0.5)]}
					for (px,py) in tmp[self.phys[row][col]]:	
						circ = plt.Circle((col + px, row + py), 0.1, fc = cfg.plotting_color_map["phy"], fill = True, zorder = 3, edgecolor = "#666666")
						ax.add_patch(circ)
					# Plot link to right
					if col < (cols - 1) and grid[row][col] != "D" and grid[row][col+1] != "D" and phys[row][col] in ["A","E"] and phys[row][col+1] in ["A","W"]:
						ax.arrow(col + 0.95, row + 0.5, 0.15, 0, zorder = 5, color = cfg.plotting_color_map["link"],length_includes_head=True, head_width = 0.0, head_length = 0.0, linewidth = 4)
						ax.arrow(col + 1.05, row + 0.5, -0.15, 0, zorder = 5, color = cfg.plotting_color_map["link"],length_includes_head=True, head_width = 0.0, head_length = 0.0, linewidth = 4)
					# Plot link to top
					if row < (rows - 1) and grid[row][col] != "D" and grid[row+1][col] != "D" and phys[row][col] in ["A","N"] and phys[row+1][col] in ["A","S"]:
						ax.arrow(col + 0.5, row + 0.95, 0, 0.15, zorder = 5, color = cfg.plotting_color_map["link"],length_includes_head=True, head_width = 0.0, head_length = 0.0, linewidth = 4)
						ax.arrow(col + 0.5, row + 1.05, 0, -0.15, zorder = 5, color = cfg.plotting_color_map["link"],length_includes_head=True, head_width = 0.0, head_length = 0.0, linewidth = 4)
		# More plotting config
		ax.axis('off')
		plt.gca().set_aspect('equal')
		ax.set_xlim(-0.01, cols+0.02)
		ax.set_ylim(-0.01, rows+0.02)
		ax.set_xticks([])
		ax.set_yticks([])
		# Save the plot
		plt.savefig("plots/" + fig_name + ".pdf")

	# Extract the network topology from the placement
	def get_network(self):
		# Gather data
		grid = self.grid
		phys = self.phys
		rows = len(grid)
		cols = len(grid[0])
		# Initialize variables to store network
		n = sum([(1 if grid[r][c] in ["C","M","I"] else 0) for r in range(rows) for c in range(cols)])
		pos_to_cid = {}
		node_types = []
		neighbors = [[] for i in range(n)]
		phy_map = [[] for i in range(n)]
		# Iterate through chiplets
		for row in range(rows):
			for col in range(cols):
				if grid[row][col] in ["C","M","I"]:
					# Add vertex (chiplet)
					cid = len(node_types)
					pos_to_cid[(row,col)] = cid
					node_types.append(grid[row][col])
					# Add edge (link to right)
					if col > 0 and grid[row][col] != "X" and grid[row][col-1] != "X" and phys[row][col] in ["A","W"] and phys[row][col-1] in ["A","E"]:
						phy1 = 0 if phys[row][col] == "W" else 3
						phy2 = 0 if phys[row][col-1] == "E" else 1
						ocid = pos_to_cid[(row,col-1)]
						neighbors[cid].append(ocid)
						phy_map[cid].append((phy1, phy2))
						neighbors[ocid].append(cid)
						phy_map[ocid].append((phy2, phy1))
					# Add edge (link to top)
					if row > 0 and grid[row][col] != "X" and grid[row-1][col] != "X" and phys[row][col] in ["A","S"] and phys[row-1][col] in ["A","N"]:
						phy1 = 0 if phys[row][col] == "S" else 2
						phy2 = 0 if phys[row-1][col] == "N" else 0
						ocid = pos_to_cid[(row-1,col)]
						neighbors[cid].append(ocid)
						phy_map[cid].append((phy1, phy2))
						neighbors[ocid].append(cid)
						phy_map[ocid].append((phy2, phy1))
		# Create and return network
		return Network(n, node_types, neighbors, phy_map, self.params["relay_chiplets"])

	# Return the area
	def get_area(self):
		return self.params["dimensions"]["C"][0] * self.params["dimensions"]["C"][1] * self.params["rows"] * self.params["cols"]

	# Perform a random mutation of the placement
	def mutate(self):
		# Gather data
		bias = self.params["mutation_bias"]
		rows = len(self.grid)
		cols = len(self.grid[0])
		grid = self.grid
		phys = self.phys
		valid = False
		# Perform random mutations until a valid placement is achieved
		while not valid:
			rand_num = rnd.random()
			new_grid = copy.deepcopy(grid)
			new_phys = copy.deepcopy(phys)
			can_rotate = sum([sum([(1 if (x in ["N","E","S","W"]) else 0) for x in y]) for y in self.phys]) > 0
			# Swap Chiplets 
			if "both" in self.params["mutation_mode"] or (rand_num >= bias) or (not can_rotate):
				if "any" in self.params["mutation_mode"]:
					# Select first chiplet to swap
					r1 = rnd.randint(0, rows-1)
					c1 = rnd.randint(0, cols-1)
					typ1 = grid[r1][c1]
					# Select second chiplet to swap: This has to be a different type than the first one
					candidates = [(r,c) for r in range(rows) for c in range(cols) if grid[r][c] != typ1]
					(r2,c2) = rnd.choice(candidates)
					typ2 = grid[r2][c2]
				elif "neighbors" in self.params["mutation_mode"]:
					# Construct list of valid swapping pairs: 
					candidates = []
					for r in range(rows-1):
						for c in range(cols-1):
							if grid[r][c] != grid[r+1][c]:
								candidates.append(((r,c),(r+1,c)))
							if grid[r][c] != grid[r][c+1]:
								candidates.append(((r,c),(r,c+1)))
					((r1,c1),(r2,c2)) = rnd.choice(candidates)
					(typ1, typ2) = (grid[r1][c1],grid[r2][c2])
				else:
					print("ERROR: Invalid mutation mode: \"%s\"" % self.params["mutation_mode"])
					sys.exit()
				# Perform the swap
				new_grid[r1][c1] = typ2
				new_grid[r2][c2] = typ1
				tmp = new_phys[r1][c1]
				new_phys[r1][c1] = new_phys[r2][c2]
				new_phys[r2][c2] = tmp
			# Rotate Chiplet
			if ("both" in self.params["mutation_mode"] or (rand_num < bias)) and can_rotate:
				valid_locations = [(row,col) for row in range(rows) for col in range(cols) if phys[row][col] not in ["X","A"]]
				(row, col) = rnd.choice(valid_locations)
				valid_choices = ["N","E","S","W"]
				# Make sure the singly PHY doesn't face outside
				if row == 0:
					valid_choices.remove("S")
				if row == (rows-1):
					valid_choices.remove("N")
				if col == 0:
					valid_choices.remove("W")
				if col == (cols-1):
					valid_choices.remove("E")
				# Make sure we actually rotate the chiplet
				if phys[row][col] in valid_choices:
					valid_choices.remove(phys[row][col])
				# Perform the rotation
				new_phys[row][col] = rnd.choice(valid_choices)
			# Construct mutated object
			mutant = HomoPlacement(self.params, new_grid, new_phys)
			valid = mutant.is_valid
		mutant.origin = "mutate"
		return mutant

	# Merge two placements into a third one	
	def merge(self, other):
		# Gather data
		grid1 = self.grid
		grid2 = other.grid
		phys1 = self.phys
		phys2 = other.phys
		rows = len(grid1)
		cols = len(grid1[0])
		# Initialize the new, merged placement
		grid = [[None for i in range(cols)] for j in range(rows)]
		phys = [[None for i in range(cols)] for j in range(rows)]
		# Construct list of chiplets to be placed
		to_place = {"C" : self.params["n_compute"], 
					"M" : self.params["n_memory"], 
					"I" : self.params["n_io"], 
					"X" : rows * cols - self.params["n_compute"] - self.params["n_memory"] - self.params["n_io"]}
		# Pass 1: If a location matches in both placements, the merged placement contains the same thing at that location 
		for row in range(rows):
			for col in range(cols):
				if grid1[row][col] == grid2[row][col]:
					typ = grid1[row][col]
					grid[row][col] = typ
					to_place[typ] -= 1
					# Only set the rotation if the type was matching
					if phys1[row][col] == phys2[row][col]:
						phys[row][col] = phys1[row][col]
		# Pass 2: Place remaining chiplets: 50/50 chance from which parent it is selected, repeat until valid
		valid = False
		while not valid:
			# Phase 2 - Step 1: Complete the grid, copy rotation if possible
			new_grid = copy.deepcopy(grid)
			new_phys = copy.deepcopy(phys)
			to_place_tmp = copy.deepcopy(to_place)
			for row in range(rows):
				for col in range(cols):
					if new_grid[row][col] == None:
						typ1 = grid1[row][col]
						typ2 = grid2[row][col]
						if rnd.random() < 0.5 and to_place_tmp[typ1] > 0:
							new_grid[row][col] = typ1
							to_place_tmp[typ1] -= 1
							new_phys[row][col] = phys1[row][col]
						elif to_place_tmp[typ2] > 0:
							new_grid[row][col] = typ2
							to_place_tmp[typ2] -= 1
							new_phys[row][col] = phys2[row][col]
						elif sum(list(to_place_tmp.values())) > 0:
							typ = rnd.choices(list(to_place_tmp.keys()), [x / sum(list(to_place_tmp.values())) for x in to_place_tmp.values()], k=1)[0]
							new_grid[row][col] = typ
							to_place_tmp[typ] -= 1
						else:
							print("ERROR: Unable to merge two placements")
							sys.exit()
			# Phase 2 - Step 1: Complete the phys once the grid is complete 
			for row in range(rows):
				for col in range(cols):
					if new_phys[row][col] == None:
						if new_grid[row][col] == "X":
							new_phys[row][col] = "X"
						elif len(self.params["phys"][new_grid[row][col]]) == 4:
							new_phys[row][col] = "A"
						else:
							valid_choices = ["N","E","S","W"]
							# Make sure the singly PHY doesn't face outside
							if row == 0:
								valid_choices.remove("S")
							if row == (rows-1):
								valid_choices.remove("N")
							if col == 0:
								valid_choices.remove("W")
							if col == (cols-1):
								valid_choices.remove("E")
							new_phys[row][col] = rnd.choice(valid_choices)
			merger = HomoPlacement(self.params, new_grid, new_phys)
			valid = merger.is_valid
		merger.origin = "merge"
		return merger	

	# Compute a unique hash function
	def compute_hash(self):
		rows = len(self.grid)
		cols = len(self.grid[0])
		return "".join([(self.grid[row][col] + self.phys[row][col]) for row in range(rows) for col in range(cols)])

	# Export this placement to the RapidChiplet toolchain
	def export(self, path, algo):
		# Gather data
		rows = len(self.grid)
		cols = len(self.grid[0])

		# Store the "chiplet_placement" file that RapidChiplet uses as an input
		placement = {"chiplets" : [], "interposer_routers" : []}
		for row in range(rows):
			for col in range(cols):
				if self.grid[row][col] in ["C","M","I"]:
					typ = self.grid[row][col]
					ori = {"A" : 0, "E" : 0, "S" : 270, "W" : 180, "N" : 90}[self.phys[row][col]]
					chiplet = {
						"position" 	: {"x" : col * self.params["dimensions"][typ][0], "y" : row * self.params["dimensions"][typ][1]},
						"rotation"	: ori,
						"name" 		: typ,
					}
					placement["chiplets"].append(chiplet)
		# Write file to file system
		hlp.write_file("%s/chiplet_placements/placement_%s_%s.json" % (path, self.params["experiment"], algo), placement)

				
					
