# Import python libraries
import sys
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as ptch

# Import RapidChiplet files
import helpers as hlp
import global_config as cfg

# Visualize a single chiplet
def visualize_chiplet(chiplet_name, chiplet):
	# Initialize the plot
	fix, ax = plt.subplots()	
	ax.set_xlim(0,chiplet["dimensions"]["x"]) 
	ax.set_ylim(0,chiplet["dimensions"]["y"]) 
	plt.axis("off")
	plt.axis('equal')
	# Plot chiplet
	ax.add_patch(ptch.Rectangle((0,0), chiplet["dimensions"]["x"], chiplet["dimensions"]["y"], edgecolor = "#000000", facecolor = cfg.chiplet_colors[chiplet["type"]]))
	# Plot PHYs
	radius = max(chiplet["dimensions"]["x"], chiplet["dimensions"]["y"]) / 50
	fontsize = min(chiplet["dimensions"]["x"], chiplet["dimensions"]["y"]) * 2
	for (pid, phy) in enumerate(chiplet["phys"]):
		ax.add_patch(ptch.Circle((phy["x"], phy["y"]), radius = radius, edgecolor = "#000000", facecolor = "#000000"))
		ax.text(phy["x"], phy["y"], str(pid), ha = "center", va = "center", color = "#FFFFFF", fontsize = fontsize)
	plt.savefig("visualizations/chiplet_%s.pdf" % chiplet_name)
	

if __name__ == "__main__":
	# Read command line arguments
	parser = argparse.ArgumentParser()	
	parser.add_argument("-cf", "--chiplet_file", required = True, help = "Path to the \"chiplets\" input file") 
	parser.add_argument("-cn", "--chiplet_name", required = True, help = "Name of the chiplet to visualize") 
	args = parser.parse_args()
	# Read the chiplet file
	chiplets = hlp.read_file(filename = args.chiplet_file)
	# Visualize the chiplet
	if args.chiplet_name in chiplets:
		visualize_chiplet(chiplet_name = args.chiplet_name, chiplet = chiplets[args.chiplet_name])
	else:
		print("error: The chiplet \"%s\" was not found in the chiplet file \"%s\"." % (args.chiplet_name, args.chiplet_file))
		sys.exit()
	
