# Import Python Libraries
import sys
import os
import copy
import math
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as colors
from pathlib import Path
import random as rnd
import numpy as np

# Import our own files
import config as cfg
import placeit_helpers as hlp

mode = "main"

# Colors to be used
global_colors = ["#000099","#009900","#990000"]

# Configure the "result evolution" plot
evol_yticks_main = {
	"32cores_homo" : [8.0 + x/4 for x in range(6)],
	"64cores_homo" : [8.25 + x/4 for x in range(6)],
	"32cores_hetero" : [8.25 + x/4 for x in range(6)],
	"64cores_hetero" : [8.0 + x/4 for x in range(6)],
}

# Configure the "result distribution" plot
dist_yticks_main = {
	"32cores_homo" : [7.9 + x/10 for x in range(8)],
	"64cores_homo" : [8.2 + x/10 for x in range(8)],
	"32cores_hetero" : [8.1 + x/10 for x in range(7)],
	"64cores_hetero" : [8.0 + x/10 for x in range(8)],
}

# Configure the "result evolution" plot
evol_yticks_appendix = {
	"32cores_homo" : [8.0 + x/1 for x in range(5)],
	"64cores_homo" : [8.0 + x/1 for x in range(6)],
	"32cores_hetero" : [7.5 + x/2 for x in range(7)],
	"64cores_hetero" : [8.5 + x*2 for x in range(5)],
}

# Configure the "result distribution" plot
dist_yticks_appendix  = {
	"32cores_homo" : [8.0 + x/10 for x in range(6)],
	"64cores_homo" : [8.3 + x/5 for x in range(6)],
	"32cores_hetero" : [7.6 + x/5 for x in range(6)],
	"64cores_hetero" : [8.2 + x/5 for x in range(6)],
}


evol_yticks = (evol_yticks_appendix if mode == "appendix" else evol_yticks_main)
dist_yticks = (dist_yticks_appendix if mode == "appendix" else dist_yticks_main)


# This dictionary defines the colormap used in the heatmaps
cdict = {'red':  ((0.0, 0.0, 0.0),(0.5, 1.0, 1.0),(1.0, 0.8, 0.8)),
        'green': ((0.0, 0.8, 0.8),(0.5, 1.0, 1.0),(1.0, 0.0, 0.0)),  
        'blue':  ((0.0, 0.0, 0.0),(0.5, 1.0, 1.0),(1.0, 0.0, 0.0)),
       }
GnRd = colors.LinearSegmentedColormap('GnRd', cdict)


# Plot cost function and trade-off for a bunch or fandom instances
# This is needed to adjust the cost-function weights
def plot_random_instances(filename, exp):
	# Used for colored bars
	rescale = lambda y: (y - np.min(y)) / (np.max(y) - np.min(y))
  	# Set-up the plot
	(fig, ax) = plt.subplots(1, 5, figsize = (12, 2.25))
	plt.subplots_adjust(left=0.05, right = 0.975, top = 0.9, bottom = 0.19, wspace = 0.6)

	# Read data
	data = hlp.read_file(filename)
	data = sorted(data, key = lambda x : -1 * x["cost"])
	n = len(data)

	# Plot the area plot
	areas = [x["area"] for x in data]
	costs = [x["cost"] for x in data]
	tmp = ax[0].scatter(costs, areas, marker = "o", c = costs, cmap='Greys_r', s = 10, edgecolor = "#000000", linewidth= 0.3, zorder = 3, vmin = 8, vmax = 14)
	fig.colorbar(tmp)

	# Plot circle around the best point
	best_idx = costs.index(min(costs))
	ax[0].plot(costs[best_idx], areas[best_idx], marker = "o", color = "#CC0000", ms = 6, fillstyle= "none", zorder = 5)

	# TODO: Set ticks (only to export plot to paper)
	xticks = [8,10,12,14]
	yticks = [450,500,550,600,650]
	ax[0].set_xticks(xticks)
	ax[0].set_yticks(yticks)
	ax[0].set_xlim(min(xticks),max(xticks))
	ax[0].set_ylim(min(yticks),max(yticks) + 0.03 * (max(yticks)-min(yticks)))

	ax[0].set_title("Area")
	ax[0].grid(zorder = 0)
	ax[0].set_ylabel("Area [mm$^2$]")
	ax[0].set_xlabel("Cost")
	xl = ax[0].get_xlim()
	yl = ax[0].get_ylim()
	x = xl[1] + (xl[1]-xl[0]) * 0.2
	y = yl[1] + (yl[1]-yl[0]) * 0.08
	ax[0].text(x, y, "Cost", ha = "center", va = "center")
	
	# Plot four throughput-vs-latency plots
	for (p, typ) in enumerate(["c2c","c2m","c2i","m2i"]):
		latencies = [x[typ + "_lat"] for x in data]
		throughputs = [100 * x[typ + "_tp"] for x in data]

		# Fix the throughput computations: Instead of 100% of source-injection-rate, plot 100% of min(source,destination) injection/ejection rate.
		params = cfg.experiment_list[exp]
		n_sending = params["n_memory" if typ == "m2i" else "n_compute"]
		n_receiving = params["n_compute" if typ == "c2c" else ("n_memory" if typ == "c2m" else "n_io")]
		ports_sending = len(params["phys"][typ[0].upper()])
		ports_receiving = len(params["phys"][typ[-1].upper()])
		throughputs = [x * (n_sending * ports_sending) / min(n_sending * ports_sending, n_receiving * ports_receiving) for x in throughputs] 

		# Get cost
		costs = [x["cost"] for x in data]
		n = min(len(latencies),len(throughputs))
	
		# Plot all points
		tmp = ax[p+1].scatter(latencies, throughputs, marker = "o", c = costs, cmap='Greys_r', s = 10, edgecolor = "#000000", linewidth= 0.3, zorder = 3, vmin = 8, vmax = 14)
		fig.colorbar(tmp)

		# Plot circle around the best point
		best_idx = costs.index(min(costs))
		ax[p+1].plot(latencies[best_idx], throughputs[best_idx], marker = "o", color = "#CC0000", ms = 6, fillstyle= "none", zorder = 5)

		# Configure axis
		ax[p+1].set_title(typ.replace("c","Core").replace("m","Memory").replace("i","IO").replace("2","-to-"))
		ax[p+1].grid(zorder = 0)
		ax[p+1].set_xlabel("Latency [cycles]")
		ax[p+1].set_ylabel("Throughput [%]")

		# TODO: Set ticks (only to export plot to paper)
		if typ == "c2c":
			xticks = [100,150,200,250]
			yticks = [6,8,10,12,14,16,18]
		else:
			xticks = [100,200,300,400]
			yticks = [40,60,80,100]
		ax[p+1].set_xticks(xticks)
		ax[p+1].set_yticks(yticks)
		ax[p+1].set_xlim(min(xticks), max(xticks))
		ax[p+1].set_ylim(min(yticks), max(yticks) + 0.03 * (max(yticks)-min(yticks)))



		xl = ax[p+1].get_xlim()
		yl = ax[p+1].get_ylim()
		x = xl[1] + (xl[1]-xl[0]) * 0.2
		y = yl[1] + (yl[1]-yl[0]) * 0.08
		ax[p+1].text(x, y, "Cost", ha = "center", va = "center")

	# Save plot
	plt.savefig("plots/random_instances_%s.pdf" % filename.split("/")[-1][:-5])

# Plots debug-information for the genetic algorithm
def plot_sa_debug(exp, custom = False):
	# Read file
	algo = "sac" if custom else "sa"
	filepath = "results/%s_%s_%d.json" % (exp, algo, 0)
	if not os.path.isfile(filepath):
		return
	data = hlp.read_file(filepath)
	if "debug_info" not in data:
		print("Error: The specified file does not contain debug info")
		sys.exit()
	data = data["debug_info"]
	# Extract info
	time = [x[0] for x in data]
	cand = [x[1] for x in data]
	cur = [x[2] for x in data]
	best = [x[3] for x in data]
	# Create plot
	(fig, ax) = plt.subplots(1, 1, figsize = (9, 3))
	plt.subplots_adjust(left=0.075, right = 0.965, top = 0.9, bottom = 0.15)
	ax.plot(time, cand, marker = "o", color = global_colors[0], label = "Candidate", linestyle = "None", markersize = 3, fillstyle = "none")
	ax.plot(time, cur, global_colors[1], label = "Current", linewidth = 1)
	ax.plot(time, best, global_colors[2], label = "Best", linestyle = ":", linewidth = 3)
	ax.grid()
	ax.set_xlabel("Time [s]")
	ax.set_ylabel("Cost Function")
	ax.legend(ncol = 3, loc = "upper center")
	# Save plot
	plt.savefig("plots/sa_debugging_%s.pdf" % exp)

# Plots debug information for simulated annealing
def plot_ga_debug(exp):
	# Read file
	filepath = "results/%s_%s_%d.json" % (exp, "ga", 0)
	if not os.path.isfile(filepath):
		return
	data = hlp.read_file(filepath)
	if "debug_info" not in data:
		print("Error: The specified file does not contain debug info")
		sys.exit()
	data = data["debug_info"]
	# Extract info
	times = [x[0] for x in data]
	costs = [x[1] for x in data]
	origins = [x[2] for x in data]
	n = min(len(times),len(costs))
	all_times = hlp.flatten([[times[i]] * len(costs[i]) for i in range(n)])
	all_costs = hlp.flatten(costs)
	all_colors = hlp.flatten([[{"random" : global_colors[0], "merge" : global_colors[1], "mutate" : global_colors[2]}[x] for x in y] for y in origins])
	# Create plot
	(fig, ax) = plt.subplots(1, 1, figsize = (9, 3))
	plt.subplots_adjust(left=0.075, right = 0.965, top = 0.9, bottom = 0.15)
	ax.scatter(all_times, all_costs, marker = "o", c = all_colors, linestyle = "None", s = 3)
	ax.grid()
	ax.set_xlabel("Time [s]")
	ax.set_ylabel("Cost Function")
	# Save plot
	plt.savefig("plots/ga_debugging_%s.pdf" % exp)

# Create the "result evolution" plot
def plot_result_evolution(exp):
	params = cfg.experiment_list[exp]
	max_time = params["time_budget"]
	# Set up plot
	(fig, ax) = plt.subplots(1, 1, figsize = (4, 1.333))
	plt.subplots_adjust(left=0.17, right = 0.975, top = 0.96, bottom = 0.31)
	# Iterate through optimization techniques
	algos = [algo for algo in params["algorithms"] if algo != "bl"]
	for (j, algo) in enumerate(algos):
		min_cost = [float("inf") for i in range(max_time+1)]
		max_cost = [0 for i in range(max_time+1)]
		avg_cost = [0 for i in range(max_time+1)]
		# Iterate through repetitions
		for rep in range(params["repetitions"]):
			# Read data
			data = hlp.read_file("results/%s_%s_%d.json" % (exp, algo, rep))["updates"]
			times = [min(int(x[0]), max_time) for x in data]
			costs = [x[1] for x in data]
			costs_unfolded = [float("inf") for i in range(max_time+1)]	
			for (time, cost) in zip(times,costs):
				costs_unfolded[int(time)] = cost
			for i in range(1,max_time+1):	
				costs_unfolded[i] = min(costs_unfolded[i-1], costs_unfolded[i])
				min_cost[i] = min(min_cost[i], costs_unfolded[i])
				max_cost[i] = max(max_cost[i], costs_unfolded[i])
				avg_cost[i] += costs_unfolded[i]
		for i in range(max_time + 1):
			avg_cost[i] = avg_cost[i] / (1 if algo == "bl" else params["repetitions"])
		start = 1
		while min_cost[start] == "-1" or max_cost[start] == -1 and start < max_time:
			start += 1
		# If there is actual data (it can be that the initialization took longer than the compute budget -
		# in that case there is no data and we don't need to plot anything)
		if start < max_time:
			# Plot data
			col = cfg.plotting_color_map[algo]
			lst = cfg.plotting_linestyle_map[algo]
			tme = [x/60 for x in list(range(start,max_time+1))]
			lab = {"br" : "Best Random (BR)","ga" : "Genetic Algorithm (GA)", "sa" : "Simulated Annealing (SA)", "bl" : "Baseline (BL)"}[algo]
			ax.plot(tme, avg_cost[start:], color = col, zorder = 3, alpha = 1.0, linewidth = 1.5, label = lab, linestyle=lst)
	# Plot baseline
	bl_cost = hlp.read_file("results/%s_%s_%d.json" % (exp, "bl", 0))["best_inst"]["sub_instance"]["cost"]
	# ax.text(0.5 * max(tme), bl_cost * 1.005, "2D Mesh (Fig. 12)",  color = cfg.plotting_color_map["bl"], fontsize = 7, ha = "center")
	ax.plot([min(tme),max(tme)], [bl_cost]*2, color = cfg.plotting_color_map["bl"], linestyle = cfg.plotting_linestyle_map["bl"])
	
	# Configure axis	
	ax.grid(zorder = 0)
	ax.set_xlabel("Runtime [min]")
	ax.set_ylabel("Cost")
	ax.set_ylim(min(evol_yticks[exp]),max(evol_yticks[exp]))
	ax.set_xlim(0, max(tme))
	ax.set_yticks(evol_yticks[exp])
	# ax.legend(loc = "center", bbox_to_anchor = (0.72,0.755), labelspacing = 0.1, borderpad = 0.2, fontsize = 8)
	# Save plot
	plt.savefig("plots/result_evolution_%s.pdf" % exp)

# Create the "result evaluation" plot
def plot_result_evaluation(exp, combined = False):	
	params = cfg.experiment_list[exp]
	# Set up plot
	(fig, ax) = plt.subplots(1, 5, figsize = (16, 3), width_ratios=[3, 3, 3, 3, 1])
	plt.subplots_adjust(left=0.075, right = 0.955, top = 0.9, bottom = 0.15, wspace = 0.5, hspace = 0.4)
	plot_data = {"c2c" : {"lat" : [], "tp" : []},
				 "c2m" : {"lat" : [], "tp" : []},
				 "c2i" : {"lat" : [], "tp" : []},
				 "m2i" : {"lat" : [], "tp" : []},
				 "Area" : {"lat" : [], "tp" : []}}
	eval_plot_data = {"c2c" : {"lat" : [], "tp" : []},
				 "c2m" : {"lat" : [], "tp" : []},
				 "c2i" : {"lat" : [], "tp" : []},
				 "m2i" : {"lat" : [], "tp" : []}}
	# Read Data: Iterate through optimization techniques
	costs = []
	algos = copy.deepcopy(params["algorithms"])
	for (j, algo) in enumerate(algos):
		data = None
		for rep in range((1 if algo == "bl" else params["repetitions"]) if algo != "bl" else 1):
			rep_data = hlp.read_file("results/%s_%s_%d.json" % (exp, algo, rep))
			if data == None or rep_data["best_inst"]["sub_instance"]["cost"] < data["best_inst"]["sub_instance"]["cost"]:
				data = rep_data
		eval_data = data["best_inst"]["sub_instance"]["eval"]
		cost = data["best_inst"]["sub_instance"]["cost"]
		costs.append(cost)
		# Read Data: Iterate through traffic classes
		for (p, typ) in enumerate(["c2c","c2m","c2i","m2i"]):
			lat = eval_data[typ + "_lat"] 
			tp = eval_data[typ + "_tp"] * 100
			plot_data[typ]["lat"].append(lat)
			plot_data[typ]["tp"].append(tp)
			ax[p].text(lat,tp,"  " + algo.upper(), ha = "left" , va = "center", zorder = 10)
			if combined and (typ in ["c2c","c2m","c2i","m2i"]):
				rc_data = hlp.read_file("./RapidChiplet/results/%s_%s_%s.json" % (exp, algo, typ.upper()))
				lat = float(rc_data["0.001"]["packet_latency"]["avg"])
				tp = max([float(load) for load in rc_data if len(rc_data[load]) > 0]) * 100
				eval_plot_data[typ]["lat"].append(lat)
				eval_plot_data[typ]["tp"].append(tp)
				ax[p].text(lat,tp,"  " + algo.upper(), ha = "left" , va = "center", zorder = 10)
			else:
				eval_plot_data[typ]["lat"] = float("nan")
				eval_plot_data[typ]["tp"] = float("nan")
		rand_x =rnd.random() 
		plot_data["Area"]["lat"].append(rand_x)
		plot_data["Area"]["tp"].append(eval_data["area"])
		ax[3].text(rand_x,eval_data["area"],"  " + algo.upper(), ha = "left" , va = "center", zorder = 10)
	# Create Plots: Iterate through traffic classes
	for (p, typ) in enumerate(["c2c","c2m","c2i","m2i","Area"]):
		# Plot data
		lats = plot_data[typ]["lat"]
		tps = plot_data[typ]["tp"]
		tmp = ax[p].scatter(lats, tps, marker = "*", c = costs, cmap='RdYlGn_r', s = 50, vmax = max(costs)*1.0, zorder = 3, edgecolor = "#000000", linewidth = 0.5)
		# Create color bar
		fig.colorbar(tmp, shrink = 1)
		xl = ax[p].get_xlim()
		yl = ax[p].get_ylim()
		x = xl[1] + (xl[1]-xl[0]) * (0.4 if p < 3 else 0.8)
		y = yl[0] + (yl[1]-yl[0]) * 1.05
		ax[p].text(x, y, "Cost", ha = "center", va = "center")
		# Add evaluation data if configures
		if combined and (typ in ["c2c","c2m","c2i","m2i"]):
			lats = eval_plot_data[typ]["lat"]
			tps = eval_plot_data[typ]["tp"]
			ax[p].scatter(lats, tps, marker = "o", c = costs, cmap='RdYlGn_r', s = 50, vmax = max(costs)*1.0, zorder = 3, edgecolor = "#000000", linewidth = 0.5)
		# Configure axis and labels
		ax[p].set_title(typ.replace("c","Core").replace("m","Memory").replace("i","IO").replace("2","-to-"))
		ax[p].set_xlabel("Latency [cycles]")
		ax[p].set_ylabel("Throughput [%]")		
		ax[p].grid(zorder = 0)
		fac = 1 if typ == "Area" else 0.15
		ax[p].set_xlim(right = ax[p].get_xlim()[1] + (ax[p].get_xlim()[1] - ax[p].get_xlim()[0]) * fac)
	ax[3].set_xlabel("")
	ax[3].set_ylabel("Area [mm^2]")		
	ax[3].set_xticks([])

	# Store plot
	plt.savefig("plots/result_evaluation_%s.pdf" % exp)

# Create the "result distribution" plot
def plot_result_distribution(exp):
	params = cfg.experiment_list[exp]
	# Set up plot
	(fig, ax) = plt.subplots(1, 1, figsize = (1.5, 1.5))
	plt.subplots_adjust(left=0.4, right = 0.975, top = 0.96, bottom = 0.3)
	# Iterate through algorithms
	algos = [algo for algo in params["algorithms"] if algo != "bl"]
	for (j, algo ) in enumerate(algos):
		all_costs = []
		for rep in range(1 if algo == "bl" else params["repetitions"]):
			data = hlp.read_file("results/%s_%s_%d.json" % (exp, algo, rep))
			all_costs.append(data["best_inst"]["sub_instance"]["cost"])
		col = cfg.plotting_color_map[algo]
		vp = ax.violinplot([all_costs], [j], showmeans = True)
		for x in ["cbars","cmins","cmaxes", "cmeans"]:
			vp[x].set_edgecolor(col)
		for x in vp["bodies"]:
			x.set_facecolor(col)
		
	ax.grid()
	ax.set_ylabel("Cost")
	ax.set_xticks([x for x in range(len(algos))])
	ax.set_yticks(dist_yticks[exp])
	ax.set_ylim(min(dist_yticks[exp]),max(dist_yticks[exp]))
	ax.set_xticklabels([x.upper() for x in algos])

	plt.savefig("plots/result_distribution_%s.pdf" % exp)

# Plot the number of instances generated by the different algorithms
def plot_ninstances(exp):
	params = cfg.experiment_list[exp]
	# Set up plot
	(fig, ax) = plt.subplots(1, 1, figsize = (3, 3))
	plt.subplots_adjust(left=0.25, right = 0.965, top = 0.9, bottom = 0.15)
	# Iterate through algorithms
	algos = [algo for algo in params["algorithms"] if algo != "bl"]
	for (j, algo ) in enumerate(algos):
		all_counters = []
		for rep in range(1 if algo == "bl" else params["repetitions"]):
			data = hlp.read_file("results/%s_%s_%d.json" % (exp, algo, rep))
			if algo == "br":
				all_counters.append(data["n_generated"])
			if algo == "sa":
				all_counters.append(data["n_iterations"])
			if algo == "ga":
				all_counters.append(params["ga_E"] + data["n_epochs"] * (params["ga_P"] - params["ga_E"]))
		if len(all_counters) > 0:
			col = cfg.plotting_color_map[algo]
			vp = ax.violinplot([all_counters], [j], showmeans = True)
			for x in ["cbars","cmins","cmaxes", "cmeans"]:
				vp[x].set_edgecolor(col)
			for x in vp["bodies"]:
				x.set_facecolor(col)
	ax.grid()
	ax.set_ylabel("#Instances")
	ax.set_xticks([x for x in range(len(algos))])
	ax.set_xticklabels([x.upper() for x in algos])
	ax.set_ylim(bottom = 0)
	plt.savefig("plots/result_ninstances_%s.pdf" % exp)

# Create latency-vs-load plots for synthetic traffic
def plot_lat_vs_load(exp):
	params = cfg.experiment_list[exp]
	# Set up plot
	(fig, ax) = plt.subplots(1, 4, figsize = (12, 3))
	plt.subplots_adjust(left=0.1, right = 0.975, top = 0.9, bottom = 0.15, wspace = 0.25)

	for (i, traffic) in enumerate(["C2C","C2M","C2I","M2I"]):
		ax[i].set_title(traffic)
		for algo in params["algorithms"]:
			data = hlp.read_file("./RapidChiplet/results/%s_%s_%s.json" % (exp, algo, traffic))
			loads = [float(load) for load in data if len(data[load]) > 0]
			lats = [float(data[load]["packet_latency"]["avg"]) for load in data if len(data[load]) > 0]
			lats = [x for _, x in sorted(zip(loads, lats))]
			loads = sorted(loads)
			ax[i].plot(loads, lats, color = cfg.plotting_color_map[algo], marker = "x", label = algo.upper())
		ax[i].legend()
		ax[i].set_ylim(0,500)
		ax[i].grid()

	plt.savefig("plots/lat_vs_load_%s.pdf" % exp)

# Create heatmaps for synthetic traffic
def create_synthetic_heatmap(names):
	algorithms = []
	
	# Extract algorithms
	for exp in names:
		params = cfg.experiment_list[exp]
		for algo in params["algorithms"]:
			if algo not in algorithms:
				algorithms.append(algo)
	real_algorithms = [x for x in algorithms if x != "bl"]

	# Compose data
	lat_data = []
	tp_data = []
	for traffic in ["C2C","C2M","C2I","M2I"]:
		lat_data_row = []
		tp_data_row = []
		labs1 = []
		for exp in names:
			fac = 2 # If the latency exceeds fac * zero-load-latency, we regard the network as saturated.
			baseline_data = hlp.read_file("./RapidChiplet/results/%s_%s_%s.json" % (exp, "bl", traffic))
			baseline_lat = float(baseline_data["0.001"]["packet_latency"]["avg"])
			baseline_tp = max([float(load) for load in baseline_data if len(baseline_data[load]) > 0 and baseline_data[load]["packet_latency"]["avg"] < fac * baseline_lat]) * 100
			for algo in real_algorithms:
				labs1.append(algo.upper())
				data = hlp.read_file("./RapidChiplet/results/%s_%s_%s.json" % (exp, algo, traffic))
				lat = float(data["0.001"]["packet_latency"]["avg"])
				tp = max([float(load) for load in data if len(data[load]) > 0 and data[load]["packet_latency"]["avg"] < fac * lat]) * 100
				lat_data_row.append(lat / baseline_lat)
				tp_data_row.append(tp / baseline_tp)
		lat_data.append(lat_data_row)
		tp_data.append(tp_data_row)
	
	# Create heatmap
	for typ in ["latency", "throughput"]:
		if typ == "latency":
			data = lat_data
			cmap = GnRd
		if typ == "throughput":
			data = tp_data
			cmap = GnRd.reversed()
		mxdif = max([abs(1 - x) for y in data for x in y])

		fig, ax = plt.subplots(figsize = (6,2.5))
		plt.subplots_adjust(left=0.05, right = 0.975, top = 0.9, bottom = 0.19, wspace = 0.5)
		im = ax.imshow(data, cmap = cmap, vmin = 1.0 - mxdif, vmax = 1.0 + mxdif)

		ax.set_yticks(list(range(4)), labels = ["C2C","C2M","C2I","M2I"])
		ax.set_xticks(np.arange(len(labs1)), labels=labs1)
		for i in range(len(names)):
			x = i * len(real_algorithms) + 1
			txt = names[i].replace("_large","").replace("_"," ")
			txt = txt[:2] + " " + txt[2:] + "g."
			ax.text(x, 4.3, txt, ha = "center")	

		for i1 in range(4):
			for j in range(len(names)):
				for k in range(len(real_algorithms)):
					i2 = j * len(real_algorithms) + k
					txt = str(round(100 * data[i1][i2])) + "%"
					text = ax.text(i2, i1, txt, ha="center", va="center", color="black")

		ax.set_ylabel("Traffic Type")
		fig.tight_layout()
		plt.savefig("plots/synthetic_heatmap_%s.pdf" % typ)

# Create bars-plot for evaluation on real traces
def create_trace_bars(names):
	algorithms = []
	traces = []
	
	# Extract algorithms
	for exp in names:
		params = cfg.experiment_list[exp]
		for algo in params["algorithms"]:
			if algo not in algorithms:
				algorithms.append(algo)
		for trace in params["eval_traces"]:
			if trace not in traces:
				traces.append(trace)

	real_algorithms = [x for x in algorithms if x != "bl"]

	# Collect data and create plot
	for ntc in [0,1]:
		fig, ax = plt.subplots(figsize = (3,2.5))
		plt.subplots_adjust(left=0.2, right = 0.99, top = 0.975, bottom = 0.27)
		cnt = 0
		labs = []
		for (i, exp) in enumerate(names):
			txt = exp.replace("_","\n") + "g."
			txt = txt[:2] + " " + txt[2:]
			x = i * (len(traces) + 0.33) * len(real_algorithms) + 1
			ax.text(x, (0.6 if mode == "appendix" else 0.66), txt, ha = "center", fontsize = 9)
			for (j, trace) in enumerate(traces):		
				baseline_data = hlp.read_file("./RapidChiplet/results/%s_%s_%s_%d.json" % (exp, "bl", trace, ntc))
				baseline_apl = baseline_data["1.0"]["network_latency"]["avg"]
				for (k, algo) in enumerate(real_algorithms):
					labs.append(algo.upper())
					try:
						data = hlp.read_file("./RapidChiplet/results/%s_%s_%s_%d.json" % (exp, algo, trace, ntc))
						apl = data["1.0"]["network_latency"]["avg"]
					except Exception as e:
						print(e)
						print("File %s not found..." % ("./RapidChiplet/results/%s_%s_%s_%d.json" % (exp, algo, trace, ntc)))
						apl = float("inf")
					speedup = baseline_apl / apl
					ax.bar(cnt, speedup, color = cfg.plotting_color_map[algo], zorder = 3)
					cnt += 1
				cnt += 1
				labs.append("")
			ax.plot([cnt-1,cnt-1],[0,2],color = "#000000", linewidth = 0.5)

		ticks = [i for i in range(len(labs)) if labs[i] != ""]
		labs = [x for x in labs if x != ""]

		ax.set_ylim(0.8,(1.4 if mode == "appendix" else 1.2))
		ax.plot([-1,cnt],[1,1], color = "#666666", linewidth = 2)
		ax.fill_between([-1,cnt], [1.0,1.0], [2.0,2.0], color='#009900', alpha=0.2)
		ax.fill_between([-1,cnt], [0.0,0.0], [1.0,1.0], color='#990000', alpha=0.2)
		ax.set_xticks(ticks)
		ax.set_xticklabels(labs, rotation = 90, fontsize = 9)
		ax.set_ylabel("Speedup over Baseline")
		ax.grid(axis = "y", color = "#666666", zorder = 0)
		ax.set_xlim(-0.75,cnt-1.25)
		plt.savefig("plots/trace_bars_%d.pdf" % ntc)

# Create trace heat map
def create_trace_heatmap(names):
	base_path = "RapidChiplet/results/"
	algorithms = []
	traces = []
	
	# Extract algorithms and traces
	for exp in names:
		params = cfg.experiment_list[exp]
		for algo in params["algorithms"]:
			if algo not in algorithms:
				algorithms.append(algo)
		for trace in params["partial_eval_traces"]:
			if trace not in traces:
				traces.append(trace)

	# Fix to remove vips-trace because of simulator issues
	if mode == "appendix" and "vips_64c_simmedium" in traces:
		traces.remove("vips_64c_simmedium")

	# Remove baseline from algorithms
	real_algorithms = [x for x in algorithms if x != "bl"]

	tmp = []

	netrace_cycles = 1
	# Create one plot per experiment
	for exp in names:	
		data = []
		# Create one row per trace
		for trace in traces:
			row = []
			regions = cfg.experiment_list[exp]["trace_region_counts"][trace]
			xlabs = []
			# Create one block of columns per trace-region
			for region in range(regions):
				# Read the baseline data
				results_file = base_path + "%s_%s_%s_%d_reg%d.json" % (exp, "bl", trace, netrace_cycles, region)
				baseline = hlp.read_file(results_file) if Path(results_file).exists() else None
				# Create one column per algorithm
				for algo in real_algorithms:
					xlabs.append(algo.upper())
					results_file = base_path + "%s_%s_%s_%d_reg%d.json" % (exp, algo, trace, netrace_cycles, region)
					placeit = hlp.read_file(results_file) if Path(results_file).exists() else None
					if baseline != None and placeit != None and "packet_latency" in baseline["1.0"] and "packet_latency" in placeit["1.0"]:
						latency_percentage = placeit["1.0"]["packet_latency"]["avg"] / baseline["1.0"]["packet_latency"]["avg"]
						tmp.append(latency_percentage)
						row.append(latency_percentage)
					else:
						row.append(float("NaN"))
			data.append(row)
		# Create plot
		fig, ax = plt.subplots(figsize = (6,2.3))
		plt.subplots_adjust(left=0.15, right = 0.99, top = 0.99, bottom = 0.05)
		# mxdif = max([abs(1 - x) for y in data for x in y])
		# Unify color over all heatmaps
		mxdif = 0.5
		masked_data = np.ma.array(data, mask=np.isnan(data))
		cmap = GnRd
		cmap.set_bad("#CCCCCC",1.)
		im = ax.imshow(masked_data, cmap = cmap, vmin = 1.0 - mxdif, vmax = 1.0 + mxdif, aspect = 0.61)
		# Add text to plots
		for i in range(len(data)):
			for j in range(len(data[i])):
				if not math.isnan(data[i][j]):
					txt = str(round(100 * data[i][j])) + "%"
					ax.text(j, i, txt, ha="center", va="center", color="black", fontsize = 7)
		# Set y-ticks
		ax.set_yticks(list(range(len(traces))))
		ax.set_yticklabels([x.split("_")[0] for x in traces])
		# Set x-ticks
		ax.set_xticks(list(range(len(xlabs))))
		ax.set_xticklabels(xlabs)
		for i in range(regions):
			x = i * len(real_algorithms) + 1
			txt = "Region %d" % (i+1)
			ypos = 9.5 if mode == "appendix" else 10.5
			ax.text(x, ypos, txt, ha = "center")	

		# Store plot
		fig.tight_layout()
		plt.savefig("plots/trace_heatmap_%s_%d.pdf" % (exp, netrace_cycles))
	print(sum(tmp)/len(tmp))

# Create trace heat map
def plot_speedup_vs_inj_rate(names):
	base_path = "RapidChiplet/results/"
	algorithms = []
	traces = []
	
	# Extract algorithms and traces
	for exp in names:
		params = cfg.experiment_list[exp]
		for algo in params["algorithms"]:
			if algo not in algorithms:
				algorithms.append(algo)
		for trace in params["partial_eval_traces"]:
			if trace not in traces:
				traces.append(trace)

	real_algorithms = [x for x in algorithms if x != "bl"]

	# Create plot
	fig, ax = plt.subplots(figsize = (3,3))
	plt.subplots_adjust(left=0.2, right = 0.99, top = 0.99, bottom = 0.15)

	# Compose data
	inj_rates = []
	rel_latencies = []
	colors = []
	netrace_cycles = 1
	# Experiments
	base_colors = ["#000099","#009900","#990000","#990099"]
	for (eidx, exp) in enumerate(names):	
		# Traces  
		for trace in traces:
			regions = cfg.experiment_list[exp]["trace_region_counts"][trace]
			# Trace Regions
			for region in range(regions):
				# Read the baseline data
				results_file = base_path + "%s_%s_%s_%d_reg%d.json" % (exp, "bl", trace, netrace_cycles, region)
				baseline = hlp.read_file(results_file) if Path(results_file).exists() else None
				# Use injection rate from baseline
				# Algorithms
				for algo in real_algorithms:
					results_file = base_path + "%s_%s_%s_%d_reg%d.json" % (exp, algo, trace, netrace_cycles, region)
					placeit = hlp.read_file(results_file) if Path(results_file).exists() else None
					if baseline != None and placeit != None and "packet_latency" in baseline["1.0"] and "packet_latency" in placeit["1.0"]:
						inj_rates.append(baseline["1.0"]["injected_flit_rate"]["avg"] * 100)
						rel_latencies.append(placeit["1.0"]["packet_latency"]["avg"] / baseline["1.0"]["packet_latency"]["avg"])
						colors.append(base_colors[eidx])

	print("AVG: ", sum(rel_latencies) / len(rel_latencies))

	# Create plot
	ax.scatter(inj_rates, rel_latencies, s=10, facecolors='none', edgecolors=colors, zorder = 3, linewidth = 0.5)
	ax.set_ylabel("Relative Latency [%]")
	ax.set_xlabel("Injection rate")
	ax.grid(zorder = 0)

	# Store plot
	plt.savefig("plots/speedup_vs_inj_rate.pdf")



		
# Plots can be created manually	
if __name__ == "__main__":	

	args = sys.argv[1:]

	if len(args) < 2:
		print("usage: plots.py <plot_type> <file-name or experiment-name>")
		sys.exit()

	plot_type = args[0]
	name = args[1]

	matplotlib.rc('pdf', fonttype=42)

	if plot_type == "random":
		if len(args) < 3:
			print("plotting random evaluations needs the <experiment> as an additional argument.")
			print("usage: plots.py random <file-name> <experiment-name>")
			sys.exit()
		exp = args[2]
		plot_random_instances(name, exp)
	elif plot_type == "sa_debug":
		plot_sa_debug(name, False)
	elif plot_type == "sac_debug":
		plot_sa_debug(name, True)
	elif plot_type == "ga_debug":
		plot_ga_debug(name)
	elif plot_type == "res_evol":
		plot_result_evolution(name)
	elif plot_type == "res_eval":
		plot_result_evaluation(name)
	elif plot_type == "res_dist":
		plot_result_distribution(name)
	elif plot_type == "ninst":
		plot_ninstances(name)
	elif plot_type == "all":
		plot_result_evolution(name)
		plot_result_evaluation(name)
		plot_result_distribution(name)
		plot_ninstances(name)
	elif plot_type == "res_eval_comb":
		plot_result_evaluation(name, combined = True)
	elif plot_type == "lat_vs_load":
		plot_lat_vs_load(name)
	elif plot_type == "synth_heatmap":
		create_synthetic_heatmap(["32cores_homo","64cores_homo","32cores_hetero","64cores_hetero"])
	elif plot_type == "trace_heatmap":
		create_trace_heatmap(["32cores_homo","64cores_homo","32cores_hetero","64cores_hetero"])
	elif plot_type == "trace_bars":
		create_trace_bars(["32cores_homo","64cores_homo","32cores_hetero","64cores_hetero"])
	elif plot_type == "su_vs_ir":
		plot_speedup_vs_inj_rate(["32cores_homo","64cores_homo","32cores_hetero","64cores_hetero"])
