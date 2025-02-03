# Import python libraries
import sys
import random as rnd

# Import our own files
import optimizer_best_random as obr					# Best Random
import optimizer_genetic_algorithm as oga			# Genetic Algorithm
import optimizer_simulated_annealing as osa			# Simulated Annealing
import create_baseline as cb						# Create baseline placements
import placeit_helpers as hlp						# Helpers
import config as cfg								# Configuration

# Map of optimizers
optimizers = {
	"br" : obr.optimizer_best_random,
	"ga" : oga.optimizer_genetic_algorithm,
	"sa" : osa.optimizer_simulated_annealing,
}

# Runs all algorithms for one experiment (one architecture)
def run_experiment(exp):
	# Set random seed to ensure reproducibility 
	rnd.seed(0)
	# Check if experiment name is valid
	if exp not in cfg.experiment_list:
		print("ERROR: Invalid experiment name \"%s\"" % exp)
		sys.exit()
	# Read parameters
	params = cfg.experiment_list[exp]
	typ = params["representation"]
	algos = params["algorithms"]
	# Store experiment name in parameters
	params["experiment"] = exp
	# If we use the heterogeneous representation, compute whether a given chiplet type is
	# rotation-sensitive, rotation-invariant or rotation-hybrid.
	if typ == "heterogeneous":
		params["rotation_behaviour"] = hlp.compute_rotation_behaviour(params)
	# Compute cost function normalizers
	params["cf_normalizers"] = hlp.compute_normalizers(params)
	# Create the baseline placement
	if "bl" in algos:
		cb.create_baseline(params)
	# Execute the specified number of repetitions
	for i in range(params["repetitions"]):	
		# Run all optimization algorithms (but don't re-create the baseline each time)
		for algo in [x for x in algos if x != "bl"]:
			print("Running experiments of \"%s\" using the %s-algorithm: repetition %d" % (exp, algo.upper(), i))
			optimizers[algo](typ, params, "%s_%s_%d" % (exp, algo, i))
		
# If this script is called directly
if __name__ == "__main__":
	# The experiment name needs to be passed as a command line argument
	if len(sys.argv) < 2:
		print("usage: python3 run_experiment <experiment-name>")
		sys.exit()
	# Run experiment
	run_experiment(sys.argv[1])

