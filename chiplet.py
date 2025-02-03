# Import python libraries
import math as m

# Import our own files
from phy import PHY

class Chiplet:
	# Constructor
	def __init__(self, pos, size, typ, phys, abs_phy_pos_given = False):
		self.pos = pos 			# Bottom-left, first x, then y
		self.size = size		# First width, then height
		self.typ = typ			# Can be C, M, I
		self.rotation = 0

		# PHYs with absolute positions w.r.t. the whole placement
		if abs_phy_pos_given:
			self.phys = phys
		else:
			phys_with_abs_pos = []	
			for phy in phys:
				phys_with_abs_pos.append(PHY((self.pos[0] + phy.pos[0], self.pos[1] + phy.pos[1])))
			self.phys = phys_with_abs_pos

	# Convert the chiplet to JSON format 
	def to_json(self):
		json = {
			"pos" : self.pos,
			"size" : self.size,
			"typ" : self.typ,
			"phys" : [p.to_json() for p in self.phys],
			"rotation" : self.rotation,
		}
		return json

	# Get the position of bottom-left corner
	def get_pos(self):
		return list(self.pos)
	
	# Get the position of top-right corner
	def get_pos_inv(self):
		return [self.pos[0] + self.size[0], self.pos[1] + self.size[1]]

	# Get the center of the chiplet
	def get_center(self):
		return [self.pos[0] + self.size[0] / 2, self.pos[1] + self.size[1] / 2]

	# Move the chiplet by a given vector
	def move_by(self, vec):
		self.pos = (int(self.pos[0] + vec[0]), int(self.pos[1] + vec[1]))
		for phy in self.phys:
			phy.pos = (round(phy.pos[0] + vec[0],4), round(phy.pos[1] + vec[1],4))

	# Move the chiplet to a specific location
	def move_to(self, pos):
		vec = (pos[0] - self.pos[0],  pos[1] - self.pos[1])
		self.move_by(vec)

	# Rotate the chiplet by 0, 90, 180, or 270 degrees
	def rotate(self, angle):
		# Check that the angle is valid
		if angle not in [0,90,180,270]:
			print("ERROR: Chiplets can only be rotated by 90, 180 or 270 degrees. Angle=%s is invalid" % str(angle))
			return False	
		# Gather info 
		self.rotation = (self.rotation + angle) % 360
		rot_int = int(angle // 90)
		alpha = m.pi / 2 * rot_int
		(cx,cy) = self.get_center()
		# Update the chiplet size and position
		if rot_int % 2 == 1:
			self.size = (self.size[1], self.size[0])
			self.pos = ((cx - self.size[0]/2), (cy - self.size[1]/2))
		# Update all phys
		for phy in self.phys:
			(x, y) = (phy.pos[0] - cx, phy.pos[1] - cy)
			(xr,yr) = (x * m.cos(alpha) - y * m.sin(alpha), x * m.sin(alpha) + y * m.cos(alpha))
			phy.pos = (cx + xr, cy + yr)
		# Move chiplet back to grid in case it was offset by 0.5
		vec = (m.floor(self.pos[0]) - self.pos[0],m.floor(self.pos[1]) - self.pos[1])
		self.move_by(vec)
