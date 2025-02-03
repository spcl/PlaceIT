# Import Python Libraries
import sys
import subprocess
import threading

# Import our own files
import config as cfg
import placeit_helpers as hlp
import export_best_placements as ebp

def write_booksim_config(	exp, 
							algo, 
							traffic_mode, 
							trace_mode = "authentic", 
							use_partial_simulation = 0,
							partial_simulation_cycles = 1000000,
							partial_simulation_region = 0,
							traffic = "C2C",
							trace = "none"
						):
	# Create the "chiplets" file (same for all algorithms)
	bsconf = {}
	bsconf["traffic_mode"] = traffic_mode
	bsconf["trace_mode"] = trace_mode
	bsconf["use_partial_simulation"] = use_partial_simulation
	bsconf["partial_simulation_cycles"] = partial_simulation_cycles
	bsconf["partial_simulation_region"] = partial_simulation_region
	bsconf["traffic"] = traffic
	bsconf["trace"] = trace
	bsconf["routing_function"] = "min"
	# We experience issues with network deadlocks in BookSim2 only for the full trace simulations of the 64cores heterogeneous architecture optimized using Simulated Annealing when only using 4 virtual channels, but with 8 virtual channels these issues disappear.
	# These issues do not arise with synthetic traffic, with partial trace regions or with any other combination of architecture and optimization algorithm.
	# Therefore, we use 8 virtual channels for that special case and 4 for all other cases.
	bsconf["num_vcs"] = 8 if (exp == "64cores_hetero" and algo == "sa" and traffic_mode == "trace" and use_partial_simulation == 0) else 4
	bsconf["vc_buf_size"] = 8
	bsconf["warmup_periods"] = (1 if traffic_mode == "synthetic" else 0)
	bsconf["sim_count"] = 1
	bsconf["hold_switch_for_packet"] = 0
	bsconf["packet_size"] = 1
	bsconf["vc_allocator"] = "separable_input_first"
	bsconf["sw_allocator"] = "separable_input_first"
	bsconf["alloc_iters"] = 1
	bsconf["sample_period"] = 5000
	bsconf["wait_for_tail_credit"] = 0
	bsconf["priority"] = "none"
	bsconf["injection_rate_uses_flits"] = 1
	bsconf["deadlock_warn_timeout"] = 1024
	hlp.write_file("RapidChiplet/inputs/booksim_config/booksim_config_%s_%s.json" % (exp, algo), bsconf)

def run_evaluation_single_algorithm_synthetic(exp, params, algo):
	# Construct the required paths and flags
	design = "./inputs/designs/design_%s_%s.json"% (exp,algo)
	# Iterate through traffic patterns
	for traffic in ["C2C","C2M","C2I","M2I"]:
		# Info to user
		print("Performing Evaluation of \"%s\" (%s) using synthetic %s traffic" % (exp, algo, traffic))
		# Write the corresponding booksim config
		write_booksim_config(exp, algo, "synthetic", traffic = traffic)
		# Set name of results file
		results_file = "%s_%s_%s" % (exp, algo, traffic) 
		# Run the experiment	
		out = subprocess.check_output(["python3", "run_booksim_simulation.py", "-df", design, "-rf", results_file], cwd = "./RapidChiplet")

def run_evaluation_single_algorithm_full_trace(exp, params, algo, full_timeout):
	# Construct the required paths and flags
	design = "./inputs/designs/design_%s_%s.json"% (exp,algo)
	# Iterate through traces
	for trace in params["eval_traces"]:
		# Construct path to trace
		trace_path = "./booksim2/src/netrace/traces/" + trace + ".tra.bz2"
		# Info to user
		print("Performing Evaluation of \"%s\" (%s) using the %s trace" % (exp, algo, trace))
		# Perform twice for authentic and idealized mode
		for netrace_cycles in [0,1]:
			# Write the corresponding booksim config
			write_booksim_config(exp, algo, "trace", trace_mode = ("authentic" if netrace_cycles else "idealized"), use_partial_simulation = 0, trace = trace_path)
			# Set name of results file
			results_file = "%s_%s_%s_%d" % (exp, algo, trace, netrace_cycles) 
			# Run the experiment	
			try:
				out = subprocess.check_output(["python3", "run_booksim_simulation.py", "-df", design, "-rf", results_file, "-to", str(full_timeout)], cwd = "./RapidChiplet")
			except Exception as e:
				print(e)

def run_evaluation_single_algorithm_partial_trace(exp, params, algo, partial_timeout, partial_cycles):
	# Construct the required paths and flags
	design = "./inputs/designs/design_%s_%s.json"% (exp,algo)
	# Iterate through traces
	for trace in params["partial_eval_traces"]:
		# Construct path to trace
		trace_path = "./booksim2/src/netrace/traces/" + trace + ".tra.bz2"
		for region in range(params["trace_region_counts"][trace]):
			# Info to user
			print("Performing Evaluation of \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))
			# Write the corresponding booksim config (We only perform partial trace evaluations with netrace cycles)
			write_booksim_config(exp, algo, "trace", trace_mode = "authentic", use_partial_simulation = 1, partial_simulation_cycles = partial_cycles, partial_simulation_region = region, trace = trace_path)
			# Set name of results file
			results_file = "%s_%s_%s_%d_reg%d" % (exp, algo, trace, 1, region) 
			# Run the experiment
			try:
				# The timeout of this outer process needs to be higher than the timeout of the inner process
				# otherwise the inner process doesn't terminate and the booksim-process remains running even though the run-booksim-process terminated
				out = subprocess.check_output(["python3", "run_booksim_simulation.py", "-df", design, "-rf", results_file, "-to", str(partial_timeout)], cwd = "./RapidChiplet", timeout = partial_timeout + 10)
				print("Successfully completed \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))
			except subprocess.TimeoutExpired:
				print("Timeout exceeded for \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))
			except subprocess.CalledProcessError as e:
				if e.returncode == 21:
					print("Timeout exceeded for \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))
				else:
					print("Non-zero exit code for \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))
			except Exception as e:
				print("Unknown exception for \"%s\" (%s) using region %d of the trace %s" % (exp, algo, region, trace))

def run_synthetic_evaluation(exp, parent_thread_id):
	params = cfg.experiment_list[exp]
	# Export the placements to RapidChiplet
	ebp.export_best_placements(exp)	
	# Iterate through optimization algorithms
	threads = []
	for (i, algo) in enumerate(params["algorithms"]):
		print("Spawning thread %d.%d to evaluate the %s-algorithm in \"%s\" using synthetic traffic" % (parent_thread_id, i, algo, exp))
		thread = threading.Thread(target = run_evaluation_single_algorithm_synthetic, args = (exp, params, algo))
		threads.append(thread)
		thread.start()
	# Wait for all threads to terminate
	for (i, thread) in enumerate(threads):
		thread.join()
		print("Thread %d.%d terminated" % (parent_thread_id, i))

def run_full_trace_evaluation(exp, parent_thread_id, full_timeout):
	params = cfg.experiment_list[exp]
	# Export the placements to RapidChiplet
	ebp.export_best_placements(exp)	
	# Iterate through optimization algorithms
	threads = []
	for (i, algo) in enumerate(params["algorithms"]):
		print("Spawning thread %d.%d to evaluate the %s-algorithm in \"%s\" using full traces" % (parent_thread_id, i, algo, exp))
		thread = threading.Thread(target = run_evaluation_single_algorithm_full_trace, args = (exp, params, algo, full_timeout))
		threads.append(thread)
		thread.start()
	# Wait for all threads to terminate
	for (i, thread) in enumerate(threads):
		thread.join()
		print("Thread %d.%d terminated" % (parent_thread_id, i))

def run_partial_trace_evaluation(exp, parent_thread_id, partial_timeout, partial_cycles):
	params = cfg.experiment_list[exp]
	# Export the placements to RapidChiplet
	ebp.export_best_placements(exp)	
	# Iterate through optimization algorithms
	threads = []
	for (i, algo) in enumerate(params["algorithms"]):
		print("Spawning thread %d.%d to evaluate the %s-algorithm in \"%s\" using partial traces" % (parent_thread_id, i, algo, exp))
		thread = threading.Thread(target = run_evaluation_single_algorithm_partial_trace, args = (exp, params, algo, partial_timeout, partial_cycles))
		threads.append(thread)
		thread.start()
	# Wait for all threads to terminate
	for (i, thread) in enumerate(threads):
		thread.join()
		print("Thread %d.%d terminated" % (parent_thread_id, i))
