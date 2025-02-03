# Import python libraries
import sys
import copy
import math
import queue
import random as rnd
import matplotlib.pyplot as plt

# Import our own files 
import config as cfg
import placeit_helpers as hlp
import highspeed_proxies as hspx
from representation_homo import HomoPlacement
from chiplet import Chiplet
from network import Network 

# Returns the distance between two positions on the chip
def get_dist(pos1, pos2, typ):
	if typ == "euclidean":
		return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1] - pos2[1])**2)
	elif typ == "manhattan":
		return abs(pos1[0]-pos2[0]) + abs(pos1[1] - pos2[1])
	else:
		print("ERROR: Invalid distance type: \"%s\"" % str(typ))
		sys.exit()

# Swap two chiplets
def swap_chiplets(c1, c2):
	pos1 = copy.deepcopy(c1.pos)
	pos2 = copy.deepcopy(c2.pos)
	c1.move_to(pos2)
	c2.move_to(pos1)

# The "placement" is the underlying data structure of the HeteroPlacement
class Placement:	
	# Create a new placement
	def __init__(self, params, chiplets):	
		self.params = params	
		self.chiplets = chiplets
		self.update_placement_size()
		network = self.get_network()
		valid = network.validate()
		self.is_valid = valid
		if valid:
			(cost, evaluation) = hspx.compute_highspeed_proxies(self.get_area(), network, params)
			self.cost = cost
			self.eval = evaluation
	
	# Store the placement as JSON
	def to_json(self):
		json = {
			"size" : self.size,
			"chiplets" : [c.to_json() for c in self.chiplets],
			"cost" : self.cost,
			"eval" : self.eval,
		}
		return json

	# Visualize the current placement
	def visualize(self, fig_name = "placement"):
		# Extract network topology
		(nw_success, nw_error, neighbors) = self.get_network_internal()
		# Set up plot
		(fig, ax) = plt.subplots(1,1, figsize = (5,5))
		plt.subplots_adjust(left=0.01, right = 0.99, top = 0.99, bottom = 0.01)
		# Axis and stuff
		plt.gca().set_aspect('equal')
		ax.set_xticks([])
		ax.set_yticks([])
		# Draw chiplets 
		for (idx1, c1) in enumerate(self.chiplets):
			col = cfg.plotting_color_map[c1.typ]
			rect = plt.Rectangle(c1.get_pos(), c1.size[0]-0.15, c1.size[1]-0.15, fc = col, fill = True, zorder= 3)
			ax.add_patch(rect)
			ax.text(c1.get_pos()[0] + c1.size[0]/2 - 0.15,  c1.get_pos()[1] + c1.size[1]/2 - 0.15, c1.typ, ha = "center", va = "center", fontweight = "bold")
			# Draw PHYs
			for phy in c1.phys:
				x = phy.pos[0] if phy.pos[0] < c1.get_pos()[0] + 0.5 else (phy.pos[0] - 0.15)
				y = phy.pos[1] if phy.pos[1] < c1.get_pos()[1] + 0.5 else (phy.pos[1] - 0.15)
				circ = plt.Circle((x,y), 0.35, fc = cfg.plotting_color_map["phy"], fill = True, zorder = 3)
				ax.add_patch(circ)
		# Draw Links
		if nw_success:
			for (c1, p1) in neighbors:
				phy = self.chiplets[c1].phys[p1]
				x1 = phy.pos[0] if phy.pos[0] < self.chiplets[c1].get_pos()[0] + 0.5 else (phy.pos[0] - 0.15)
				y1 = phy.pos[1] if phy.pos[1] < self.chiplets[c1].get_pos()[1] + 0.5 else (phy.pos[1] - 0.15)
				for (c2, p2) in neighbors[(c1,p1)]:
					phy = self.chiplets[c2].phys[p2]
					x2 = phy.pos[0] if phy.pos[0] < self.chiplets[c2].get_pos()[0] + 0.5 else (phy.pos[0] - 0.15)
					y2 = phy.pos[1] if phy.pos[1] < self.chiplets[c2].get_pos()[1] + 0.5 else (phy.pos[1] - 0.15)
					ax.arrow(x1,y1,x2-x1,y2-y1,zorder = 5, color = cfg.plotting_color_map["link"],length_includes_head=True, head_width = 0.0, head_length = 0.0, linewidth = 6)
		ax.axis('off')
		# Set scale
		ax.set_xlim(-0.1,self.size[0] + 0.05)
		ax.set_ylim(-0.1,self.size[1] + 0.05)
		# Store image
		plt.savefig("plots/" + fig_name + ".pdf")

	def update_placement_size(self):
		bottom_left_corners = [chiplet.get_pos() for chiplet in self.chiplets]
		correction_x = -1 * min([blc[0] for blc in bottom_left_corners])
		correction_y = -1 * min([blc[1] for blc in bottom_left_corners])
		vec = [correction_x, correction_y]
		for chiplet in self.chiplets:
			chiplet.move_by(vec)
		top_right_corners = [chiplet.get_pos_inv() for chiplet in self.chiplets]
		size_x = max([trc[0] for trc in top_right_corners])
		size_y = max([trc[1] for trc in top_right_corners])
		self.size = (size_x, size_y)

	# Derive the placement-based interconnect topology
	def get_network_internal(self):	
		# 0) Construct a graph where phys are vertices and links are edges
		neighbors = {(cidx,pidx) : [] for (cidx, c) in enumerate(self.chiplets) for pidx in range(len(c.phys)) }
		edges = []
		edge_weights = {}
		edge_is_d2d = {}
		# 1) Add edges within chiplet (not D2D)
		for (cidx, c) in enumerate(self.chiplets):
			for pidx1 in range(len(c.phys)):
				for pidx2 in range(len(c.phys)):
					if pidx1 == pidx2:
						continue
					neighbors[(cidx,pidx1)].append((cidx,pidx2))
					neighbors[(cidx,pidx2)].append((cidx,pidx1))
					edge_weights[((cidx,pidx1),(cidx,pidx2))] = 0
					edge_weights[((cidx,pidx2),(cidx,pidx1))] = 0
					edge_is_d2d[((cidx,pidx1),(cidx,pidx2))] = False
					edge_is_d2d[((cidx,pidx2),(cidx,pidx1))] = False
		# 2) Add edges between chiplets (D2D)
		for (cidx1, c1) in enumerate(self.chiplets):
			for (cidx2, c2) in enumerate(self.chiplets):
				if cidx1 == cidx2:
					continue
				for (pidx1, p1) in enumerate(c1.phys):
					for (pidx2, p2) in enumerate(c2.phys):
						dist = get_dist(p1.pos, p2.pos, self.params["dist_type"])		
						if dist <= self.params["max_length"]:
							neighbors[(cidx1,pidx1)].append((cidx2,pidx2))
							neighbors[(cidx2,pidx2)].append((cidx1,pidx1))
							edge_weights[((cidx1,pidx1),(cidx2,pidx2))] = dist
							edge_weights[((cidx2,pidx2),(cidx1,pidx1))] = dist
							edge_is_d2d[((cidx1,pidx1),(cidx2,pidx2))] = True
							edge_is_d2d[((cidx2,pidx2),(cidx1,pidx1))] = True
							edges.append(((cidx1,pidx1),(cidx2,pidx2)))
		# 3) Check for unconnected chiplets:
		unconnected_chiplet_ids = []
		for (cidx, c) in enumerate(self.chiplets):
			n_links = sum([len(neighbors[(cidx,pidx)]) for pidx in range(len(c.phys))])
			if n_links == 0:
				unconnected_chiplet_ids.append(cidx)
		if len(unconnected_chiplet_ids) > 0:
			return (False, "unconnected chiplets", unconnected_chiplet_ids)
		# 4) Find a minimal spanning tree using Prim's Algorithm
		final_neighbors = {(cidx,pidx) : [] for (cidx, c) in enumerate(self.chiplets) for pidx in range(len(c.phys)) }
		phy_available = {(cidx,pidx) : True for (cidx, c) in enumerate(self.chiplets) for pidx in range(len(c.phys)) }
		final_nodes = []
		todo = queue.PriorityQueue()
		todo.put((0,(None, (0,0))))
		while todo.qsize() > 0:
			(_, (pred,cur)) = todo.get()
			# If this node was already reached over a cheaper path
			if cur in final_nodes:
				continue
			# If one of both phys of that link are already used for a different link
			if pred != None and (pred[0] != cur[0]) and ((not phy_available[pred]) or (not phy_available[cur])):
				continue
			# Store new node and new edge, update phy availability if needed
			final_nodes.append(cur)
			if pred != None:
				final_neighbors[cur].append(pred)
				final_neighbors[pred].append(cur)
				if pred[0] != cur[0]:
					phy_available[pred] = False
					phy_available[cur] = False
			# Explore all neighbors
			for nei in neighbors[cur]:
				if nei not in final_nodes:
					dist = edge_weights[(cur,nei)]
					todo.put((dist, (cur, nei)))
		# 5) Check if the whole graph is unconnected
		if len(final_nodes) < len(neighbors):
			return (False, "unconnected network", None)
		# 6) Post-process: Only keep D2D links
		for (cidx1, pidx1) in final_neighbors: 
			idx = 0
			while idx < len(final_neighbors[(cidx1, pidx1)]):
				(cidx2, pidx2) = final_neighbors[(cidx1, pidx1)][idx]
				if cidx1 == cidx2:
					del final_neighbors[(cidx1, pidx1)][idx]
				else:
					idx += 1
		# 7) Add additional edges to increase connectivity
		connected_chiplet_pairs = [(min(a[0],b[0]), max(a[0],b[0])) for a in final_neighbors for b in final_neighbors[a]]
		edges = sorted(edges, key = lambda x : edge_weights[x])
		for (src, dst) in edges:
			if (min(src[0],dst[0]), max(src[0],dst[0])) not in connected_chiplet_pairs:
				if phy_available[src] and phy_available[dst]:
					final_neighbors[src].append(dst)
					final_neighbors[dst].append(src)
					phy_available[src] = False
					phy_available[dst] = False
					connected_chiplet_pairs.append((min(src[0],dst[0]), max(src[0],dst[0])))
		return (True, None, final_neighbors)
		
	# Derive the placement-based interconnect topology
	def get_network(self):	
		# Try to extract a network topology
		(success, error, info) = self.get_network_internal()
		# If unable to derive topology, return None
		if not success:
			return Network(None, None, None, None, None)
		# Topology was successfully derived, convert to output format
		else:
			n = len(self.chiplets)
			node_types = [self.chiplets[i].typ for i in range(n)]
			neighbors = [[] for i in range(n)]		
			phy_map = [[] for i in range(n)]		
			internal_neighbors = info
			for (cidx1, pidx1) in internal_neighbors:
				for (cidx2, pidx2) in internal_neighbors[(cidx1, pidx1)]:
					if cidx1 != cidx2:
						neighbors[cidx1].append(cidx2)
						phy_map[cidx1].append((pidx1, pidx2))
			return Network(n, node_types, neighbors, phy_map, self.params["relay_chiplets"])

	# Return the area of this placement
	def get_area(self):
		return self.size[0] * self.size[1]


	# Export this placement to RapidChiplet
	def export(self, path, algo):
		# Create placement-file
		placement = {"chiplets" : [], "interposer_routers" : []}	
		for (idx, chiplet) in enumerate(self.chiplets):
			placement["chiplets"].append({
				"position" 	: {"x" : chiplet.pos[0], "y" : chiplet.pos[1]},	
				"rotation" 	: chiplet.rotation,
				"name" 		: chiplet.typ,
			})
		hlp.write_file("%s/chiplet_placements/placement_%s_%s.json" % (path, self.params["experiment"], algo), placement)




