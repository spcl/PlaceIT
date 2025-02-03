# Import python libraries
import time
import copy
import math
import random as rnd

# Import our own files
import placeit_helpers as hlp
from instance import Instance

def optimizer_simulated_annealing(typ, params, save_name):
	# Extract relevant parameters
	time_budget = params["time_budget"]
	cooling = params["sa_cooling"]
	adaptive = params["sa_adaptive"]
	T0 = params["sa_T0"]
	L = params["sa_L"]
	a = params["sa_a"]
	b = params["sa_b"]
	n = params["n_compute"] + params["n_memory"] + params["n_io"]
	store_debug_info = params["debug_info"]
	debug_divider = 1 + int(1/params["debug_frac_sa"])
	# Info about the best instance found
	best_inst = None
	updates = []
	debug_info = []
	# Start timer
	starttime = time.process_time()
	duration = 0
	# Generate an initial placement
	cur_inst = Instance(typ, params)	
	# The current config is the best known at start
	best_inst = cur_inst
	updates.append((time.process_time() - starttime, cur_inst.get_cost()))
	# Keep statistics
	iteration = 0
	n2 = n/2
	# Run simulated annealing algorithm
	while duration < time_budget:
		iteration += 1
		duration = time.process_time() - starttime
		cand_inst = cur_inst.mutate()
		# Difference between candidate and current evaluation
		diff = (cand_inst.get_cost() - cur_inst.get_cost())
		k = int(math.floor(iteration/L))
		# Calculate temperature for current epoch
		if cooling == "exp-mult":
			T = T0 * a**k
		elif cooling == "log-mult":
			T = T0 / (1 + a * math.log(1+k))
		elif cooling == "lin-mult":
			T = T0 / (1 + a * k)
		elif cooling == "quad-mult":
			T = T0 / (1 + a * k**2)
		else:
			print("ERROR: Invalid cooling schedule \"%s\"" % cooling)
		# Perform adaptive cooling
		if adaptive:
			T = (1 + ((cur_inst.get_cost() - best_inst.get_cost())/cur_inst.get_cost()))**b * T
		# Update current
		if diff < 0:
			cur_inst = cand_inst
			# Update best
			if cand_inst.get_cost() < best_inst.get_cost():
				best_inst = cand_inst
				updates.append((duration, best_inst.get_cost()))
		# Compute metropolis score
		else:
			# Calculate metropolis acceptance criterion
			metropolis = math.exp(-diff / T)
			# Check if we should keep the new point
			acc_flag = False
			if rnd.random() < metropolis:
				cur_inst = cand_inst
				acc_flag = True
		# Store debug information
		if store_debug_info and (iteration % debug_divider) == 0:
			debug_info.append((duration, cand_inst.get_cost(), cur_inst.get_cost(), best_inst.get_cost()))
	# Storing the baseline requires serializing the phys in the configuration
	params_ = copy.deepcopy(params)
	for c_type in params_["phys"]:
		params_["phys"][c_type] = [x.to_json() for x in params_["phys"][c_type]]
	# Store Results
	to_store = {"best_inst" : best_inst.to_json(),
				"updates" : updates,
				"parameters" : params_,
				"n_iterations" : iteration}
	# Store debug information
	if store_debug_info:
		to_store["debug_info"] = debug_info
	# Store results
	hlp.write_file("results/%s.json" % save_name, to_store)

