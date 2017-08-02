class Flat:
	class Types:
		FLAT = 0
		HOUSE = 1
		DACHA = 2
		BUILDING = 3
		SHOP = 4
		OFFICE = 5
	def __init__(self, type=Types.FLAT):
		self.type = type
