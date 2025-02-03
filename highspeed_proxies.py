# Import python libraries
import queue 
import random as rnd

# compute cost function of a placement
def cost_function(results, normalizers, weights):
	metrics = list(results.keys())
	cost = 0
	for metric in metrics:
		# Lower is better
		if "lat" in metric or metric == "area":
			cost += results[metric] / normalizers[metric] * weights[metric]
		# Higher is better
		elif "tp" in metric:
			cost += (1/(results[metric] / normalizers[metric])) * weights[metric]
		else:
			print("ERROR: No cost function computation defined for metric \"%s\"" % metric)
	return cost

# Compute the performance proxies as in RapidChiplet
# We implement our own version to avoid writing and reading input files which slows down the process
def compute_highspeed_proxies(area, network, params):
	# Hard-coded traffic classes
	traffic_classes = ["C2C","C2M","C2I","M2I"]
	# Extract network info
	n = network.n
	node_types = network.node_types
	neighbors = network.neighbors
	relay_types = network.relay_types
	# Extract parameters
	cf_normalizers = params["cf_normalizers"]
	cf_weights = params["cf_weights"]
	# Construct custom lists
	all_cids = list(range(n))
	cid_subsets = {letter : [i for i in range(n) if node_types[i] == letter] for letter in ["C","M","I"]}
	# Construct shortest paths
	paths = {} 
	edge_to_path_count = {tc : {} for tc in traffic_classes}
	# Use all chiplet types as source and compute reversed paths for C2C, C2M, and C2I
	for src in all_cids:
		hops = [float("inf") for i in range(n)]		# Distance from source
		preds = [[] for i in range(n)]				# List of predecessors
		todo = queue.PriorityQueue()				# Known but not yet visited nodes
		# Initialize with source
		hops[src] = 0								
		todo.put((0, src))
		# Visit all nodes
		while todo.qsize() > 0:
			(cur_hops, cur) = todo.get()
			# This is no longer the shortest known path from src to cur
			if cur_hops > hops[cur]:
				continue
			# This is (one of) the currently shortest path from src to cur
			if cur_hops == hops[cur]:
				# Iterate through neighbors of cur
				for nei in neighbors[cur]:	
					nei_hops = cur_hops + 1
					# New shortest path is found
					if nei_hops < hops[nei]:
						hops[nei] = nei_hops
						preds[nei] = [cur]
						# Only visit chiplets that can relay traffic
						if node_types[nei] in relay_types:
							todo.put((nei_hops, nei))
					# Alternative shortest path is found
					elif nei_hops == hops[nei]:
						if cur not in preds[nei]:
							preds[nei].append(cur)
			# ERROR: This path is shorter than the shortest known path
			else:
				print("ERROR: This path is shorter than the best known -> Bug in Dijkstra implementation")
		# Backtracking to construct paths for C2C, C2M, C2I: Only end at compute nodes since we use reversed pats
		for dst in (cid_subsets["C"] + cid_subsets["M"]):
			# Determine path type:
			if node_types[src] == "C" and node_types[dst] == "C":
				path_typ = "C2C"
			elif node_types[src] == "M" and node_types[dst] == "C":
				path_typ = "C2M"
			elif node_types[src] == "I" and node_types[dst] == "C":
				path_typ = "C2I"
			elif node_types[src] == "I" and node_types[dst] == "M":
				path_typ = "M2I"
			else:
				continue
			cur = dst
			paths[(dst,src)] = []
			while cur != src:
				path_counts = [edge_to_path_count[path_typ][(cur,pred)] if (cur,pred) in edge_to_path_count[path_typ] else 0 for pred in preds[cur]]
				# Select predecessor to greedily minimize path count per link
				idx = path_counts.index(min(path_counts)) if len(set(path_counts)) > 1 else 0
				pred = preds[cur][idx]
				edge = (cur, pred)
				# Store path
				paths[(dst,src)].append(cur)
				# Update edge count
				if edge not in edge_to_path_count[path_typ]:
					edge_to_path_count[path_typ][edge] = 0
				edge_to_path_count[path_typ][edge] += 1
				cur = pred
			paths[(dst,src)].append(src)

	# compute per-edge per-flow throughputs
	edge_to_per_flow_bw = {tc : {} for tc in traffic_classes}
	for path_typ in traffic_classes:
		for (s,t) in edge_to_path_count[path_typ]:
			edge_to_per_flow_bw[path_typ][(s,t)] = 1 / edge_to_path_count[path_typ][(s,t)]
	# Compute per-path latencies and throughputs: Core-to-Core
	latencies = {tc : [] for tc in traffic_classes}
	throughputs = {tc : [] for tc in traffic_classes}
	for tc in traffic_classes:
		for src in cid_subsets[tc[0]]:
			acc_hops = []
			acc_tps = []
			for dst in cid_subsets[tc[-1]]:
				if src != dst:
					path = paths[(src,dst)]
					acc_hops.append(len(paths[(src,dst)])-1)
					acc_tps.append(min([edge_to_per_flow_bw[tc][(path[i],path[i+1])] for i in range(len(path)-1)]))
			h = sum(acc_hops) / len(acc_hops)
			latencies[tc].append((h-1) * params["L_relay"] + 2 * h * params["L_phy"] + h * params["L_link"])	
			throughputs[tc].append(sum(acc_tps) / len(params["phys"][tc[0]])) 

	# Aggregate statistics
	avg = lambda x : sum(x)/len(x)
	results = {
		"c2c_lat" : avg(latencies["C2C"]),
		"c2c_tp" : avg(throughputs["C2C"]),
		"c2m_lat" : avg(latencies["C2M"]),
		"c2m_tp" : avg(throughputs["C2M"]),
		"c2i_lat" : avg(latencies["C2I"]),
		"c2i_tp" : avg(throughputs["C2I"]),
		"m2i_lat" : avg(latencies["M2I"]),
		"m2i_tp" : avg(throughputs["M2I"]),
		"area" : area,
	}
	
	# Compute cost function
	cost = cost_function(results, cf_normalizers, cf_weights)
	
	# Return median in case of multiple repetitions, usually only one repetition is done with a deterministic routing function
	return (cost, results)	
