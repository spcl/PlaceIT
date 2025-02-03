import math as m
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LinearLocator
from matplotlib import cm

deltas = [1,0.5,0.1,0.05]
iters = 12000
L = 45
t0 = 28
a = 1

xvals = [i for i in range(iters)]
yvals = []
mets = []
oyvals = []
omets = []


# New approach
for delta in deltas:
	mets.append([])
	yvals = []
	for i in range(iters):
		k = int(m.floor(i/L))
		# Exponential multiplicative cooling -> Bad
		#t = t0 * a**k
		# Logarithmically multiplicative cooling -> OK
		#t = t0 / (1 + a * m.log(1 + k))
		# Linear multiplicative cooling -> Excellent 
		t = t0 / (1 + a * k)
		# Quadratic multiplicative cooling -> OK
		# t = t0 / (1 + a * k**2)
		# BoltzExp
		#a = (1 / m.log(be_tres+2))**(2/(2*be_tres-t0))
		#t = (t0 / m.log(k+2)) if k <= be_tres else (t0 * a**(k-t0/2))
		yvals.append(t)
		mets[-1].append(m.exp(-delta / t))



(fig, ax) = plt.subplots(1, 2, figsize = (6, 3))
plt.subplots_adjust(left=0.05, right = 0.965, top = 0.9, bottom = 0.15)

ax[0].plot(xvals, yvals)
tax = ax[0].twinx()
ax[0].set_ylim(bottom = 0)
tax.set_ylim(bottom = 0)
ax[0].grid()

ax[1].set_prop_cycle(None)
for (delta, met) in zip(deltas, mets):
	ax[1].plot(xvals, met, label = str(delta))
ax[1].set_prop_cycle(None)
for (delta, met) in zip(deltas, omets):
	ax[1].plot(xvals, met, label = str(delta), linestyle = "--")

ax[1].set_ylim(bottom = 0)
ax[1].grid()
ax[1].legend()


plt.show()


