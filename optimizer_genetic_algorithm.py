# Import python libraries
import random as rnd
import time
import copy

# Import our own files
import placeit_helpers as hlp
from instance import Instance

# Create a random population
def get_random_population(typ, params):
	pop_size = params["ga_P"]
	population = []
	while len(population) < pop_size:
		population.append(Instance(typ, params))
	return population

# Perform tournament selection
def tournament_selection(params, pop):
	candidates = rnd.choices(pop, k = params["ga_T"])
	return sorted(candidates, key = lambda x : x.get_cost())[:2]

# Dictionary of selection functions - currently, we only use tournament selection
selection_functions = {
	"tournament" : tournament_selection,
}

# Perform one epoch
def run_epoch(pop, params):
	n = len(pop)
	# Run one epoch
	ordered_pop = sorted(pop, key = lambda x : x.get_cost())
	# Elitism Selection
	new_pop = ordered_pop[:params["ga_E"]]
	new_pop_hashes = [x.get_hash() for x in new_pop] 
	# Selecting the remaining elements
	while len(new_pop) < params["ga_P"]:
		valid = False
		while not valid:
			parents = selection_functions[params["ga_sel_fun"]](params, pop)
			child = parents[0].merge(parents[1])
			if rnd.random() < params["ga_pm"]:
				child = child.mutate()
			valid = (child.get_hash() not in new_pop_hashes)
		new_pop.append(child)
		new_pop_hashes.append(child.get_hash())
	return new_pop

def optimizer_genetic_algorithm(typ, params, save_name):
	# Extract relevant parameters
	time_budget = params["time_budget"]
	store_debug_info = params["debug_info"]
	debug_divider = 1 + int(1/params["debug_frac_ga"])
	# Info about best instance found
	best_inst = None
	updates = []
	debug_info = []
	# Start timer
	starttime = time.process_time()
	duration = 0
	# Initialize random population
	pop = get_random_population(typ, params)
	# Run the genetic algorithm
	epoch_counter = 0
	while duration < time_budget:
		pop = run_epoch(pop, params)
		epoch_counter += 1
		duration = time.process_time() - starttime
		for individual in pop:
			if best_inst == None or individual.get_cost() < best_inst.get_cost():
				best_inst = individual
				updates.append((duration, best_inst.get_cost()))
		if store_debug_info and (epoch_counter % debug_divider) == 0:
			debug_info.append((duration, [x.get_cost() for x in pop],[x.get_origin() for x in pop]))
	# Storing the baseline requires serializing the phys in the configuration
	params_ = copy.deepcopy(params)
	for c_type in params_["phys"]:
		params_["phys"][c_type] = [x.to_json() for x in params_["phys"][c_type]]
	# Save results
	to_store = {"best_inst" : best_inst.to_json(),
				"updates" : updates,
				"parameters" : params_,
				"n_epochs" : epoch_counter}
	# Store debug info if configured to do so
	if store_debug_info:
		to_store["debug_info"] = debug_info
	# Store results
	hlp.write_file("results/%s.json" % save_name, to_store)



