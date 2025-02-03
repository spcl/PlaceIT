# Import our own files
from representation_homo import HomoPlacement
from representation_hetero import HeteroPlacement
from placement import Placement
import placeit_helpers as hlp

# All optimization algorithms work with the instance-class. 
# Internally, the instance class calls functions from a specific placement representation 
class Instance:
	# Constructor
	def __init__(self, typ, params, sub_instance = None):
		self.typ = typ
		self.params = params
		# The placement representation was passed as an argument
		if sub_instance != None:
			self.sub_instance = sub_instance
		# Randomly initialize the underlying placement representation
		else:
			self.sub_instance = {"homogeneous" : HomoPlacement, "placement" : Placement, "heterogeneous" : HeteroPlacement}[typ](params)

	# Convert instance to JSON
	def to_json(self):
		json = {
			"typ" : self.typ,
			"sub_instance" : self.sub_instance.to_json(),
		}
		return json

	# Visualize this instance
	def visualize(self, fig_name = None):
		self.sub_instance.visualize(fig_name)

	# Extract the placement-based ICI topology
	def get_network(self):
		return self.sub_instance.get_network()

	# Get the area
	def get_area(self):
		return self.sub_instance.get_area()

	# Perform a mutation
	def mutate(self):
		return Instance(self.typ, self.params, self.sub_instance.mutate())

	# Merge two instances
	def merge(self, other):
		return Instance(self.typ, self.params, self.sub_instance.merge(other.sub_instance))

	# Extract cost
	def get_cost(self):
		return self.sub_instance.cost

	# Get the evaluation of an instance
	def get_eval(self):
		return self.sub_instance.eval

	# Get the origin of an instance (either random, mutation, or merge)
	def get_origin(self):
		return self.sub_instance.origin

	# Get a unique hash of an instance
	def get_hash(self):
		return self.sub_instance.hash

	# Returns True if the instance is valid (i.e. the ICI topology is connected)
	def is_valid(self):
		return self.sub_instance.is_valid

	# Export this instance to RapidChiplet
	def export(self, path, algo):
		# Export placement	
		self.sub_instance.export(path, algo)

		# Export topology
		nw = self.sub_instance.get_network()
		topology = []		
		for src_id in range(nw.n):
			for (dst_id, (src_phy, dst_phy)) in zip(nw.neighbors[src_id], nw.phy_map[src_id]):
				if src_id < dst_id:
					link = {
						"ep1" : {"type" : "chiplet", "outer_id" : src_id, "inner_id" : src_phy},
						"ep2" : {"type" : "chiplet", "outer_id" : dst_id, "inner_id" : dst_phy},
					}
					topology.append(link)
		hlp.write_file("%s/ici_topologies/topology_%s_%s.json" % (path, self.params["experiment"], algo), topology)
	
