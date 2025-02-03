# Import python libraries
import sys
import copy

# Import our own files
import config as cfg					# Configuration
import placeit_helpers as hlp			# Helpers
from chiplet import Chiplet				# A class for chiplets
from placement import Placement			# The placement-class (the underlying data-structure of the hetero-representation)
from representation_homo import HomoPlacement	# Homogeneous placement
from instance import Instance			# Instance (can be both homo or hetero)

# Variables to simplify the description of homogeneous placements
c = "C"
m = "M"
i = "I"
d = "D"
a = "A"
n = "N"
e = "E"
s = "S"
w = "W"

# The homogeneous placement for 32 cores
grid_32cores_homo = [
	[i,c,c,c,c,c,c,c,c,m],
	[m,c,c,c,c,c,c,c,c,i],
	[i,c,c,c,c,c,c,c,c,m],
	[m,c,c,c,c,c,c,c,c,i],
]
phys_32cores_homo = [
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
]
phys_32cores_homo_2 = [
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
]

# The homogeneous placement for 64 cores
grid_64cores_homo = [
	[m,c,c,c,c,c,c,c,c,i],
	[i,c,c,c,c,c,c,c,c,m],
	[m,c,c,c,c,c,c,c,c,i],
	[i,c,c,c,c,c,c,c,c,m],
	[m,c,c,c,c,c,c,c,c,i],
	[i,c,c,c,c,c,c,c,c,m],
	[m,c,c,c,c,c,c,c,c,i],
	[i,c,c,c,c,c,c,c,c,m],
]
phys_64cores_homo = [
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
	[e,a,a,a,a,a,a,a,a,w],
]
phys_64cores_homo_2 = [
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
	[a,a,a,a,a,a,a,a,a,a],
]

# The heterogeneous placement for 32 cores
placement_32cores_hetero = {}
placement_32cores_hetero["C"] = [((4 + 3 * x, 3 * y),0) for x in range(4) for y in range(8)]
placement_32cores_hetero["M"] = [
	((0,6),2),	
	((0,18),2),	
	((16,0),0),	
	((16,12),0),	
]
placement_32cores_hetero["I"] = [
	((1,1),2),	
	((1,13),2),	
	((16,7),0),	
	((16,19),0),	
]

# The heterogeneous placement for 64 cores
placement_64cores_hetero = {}
placement_64cores_hetero["C"] = [((4 + 3 * x, 3 + 3 * y),0) for x in range(8) for y in range(8)]
placement_64cores_hetero["M"] = [
	((0,3),2),	
	((0,9),2),	
	((0,15),2),	
	((0,21),2),	

	((28,3),0),	
	((28,9),0),	
	((28,15),0),	
	((28,21),0),	
]
placement_64cores_hetero["I"] = [
	((5,0),3),	
	((11,0),3),	
	((17,0),3),	
	((23,0),3),	

	((5,27),1),	
	((11,27),1),	
	((17,27),1),	
	((23,27),1),	
]

# Dictionary containing all baselines, keyed by the experiment-name
baselines = {
	"32cores_homo" : (grid_32cores_homo,phys_32cores_homo),
	"64cores_homo" : (grid_64cores_homo,phys_64cores_homo),
	"32cores_homo_2" : (grid_32cores_homo,phys_32cores_homo_2),
	"64cores_homo_2" : (grid_64cores_homo,phys_64cores_homo_2),
	"32cores_hetero" : placement_32cores_hetero,
	"64cores_hetero" : placement_64cores_hetero,
	"debug" : placement_32cores_hetero,
}

# Function to create a manual placement
def create_baseline(params):
	# Read parameters
	exp = params["experiment"]
	r_typ = params["representation"]
	# Read correct baseline	
	baseline = baselines[exp]
	# Differentiate between placement representations: Homogeneous
	if r_typ == "homogeneous":
		# This is the case for the experiments of the appendix
		if len(params["relay_chiplets"]) == 3:
			baseline = baselines[exp + "_2"]
		homo = HomoPlacement(params, baseline[0], baseline[1])
		inst = Instance("homogeneous", params, homo)
	# Differentiate between placement representations: Heterogeneous 
	elif r_typ == "heterogeneous":
		chiplets = []
		for c_typ in baseline:
			for (pos, rot) in baseline[c_typ]:
				chiplet = Chiplet(pos, params["dimensions"][c_typ], c_typ, params["phys"][c_typ])
				chiplet.rotate(90*rot)
				chiplet.move_to(pos)
				chiplets.append(chiplet)
		plac = Placement(params, chiplets)
		if not plac.is_valid:
			print("ERROR: Invalid baseline placement")
			plac.visualize("invalid_baseline_placement")
			sys.exit()
		inst = Instance("placement", params, plac)
	else:
		print("ERROR: Invalid placement representation \"%s\"" % r_typ)
		sys.exit()

	# Storing the baseline requires serializing the phys in the configuration
	params_ = copy.deepcopy(params)
	for c_type in params_["phys"]:
		params_["phys"][c_type] = [x.to_json() for x in params_["phys"][c_type]]

	# Things to be written in the results file
	# Since the baseline is created instantaneously and not through some optimization process, there are no updates.
	to_store = {"best_inst" : inst.to_json(), "updates" : [], "parameters" : params_}

	# Store the results file
	hlp.write_file("results/%s.json" % (exp + "_bl_0"), to_store)	

# If this script is called directly
if __name__ == "__main__":
	# The experiment name needs to be passed as a command line argument
	if len(sys.argv) < 2:
		print("usage: python3 create_baseline.py <experiment-name>")
		sys.exit()
	# Run experiment
	params = cfg.experiment_list[sys.argv[1]]
	params["experiment"] = sys.argv[1]
	# If we use the heterogeneous representation, compute whether a given chiplet type is
	# rotation-sensitive, rotation-invariant or rotation-hybrid.
	if params["representation"] == "heterogeneous":
		params["rotation_behaviour"] = hlp.compute_rotation_behaviour(params)
	params["cf_normalizers"] = hlp.compute_normalizers(params)
	create_baseline(params)
