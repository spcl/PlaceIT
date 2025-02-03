# Import python libraries
import sys

# Import our own files
import config as cfg
import placeit_helpers as hlp

# Export the best placement per optimization algorithm to RapidChiplet
def export_best_placements(exp):

	# Read Configuration
	params = cfg.experiment_list[exp]
	params["experiment"] = exp

	# Create the "chiplets" file (same for all algorithms)
	chiplets = {}
	for typ in ["C","M","I"]:
		phys = params["phys"][typ]
		chiplet = {
			"dimensions" : {"x" : params["dimensions"][typ][0], "y" : params["dimensions"][typ][1]},
			"type" : {"C" : "compute", "M" : "memory", "I" : "io"}[typ],
			"phys" : [{"x" : phys[i].pos[0], "y" : phys[i].pos[1]} for i in range(len(phys))],
			"technology" : "placeit_tech",
			"power" : 0, 		# De do not use the power estimation features
			"relay" : (typ in params["relay_chiplets"]),
			"internal_latency" : params["L_relay"],
			"unit_count" : 1,	# We assume one unit per chiplet	
		}
		chiplets[typ] = chiplet
	hlp.write_file("RapidChiplet/inputs/chiplets/chiplets_" + exp + ".json", chiplets)

	# Create the "technology nodes" file (same for all algorithms)
	placeit_tech = {
		"phy_latency" : params["L_phy"],
		"wafer_radius" : 101.6,								# 8inch diameter -> 101.6mm radius
		"wafer_cost" : 500,									# Probably inaccurate, but we don't use the cost model anyway.
		"defect_density": 0.005,							# 0.5/cm2 -> 0.005/mm2
	}
	technology_nodes = {"placeit_tech" : placeit_tech}
	hlp.write_file("RapidChiplet/inputs/technology_nodes/technology_nodes_" + exp + ".json", technology_nodes)

	# Create the "packaging" file (same for all algorithms)
	packaging = {
		"link_routing" : params["dist_type"],	
		"link_latency_type" : "constant",
		"link_latency" : params["L_link"],
		"packaging_yield" : 1,								# Dummy value, we don't use the cost feature
		"is_active" : False,								# We use a passive interposer 
		"has_interposer" : True,
		"interposer_technology" : "placeit_tech",
	}
	hlp.write_file("RapidChiplet/inputs/packaging/packaging_" + exp + ".json", packaging)


	# Placement and Topology (export the best one for each optimization algorithm)
	# Export the design file (export best for each optimization algorithm)
	for algo in params["algorithms"]:
		# Find best results
		best_cost = float("inf")
		best_file = None
		for rep in range(1 if algo == "bl" else params["repetitions"]):
			filename = "results/%s_%s_%d.json" % (exp, algo, rep)
			results = hlp.read_file(filename)
			if results["best_inst"]["sub_instance"]["cost"] < best_cost:
				best_cost = results["best_inst"]["sub_instance"]["cost"]
				best_file = filename
		# Restore best instance
		inst = hlp.restore_instance(best_file)
		# Export Placement and Topology
		inst.export("RapidChiplet/inputs", algo)
		# Create design file
		design = {
			"technology_nodes_file" 	: "inputs/technology_nodes/technology_nodes_%s.json" % (exp),
			"chiplets_file" 			: "inputs/chiplets/chiplets_%s.json" % (exp),
			"chiplet_placement_file" 	: "inputs/chiplet_placements/placement_%s_%s.json" % (exp, algo),
			"ici_topology_file" 		: "inputs/ici_topologies/topology_%s_%s.json" % (exp, algo),
			"packaging_file"			: "inputs/packaging/packaging_%s.json" % (exp),
			"thermal_config"			: "inputs/thermal_config/example_thermal_config.json",						# We don't use this
			"booksim_config"			: "inputs/booksim_config/booksim_config_%s_%s.json" % (exp,algo),	# This file will be written by the evaluation script
		}
		hlp.write_file("RapidChiplet/inputs/designs/design_%s_%s.json" % (exp, algo), design)

# If this script is called directly
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("usage: python3 export_best_placements.py <experiment-name>")
		sys.exit()
	exp = sys.argv[1]
	export_best_placements(exp)
	



