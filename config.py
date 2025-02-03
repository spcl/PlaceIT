# Import our own files
from phy import PHY

mode = "main"

# Colors for plotting
plotting_color_map = {
	"C" : "#66aadd", 	# Compute chiplet
	"M" : "#66ddaa", 	# Memory chiplet
	"I" : "#ddaa66",	# IO chiplet
	"X" : "#FFFFFF",	# No chiplet
	"phy" :"#666666",	# PHY
	"link":"#000000",	# D2D link
	"br": "#000000",	# Best random optimizer
	"ga": "#000099",	# Genetic algorithm optimizer
	"sa": "#009900",	# Simulated annealing optimizer
	"bl": "#990000",	# Baseline
}

# Line-Styles for plotting
plotting_linestyle_map = {
	"br": "solid",			# Best random optimizer
	"ga": (0, (2, 1)),		# Genetic algorithm optimizer
	"sa": (0, (1, 0.5)),	# Simulated annealing optimizer
	"bl":  (0, (3, 1)),		# Baseline 
}

# Cost-function weights 
# These are supposed to be set manually by the user
cf_weights = {
				"c2c_lat" : 0.1,
				"c2c_tp" : 0.1,
				"c2m_lat" : 2,
				"c2m_tp" : 2,
				"c2i_lat" : 0.1,
				"c2i_tp" : 0.1,
				"m2i_lat" : 2,
				"m2i_tp" : 2,
				"area" : 2,
			}

# Chiplet dimensions
# These are supposed to be set manually by the user
sizes_hetero = {"C" : (3,3), "M" : (4,5), "I" : (3,4)}
sizes_homo = {"C" : (3,3), "M" : (3,3), "I" : (3,3)}

# PHY spacing towards closest edge
ps = 0.2 

# PHY placement for heterogeneous chiplets
comp_phys = [	PHY((ps,sizes_hetero["C"][1]/2)),
				PHY((sizes_hetero["C"][0]-ps,sizes_hetero["C"][1]/2)),
				PHY((sizes_hetero["C"][0]/2,ps)),
				PHY((sizes_hetero["C"][0]/2,sizes_hetero["C"][1]-ps))]
mem_phys = 	[ 	PHY((ps,sizes_hetero["M"][1]/2))]
io_phys = 	[	PHY((ps,sizes_hetero["I"][1]/2))]
mem_phys_2 = [	PHY((ps,sizes_hetero["M"][1]/2)),
				PHY((sizes_hetero["M"][0]-ps,sizes_hetero["M"][1]/2)),
				PHY((sizes_hetero["M"][0]/2,ps)),
				PHY((sizes_hetero["M"][0]/2,sizes_hetero["M"][1]-ps))]
io_phys_2 = [	PHY((ps,sizes_hetero["I"][1]/2)),
				PHY((sizes_hetero["I"][0]-ps,sizes_hetero["I"][1]/2)),
				PHY((sizes_hetero["I"][0]/2,ps)),
				PHY((sizes_hetero["I"][0]/2,sizes_hetero["I"][1]-ps))]
phys_hetero = {"C" : comp_phys, "M" : mem_phys, "I" : io_phys}
phys_hetero_2 = {"C" : comp_phys, "M" : mem_phys_2, "I" : io_phys_2}

# PHY placement for Homogeneous chiplets
# PHYs for homogeneous placements need to be ordered North, East, South, West
phys_4 = [		PHY((sizes_hetero["C"][0]/2,sizes_hetero["C"][1]-ps)),		# North
				PHY((sizes_hetero["C"][0]-ps,sizes_hetero["C"][1]/2)),		# East
				PHY((sizes_hetero["C"][0]/2,ps)),							# South
				PHY((ps,sizes_hetero["C"][1]/2))]							# West
phys_1 = [		PHY((sizes_hetero["C"][0] - ps, sizes_hetero["C"][1]/2))]	# East
phys_homo = {"C" : phys_4, "M" : phys_1, "I" : phys_1}
phys_homo_2 = {"C" : phys_4, "M" : phys_4, "I" : phys_4}

# Configuration of traces
eval_traces = ["blackscholes_64c_simsmall"]

# Configuration of trace regions
trace_region_counts = {
	"blackscholes_64c_simsmall" : 5,
	"bodytrack_64c_simlarge" : 5,
	"canneal_64c_simmedium" : 5,
	"dedup_64c_simmedium" : 5,
	"ferret_64c_simmedium" : 5,
	"fluidanimate_64c_simsmall" : 5,
	"swaptions_64c_simlarge" : 5,
	"vips_64c_simmedium" : 5,
	"x264_64c_simsmall" : 5,
}

partial_eval_traces = list(trace_region_counts.keys())

# Experiment Setup for 32-cores with homogeneous chiplets
params_32cores_homo = {
	"algorithms"	: ["bl","br","ga","sa"],	# Optimization Algorithm
	"representation": "homogeneous",			# Placement Representation
	"time_budget"	: 3600,						# Time Budget
	"repetitions" 	: 10,						# Repetitions to create confidence intervals
	"norm_samples" 	: 500,						# Number of Samples to compute Cost Function Normalizers
	"mutation_mode" : "neighbors-one",			# Mutation mode
	"n_compute" 	: 32,						# Number of compute-chiplets
	"n_memory" 		: 4,						# Number of memory-chiplets
	"n_io"		 	: 4,						# Number of IO-chiplets
	"dimensions" 	: sizes_homo,				# Chiplet dimensions
	"phys" 			: (phys_homo_2 if mode == "appendix" else phys_homo),			
	"relay_chiplets": (["C","M","I"] if mode == "appendix" else ["C"]),			
	"dist_type"		: "euclidean",				# Distance measure: euclidean or manhattan
	"max_length"	: 3,						# Maximum length of D2D links
	"L_relay"		: 10,						# Latency of relaying a message through a chiplet [cycles]
	"L_phy"			: 12,						# Latency of a PHY
	"L_link"		: 1,						# Latency of a link
	"debug_info" 	: False,					# Enables debug-information
	"debug_frac_sa"	: 0.05,						# Fraction of instances to be stored in the debug info 
	"debug_frac_ga"	: 0.5,						# Fraction of populations to be stored in the debug info 
	"rows" 			: 4,						# Rows of chiplets (for homogeneous placements only)
	"cols" 			: 10,						# Columns of chiplets (for homogeneous placements only)
	"cf_weights"	: cf_weights,				# Cost function weights
	"mutation_bias" : 0.5,						# Steers probability of "swap" vs. "rotate" in the "?-one" mutation mode
	"sa_cooling"	: "lin-mult",				# Cooling schedule in SA
	"sa_adaptive"	: True,						# Enable adaptive cooling in SA
	"sa_T0" 		: 40, 						# Initial temperature in SA
	"sa_L"			: 250,						# Iterations per round in SA
	"sa_a"			: 1,						# The parameter alpha in SA
	"sa_b"			: 5,						# The parameter beta in SA
	"ga_P"			: 200,						# Population size in GA
	"ga_E" 			: 30,						# Elitism size in GA
	"ga_T" 			: 30,						# Tournament size in GA
	"ga_pm" 		: 0.5,						# Mutation probability in GA
	"ga_sel_fun"  	: "tournament",				# Selection function in GA
	"eval_traces"	: eval_traces,				# Traces to be used in the evaluation of this experiment
	"partial_eval_traces" : partial_eval_traces,# Traces to be used in the evaluation of this experiment
	"trace_region_counts" : trace_region_counts,# Number of trace regions per trace
}

# Experiment Setup for 64-cores with homogeneous chiplets
params_64cores_homo = {
	"algorithms"	: ["bl","br","ga","sa"],	# Optimization Algorithm 
	"representation": "homogeneous",			# Placement Representation
	"time_budget"	: 3600,						# Time Budget
	"repetitions" 	: 10,						# Repetitions to create confidence intervals
	"norm_samples" 	: 500,						# Number of Samples to compute Cost Function Normalizers
	"mutation_mode" : "neighbors-one",			# Mutation mode
	"n_compute" 	: 64,						# Number of compute-chiplets
	"n_memory" 		: 8,						# Number of memory-chiplets
	"n_io"		 	: 8,						# Number of IO-chiplets
	"dimensions" 	: sizes_homo,				# Chiplet dimensions
	"phys" 			: (phys_homo_2 if mode == "appendix" else phys_homo),			
	"relay_chiplets": (["C","M","I"] if mode == "appendix" else ["C"]),			
	"dist_type"		: "euclidean",				# Distance measure: euclidean or manhattan
	"max_length"	: 3,						# Maximum length of D2D links
	"L_relay"		: 10,						# Latency of relaying a message through a chiplet [cycles]
	"L_phy"			: 12,						# Latency of a PHY
	"L_link"		: 1,						# Latency of a link
	"debug_info" 	: False,					# Enables debug-information
	"debug_frac_sa"	: 0.05,						# Fraction of instances to be stored in the debug info 
	"debug_frac_ga"	: 0.5,						# Fraction of populations to be stored in the debug info 
	"rows" 			: 8,						# Rows of chiplets (for homogeneous placements only)
	"cols" 			: 10,						# Columns of chiplets (for homogeneous placements only)
	"cf_weights"	: cf_weights,				# Cost function weights
	"mutation_bias" : 0.5,						# Steers probability of "swap" vs. "rotate" in the "?-one" mutation mode
	"sa_cooling"	: "lin-mult",				# Cooling schedule in SA
	"sa_adaptive"	: True,						# Enable adaptive cooling in SA
	"sa_T0" 		: 35, 						# Initial temperature in SA
	"sa_L"			: 50,						# Iterations per round in SA
	"sa_a"			: 1,						# The parameter alpha in SA
	"sa_b"			: 5,						# The parameter beta in SA
	"ga_P"			: 50,						# Population size in GA
	"ga_E" 			: 8,						# Elitism size in GA
	"ga_T" 			: 8,						# Tournament size in GA
	"ga_pm" 		: 0.5,						# Mutation probability in GA
	"ga_sel_fun"  	: "tournament",				# Selection function in GA
	"eval_traces"	: eval_traces,				# Traces to be used in the evaluation of this experiment
	"partial_eval_traces" : partial_eval_traces,# Traces to be used in the evaluation of this experiment
	"trace_region_counts" : trace_region_counts,# Number of trace regions per trace
}

# Experiment Setup for 32-cores with heterogeneous chiplets
params_32cores_hetero = {
	"algorithms"	: ["bl","br","ga","sa"],	# Optimization Algorithm
	"representation": "heterogeneous",			# Placement Representation
	"time_budget"	: 3600,						# Time Budget
	"repetitions" 	: 6,						# Repetitions to create confidence intervals
	"norm_samples" 	: 500,						# Number of Samples to compute Cost Function Normalizers
	"mutation_mode" : "any-one",				# Mutation mode
	"n_compute" 	: 32,						# Number of compute-chiplets
	"n_memory" 		: 4,						# Number of memory-chiplets
	"n_io"		 	: 4,						# Number of IO-chiplets
	"dimensions" 	: sizes_hetero,				# Chiplet dimensions
	"phys" 			: (phys_hetero_2 if mode == "appendix" else phys_hetero),			
	"relay_chiplets": (["C","M","I"] if mode == "appendix" else ["C"]),			
	"dist_type"		: "euclidean",				# Distance measure: euclidean or manhattan
	"max_length"	: 3,						# Maximum length of D2D links
	"L_relay"		: 10,						# Latency of relaying a message through a chiplet [cycles]
	"L_phy"			: 12,						# Latency of a PHY
	"L_link"		: 1,						# Latency of a link
	"debug_info" 	: False,					# Enables debug-information
	"debug_frac_sa"	: 0.05,						# Fraction of instances to be stored in the debug info 
	"debug_frac_ga"	: 0.5,						# Fraction of populations to be stored in the debug info 
	"cf_weights"	: cf_weights,				# Cost function weights
	"mutation_bias" : 0.5,						# Steers probability of "swap" vs. "rotate" in the "?-one" mutation mode
	"sa_cooling"	: "lin-mult",				# Cooling schedule in SA
	"sa_adaptive"	: True,						# Enable adaptive cooling in SA
	"sa_T0" 		: 33, 						# Initial temperature in SA
	"sa_L"			: 50,						# Iterations per round in SA
	"sa_a"			: 1,						# The parameter alpha in SA
	"sa_b"			: 5,						# The parameter beta in SA
	"ga_P"			: 30,						# Population size in GA
	"ga_E" 			: 6,						# Elitism size in GA
	"ga_T" 			: 6,						# Tournament size in GA
	"ga_pm" 		: 0.5,						# Mutation probability in GA
	"ga_sel_fun"  	: "tournament",				# Selection function in GA
	"eval_traces"	: eval_traces,				# Traces to be used in the evaluation of this experiment
	"partial_eval_traces" : partial_eval_traces,# Traces to be used in the evaluation of this experiment
	"trace_region_counts" : trace_region_counts,# Number of trace regions per trace
}

# Experiment Setup for 64-cores with heterogeneous chiplets
params_64cores_hetero = {
	"algorithms"	: ["bl","br","ga","sa"],	# Optimization Algorithm
	"representation": "heterogeneous",			# Placement Representation 
	"time_budget"	: 3600,						# Time Budget
	"repetitions" 	: 10,						# Repetitions to create confidence intervals
	"norm_samples" 	: 500,						# Number of Samples to compute Cost Function Normalizers 
	"mutation_mode" : "any-one",				# Mutation mode
	"n_compute" 	: 64,						# Number of compute-chiplets
	"n_memory" 		: 8,						# Number of memory-chiplets
	"n_io"		 	: 8,						# Number of IO-chiplets
	"dimensions" 	: sizes_hetero,				# Chiplet dimensions
	"phys" 			: (phys_hetero_2 if mode == "appendix" else phys_hetero),			
	"relay_chiplets": (["C","M","I"] if mode == "appendix" else ["C"]),			
	"dist_type"		: "euclidean",				# Distance measure: euclidean or manhattan
	"max_length"	: 3,						# Maximum length of D2D links
	"L_relay"		: 10,						# Latency of relaying a message through a chiplet [cycles]
	"L_phy"			: 12,						# Latency of a PHY
	"L_link"		: 1,						# Latency of a link
	"debug_info" 	: False,					# Enables debug-information
	"debug_frac_sa"	: 0.05,						# Fraction of instances to be stored in the debug info 
	"debug_frac_ga"	: 0.5,						# Fraction of populations to be stored in the debug info 
	"cf_weights"	: cf_weights,				# Cost function weights
	"mutation_bias" : 0.5,						# Steers probability of "swap" vs. "rotate" in the "?-one" mutation mode
	"sa_cooling"	: "lin-mult",				# Cooling schedule in SA
	"sa_adaptive"	: True,						# Enable adaptive cooling in SA
	"sa_T0" 		: 28, 						# Initial temperature in SA
	"sa_L"			: 45,						# Iterations per round in SA
	"sa_a"			: 1,						# The parameter alpha in SA
	"sa_b"			: 5,						# The parameter beta in SA
	"ga_P"			: 20,						# Population size in GA
	"ga_E" 			: 5,						# Elitism size in GA
	"ga_T" 			: 5,						# Tournament size in GA
	"ga_pm" 		: 0.5,						# Mutation probability in GA
	"ga_sel_fun"  	: "tournament",				# Selection function in GA
	"eval_traces"	: eval_traces,				# Traces to be used in the evaluation of this experiment
	"partial_eval_traces" : partial_eval_traces,# Traces to be used in the evaluation of this experiment
	"trace_region_counts" : trace_region_counts,# Number of trace regions per trace
}

# List of all experiments
experiment_list = {
	"32cores_homo" : params_32cores_homo,
	"64cores_homo" : params_64cores_homo,
	"32cores_hetero" : params_32cores_hetero,
	"64cores_hetero" : params_64cores_hetero,
}

