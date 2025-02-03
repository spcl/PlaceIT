# Import python libraries
import sys
import matplotlib.pyplot as plt
import json

# Write a JSON file
def write_file(file, content):
    file = open(file, "w")
    file.write(json.dumps(content, indent=4))
    file.close()

# Read a JSON file
def read_file(filename):
    file = open(filename, "r")
    file_content = json.loads(file.read())
    file.close()
    return file_content

# Compute cost function normalizers
def compute_normalizers(params):
	from instance import Instance
	all_metrics = ["c2c_lat","c2c_tp","c2m_lat","c2m_tp","c2i_lat","c2i_tp","m2i_lat","m2i_tp","area"]
	params["cf_normalizers"] = {metric : 1 for metric in all_metrics}
	reps = params["norm_samples"]			
	typ = params["representation"]
	instances = [Instance(typ, params) for i in range(reps)]
	cf_normalizers = {}
	for metric in all_metrics:
		cf_normalizers[metric] = sum([inst.get_eval()[metric] for inst in instances]) / reps
	return cf_normalizers	

# Compute rotation-behaviour for each chiplet type (for heterogeneous placements only)
def compute_rotation_behaviour(params):
	from chiplet import Chiplet
	rotation_behaviour = {}
	c_types = list(params["dimensions"].keys())
	for typ in c_types:
		chiplet = Chiplet((0,0), params["dimensions"][typ], typ, params["phys"][typ])
		phy_poss_1 = set([phy.pos for phy in chiplet.phys])
		chiplet.rotate(90)
		chiplet.move_to((0,0))
		phy_poss_2 = set([phy.pos for phy in chiplet.phys])
		chiplet.rotate(90)
		chiplet.move_to((0,0))
		phy_poss_3 = set([phy.pos for phy in chiplet.phys])
		if phy_poss_1 != phy_poss_3:
			rotation_behaviour[typ] = "sensitive"
		elif phy_poss_1 != phy_poss_2 or params["dimensions"][typ][0] != params["dimensions"][typ][1]:
			rotation_behaviour[typ] = "hybrid"
		else:
			rotation_behaviour[typ] = "invariant"
	return rotation_behaviour

# Restore an instance from a result-file
def restore_instance(path):
	# Imports
	import config as cfg
	from representation_homo import HomoPlacement
	from representation_hetero import HeteroPlacement 
	from placement import Placement 
	from chiplet import Chiplet
	from phy import PHY
	from instance import Instance

	# Read data
	results = read_file(path)
	exp = results["parameters"]["experiment"]
	typ = results["best_inst"]["typ"]	
	data = results["best_inst"]["sub_instance"]
	params = cfg.experiment_list[exp]
	params["cf_normalizers"] = results["parameters"]["cf_normalizers"]
	
	# Differentiate between representations: Homogeneous
	if typ == "homogeneous":
		sub_inst = HomoPlacement(params, data["grid"], data["phys"])
	# Differentiate between representations: Heterogeneous 
	elif typ == "heterogeneous":
		sub_inst = HeteroPlacement(params, data["types"], data["rotations"])
	# Differentiate between representations: Placement (the underlying data-structure of HeteroPlacement) 
	elif typ == "placement":
		chiplets = []	
		for chiplet_ in data["chiplets"]:
			phys = []
			for phy_ in chiplet_["phys"]:
				phys.append(PHY(phy_["pos"]))
			chiplet = Chiplet(chiplet_["pos"], chiplet_["size"], chiplet_["typ"], phys, abs_phy_pos_given = True)
			chiplet.rotation = chiplet_["rotation"]
			chiplets.append(chiplet)
		sub_inst = Placement(params, chiplets)
	else:
		print("ERROR: Unsupported placement representation \"%s\"" % typ)
		sys.exit()
	# Create and return instance
	return Instance(typ, params, sub_inst)
