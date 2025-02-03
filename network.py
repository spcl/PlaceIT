# Class representing an inter-chiplet interconnection network
class Network:
	# Constructor
	def __init__(self, n, node_types, neighbors, phy_map, relay_types):
		self.n = n
		self.node_types = node_types
		self.neighbors = neighbors
		self.phy_map = phy_map
		self.relay_types = relay_types

	# Check that the network is valid, i.e. fully connected
	def validate(self):
		# Check that the network was initialized correctly
		if self.n == None or self.node_types == None or self.neighbors == None or self.relay_types == None:
			return False
		# Start at a random compute-chiplet, perform BFS to check that every chiplet is reachable
		start = self.node_types.index("C")	
		visited = []
		todo = [start]
		while len(todo) > 0:
			cur = todo.pop()
			visited.append(cur)
			# Only continue BFS if the cur-chiplet has relay-capability
			if self.node_types[cur] in self.relay_types:
				for nei in self.neighbors[cur]:
					if nei not in visited and nei not in todo:
						todo.append(nei)
		return len(visited) == self.n

