# Import python libraries
import sys
import json
import random as rnd 

# Import our own files
import plots
import config as cfg
import placeit_helpers as hlp
from instance import Instance

def create_cost_function_weight_adjustment_plot(exp, reps, norm):
	# Set random seed to ensure reproducibility 
	rnd.seed(0)

	# Fetch parameters
	params = cfg.experiment_list[exp]

	# If we use the heterogeneous representation, compute whether a given chiplet type is
	# rotation-sensitive, rotation-invariant or rotation-hybrid.
	if params["representation"]== "heterogeneous":
		params["rotation_behaviour"] = hlp.compute_rotation_behaviour(params)

	# Compute cost function normalizers
	print("Generating %d instances to compute cost function normalizers" % norm)
	params["norm_samples"] = norm
	params["cf_normalizers"] = hlp.compute_normalizers(params)

	# Generate instances to adjust the cost function
	print("Generating %d instances to adjust the cost function weights" % reps)
	instances = []
	for i in range(reps):
		instances.append(Instance(params["representation"], params))

	# Evaluate the generated instances
	evals = []
	for instance in instances:
		evaluation = instance.get_eval()
		evaluation["cost"] = instance.get_cost()
		evaluation["area"] = instance.get_area()
		evals.append(evaluation)

	# Store the evaluations of all generated instances
	filename = "results/random_evals_%s.json" % exp
	hlp.write_file(filename, evals)

	# Plot the "cost function weights adjustment plot"
	plots.plot_random_instances(filename, exp)

# If this script is called directly
if __name__ == "__main__":
	if len(sys.argv) < 4:
		print("usage: python3 create_cost_function_weigth_adjustment_plot <experiment-name> <repetitions> <normalization-samples>")
		sys.exit()
	exp = sys.argv[1]
	reps = int(sys.argv[2])
	norm = int(sys.argv[3])
	create_cost_function_weight_adjustment_plot(exp, reps, norm)
