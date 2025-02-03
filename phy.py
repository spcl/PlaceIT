class PHY:
	def __init__(self, pos):
		self.pos = pos

	def to_json(self):
		json = {
			"pos" : self.pos,
		}
		return json
