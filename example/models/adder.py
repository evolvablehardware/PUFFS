class Model:
	def __init__(self, A, B, S, log=None):
		self.A = A
		self.B = B
		self.S = S

		# Internal state (none needed for pure adder)
		self.log = log

	def cycle(self):
		while True:
			if not self.A.isValid() or not self.B.isValid():
				return

			self.S.send(self.A.recv() + self.B.recv())
