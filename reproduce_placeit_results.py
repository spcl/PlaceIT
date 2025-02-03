# Import python libraries
import sys
import threading
import random as rnd

# Import our own files
import plots
import config as cfg
import run_experiments as rexp
import run_evaluation as reval
import create_cost_function_weight_adjustment_plot as ccfwap
import visualize_best_placements as vbp

mode = "main"

# Configure the experiments to run here
experiments = ["32cores_homo","64cores_homo","32cores_hetero","64cores_hetero"]

# Reproduce all data from the PlaceIT paper
# Note: This takes multiple days to run!
def reproduce_placeit_results(mode):
	# Set random seed to ensure reproducibility 
	rnd.seed(0)
	#############################################################################################################
	# Perform optimization of placements and topologies															#
	#############################################################################################################
	# Run all experiments sequentially to avoid slowdowns due to Pythons global interpreter lock (GIL).
	# This takes approximately 5 days.
	exp_threads = []
	for (i, exp) in enumerate(experiments):
		rexp.run_experiment(exp)

	#############################################################################################################
	# Perform evaluation on synthetic traffic
	#############################################################################################################
	# Run the evaluation: Start one thread per experiment
	# The evaluation-runner will then start one thread per algorithm, i.e., a total of 16 threads will be running
	eval_threads = []
	for (i, exp) in enumerate(experiments):
		print("Spawning thread %i to run synthetic evaluation for \"%s\"" % (i, exp))
		thread = threading.Thread(target = reval.run_synthetic_evaluation, args = (exp, i))
		eval_threads.append(thread)
		thread.start()
	# Wait for all evaluation-threads to complete their work
	for (i, thread) in enumerate(eval_threads):
		thread.join()
		print("Synthetic evaluation thread %d terminated" % (i))

	#############################################################################################################
	# Perform evaluation on full traffic traces
	#############################################################################################################
	# Run the evaluation: Start one thread per experiment
	# The evaluation-runner will then start one thread per algorithm, i.e., a total of 16 threads will be running
	timeout = 3600 * 12
	eval_threads = []
	for (i, exp) in enumerate(experiments):
		print("Spawning thread %i to run full trace evaluation for \"%s\"" % (i, exp))
		thread = threading.Thread(target = reval.run_full_trace_evaluation, args = (exp, i, timeout))
		eval_threads.append(thread)
		thread.start()
	# Wait for all evaluation-threads to complete their work
	for (i, thread) in enumerate(eval_threads):
		thread.join()
		print("Full trace evaluation thread %d terminated" % (i))

	#############################################################################################################
	# Perform evaluation on partial traffic traces
	#############################################################################################################
	# Run the evaluation: Start one thread per experiment
	# The evaluation-runner will then start one thread per algorithm, i.e., a total of 16 threads will be running
	partial_cycles = 1000000	
	timeout = 3600				
	eval_threads = []
	for (i, exp) in enumerate(experiments):
		print("Spawning thread %i to run partial trace evaluation for \"%s\"" % (i, exp))
		thread = threading.Thread(target = reval.run_partial_trace_evaluation, args = (exp, i, timeout, partial_cycles))
		eval_threads.append(thread)
		thread.start()
	# Wait for all evaluation-threads to complete their work
	for (i, thread) in enumerate(eval_threads):
		thread.join()
		print("Partial trace evaluation thread %d terminated" % (i))

	#############################################################################################################
	# Create Figures																							#
	#############################################################################################################

	# Create Figure 4 from the paper
	print("Creating random instances to showcase the cost function weights adjustment plot")
	ccfwap.create_cost_function_weight_adjustment_plot("32cores_hetero", 300, 500)
	# Create Figures 6 and 12 from the paper
	print("Creating Figures showing results of the optimization process")
	for exp in experiments:
		plots.plot_result_evolution(exp)
		plots.plot_result_distribution(exp)		
	# Create Figure 13 from the paper
	# Note: This function actually plots more figures than we included in the paper.
	print("Visualizing baseline and optimized placements")
	for exp in experiments:
		vbp.visualize_best_placements(exp)		
	# Create Figure 14 or 15 the paper
	print("Creating Figures showing results on synthetic traffic")
	plots.create_synthetic_heatmap(experiments)
	# Create Figure 17 or 18 from the paper
	print("Creating Figures showing results on full traffic traces")
	plots.create_trace_bars(experiments)
	# Create Figure 16 from the paper (left or right half)
	print("Creating Figures showing results on partial traffic traces")
	plots.create_trace_heatmap(experiments)


# NOTE: The mode in the config.py and plots.py needs to be set manually!!!
reproduce_placeit_results(mode)
