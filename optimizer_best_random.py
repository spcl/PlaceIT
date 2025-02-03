# Import python libraries
import time
import copy

# Import our own files
import placeit_helpers as hlp
from instance import Instance


def optimizer_best_random(typ, params, save_name):
	# Extract relevant parameters
	time_budget = params["time_budget"]
	# Info about the best instance found
	best_inst = None
	updates = []
	# Start timer
	starttime = time.process_time()
	duration = 0
	# Generate random placements until time budges is expired
	n_generated = 0
	while duration < time_budget:
		# Generate and evaluate a random placement
		inst = Instance(typ, params)
		duration =  time.process_time() - starttime
		n_generated += 1
		# Check if this one is better than the previous one
		if best_inst == None or inst.get_cost() < best_inst.get_cost():
			best_inst = inst
			updates.append((duration, best_inst.get_cost()))
	# Storing the baseline requires serializing the phys in the configuration
	params_ = copy.deepcopy(params)
	for c_type in params_["phys"]:
		params_["phys"][c_type] = [x.to_json() for x in params_["phys"][c_type]]
	# Store results
	to_store = {"best_inst" : best_inst.to_json(),
				"updates" : updates,
				"parameters" : params_,
				"n_generated" : n_generated}

	hlp.write_file("results/%s.json" % save_name, to_store)
