import json
import matplotlib.pyplot as plt

import config as cfg
import placeit_helpers as hlp
from instance import Instance

outer_reps = 50
inner_reps = 10

typ = "blueprint"
exp = "32cores_large"
params = cfg.experiment_list[exp]
params["norm_samples"] = outer_reps
params["cf_normalizers"] = hlp.compute_normalizers(params)

random_instances_outer = [Instance(typ, params) for i in range(outer_reps)]
random_instances_inner = [Instance(typ, params) for i in range(inner_reps)]


diffs = {}

diffs["Random"] = []
for inst1 in random_instances_outer:
	for inst2 in random_instances_inner:
		if inst1 == inst2:
			continue
		diffs["Random"].append(abs(inst1.get_cost() - inst2.get_cost()))


for mm in ["any","neighbors"]:
	for mm2 in ["one","both"]:
		for bias in ([0.0,0.5,1.0] if mm2 == "one" else [float("nan")]):
			lab = "%s-%s-%.1f" % (mm[0], mm2[0], bias)
			diffs[lab] = []
			params["mutation_mode"] = mm
			params["mutation_mode2"] = mm2
			params["mutation_bias"] = bias
			for inst1 in random_instances_outer:
				for i in range(inner_reps):
					inst2 = inst1.mutate()
					diffs[lab].append(abs(inst1.get_cost() - inst2.get_cost()))
	
(fig, ax) = plt.subplots(1, 1, figsize = (10, 3))
plt.subplots_adjust(left=0.15, right = 0.965, top = 0.9, bottom = 0.15)

for (i, lab) in enumerate(diffs.keys()):
	ax.violinplot([diffs[lab]], positions = [i], showmeans = True)

ax.grid()
ax.set_title("Sample size: %d (%s)" % (outer_reps * inner_reps, typ))
ax.set_ylabel("Difference in cost function")
ax.set_xticks(list(range(len(diffs))))
ax.set_xticklabels(list(diffs.keys()))

plt.savefig("plots/neighbor_similarity_%s_%s.pdf" % (typ, exp))

