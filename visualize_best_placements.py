# Import Python Libraries
import sys

# Import our own files
import config as cfg
import placeit_helpers as hlp

def visualize_best_placements(exp):
	params = cfg.experiment_list[exp]
	# Iterate through algorithms
	for algo in params["algorithms"]:
		# Find the best placement found by this algorithm
		best_cost = float("inf")
		best_file = None
		for rep in range(1 if algo == "bl" else params["repetitions"]):
			filename = "results/%s_%s_%d.json" % (exp, algo, rep)
			results = hlp.read_file(filename)
			if results["best_inst"]["sub_instance"]["cost"] < best_cost:
				best_cost = results["best_inst"]["sub_instance"]["cost"]
				best_file = filename
		# Restore and visualize the best placement
		inst = hlp.restore_instance(best_file)
		inst.visualize("%s_%s" % (exp, algo))

# The visualization function can be called manually
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("usage: python3 visualize_best_placements.py <experiment-name>")
		sys.exit()
	exp = sys.argv[1]
	visualize_best_placements(exp)
