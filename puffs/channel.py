import cocotb
from cocotb.triggers import Timer
from cocotb.triggers import RisingEdge
from cocotb.triggers import FallingEdge
from cocotb.clock import Clock
from cocotb.binary import BinaryValue

import random
from puffs import fixed

def randomInt(bounds):
	if isinstance(bounds, list):
		return [randomInt(bound) for bound in bounds]
	elif isinstance(bounds, tuple):
		return random.randint(int(bounds[0]), int(bounds[1])-1)

def randomReal(bounds):
	if isinstance(bounds, list):
		return [randomReal(bound) for bound in bounds]
	elif isinstance(bounds, tuple):
		return random.uniform(bounds[0], bounds[1])

class Logger:
	def __init__(self):
		self.log = open("test.log", "w")
		self.errs = 0

	def info(self, msg):
		print(f"info: {msg}", file=self.log)

	def check(self, cond, msg):
		if not cond:
			self.error(msg)

	def error(self, msg):
		self.errs += 1
		print(f"error: {msg}", file=self.log)

	def warn(self, msg):
		print(f"warning: {msg}", file=self.log)

	def done(self):
		self.log.close()
		assert self.errs == 0, f"test failed with {self.errs} errors."

class RandomInt:
	def __init__(self, bounds=(0,2)):
		self.bounds = bounds
	
	def next(self):
		return randomInt(self.bounds)

class RandomReal:
	def __init__(self, bounds=(0,1)):
		self.bounds = bounds
	
	def next(self):
		return randomReal(self.bounds)

class TokenList:
	def __init__(self, values=[0]):
		self.values = values
		self.index = 0

	def next(self):
		result = self.values[self.index]
		self.index = (self.index+1)%len(self.values)
		return result

class Bits:
	def __init__(self, signed=False):
		self.signed = signed

	def encode(self, value):
		raise NotImplementedError()

	def decode(self, value):
		raise NotImplementedError()

	# must be a python value
	def write(self, signal, value):
		if isinstance(signal, list) and isinstance(value, list):
			for i, s in enumerate(signal):
				self.write(s, value[i])
		else:
			signal.value = self.encode(value)

	# must be a cocotb signal
	def read(self, signal):
		if isinstance(signal, list):
			return [self.read(s) for s in signal]
		elif self.signed:
			return self.decode(signal.value.signed_integer)
		return self.decode(signal.value.integer)
 
class Int(Bits):
	def __init__(self, signed=False):
		super().__init__(signed)

	def encode(self, value):
		if isinstance(value, list):
			return [self.encode(v) for v in value]
		return value
	
	def decode(self, value):
		return value

	def areEqual(self, v0, v1):
		return v0 == v1

class Fixed(Bits):
	def __init__(self, width, prec, signed=False):
		super().__init__(signed)
		self.width = width
		self.prec = prec
	
	def encode(self, value):
		if isinstance(value, list):
			return [self.encode(v) for v in value]
		elif self.signed:
			return fixed.toS(value, self.width, self.prec)
		return fixed.toU(value, self.width, self.prec)

	def decode(self, value):
		if isinstance(value, list):
			return [self.decode(v) for v in value]
		elif self.signed:
			return fixed.sToFloat(value, self.width, self.prec)
		return fixed.uToFloat(value, self.prec)

	def areEqual(self, v0, v1):
		return fixed.floatEqual(v0, v1, 5)

class Arr(Bits):
	def __init__(self, num, width, sub):
		super().__init__(sub.signed)
		self.num = num
		self.width = width
		self.sub = sub

	def off(self, i):
		return self.width * i

	def mask(self):
		return (1 << self.width)-1

	def pack(self, v, i):
		if v < 0:
			return ((~(-v)+1) & self.mask()) << self.off(i)
		return (v & self.mask()) << self.off(i)

	def unpack(self, v, i):
		result = (v >> self.off(i)) & self.mask()
		if self.signed and (result >> (self.width-1)) == 1:
			result = -((~result+1) & self.mask())
		return result

	def encode(self, value):
		result = 0
		test = []
		for i, v in enumerate(value):
			result = result | self.pack(self.sub.encode(v), i)
			test.append(self.sub.encode(v))
		#print(f"encode value={value} enc={[hex(t) for t in test]} pack={[hex(self.pack(t, i)) for i, t in enumerate(test)]} result={result:x}")
		self.decode(result)
		return result

	def decode(self, value):
		result = []
		test = []
		for i in range(0, self.num):
			result.append(self.sub.decode(self.unpack(value, i)))
			test.append(self.unpack(value, i))
		#print(f"decode value={value:x} unpack={[hex(t) for t in test]} result={result}")
		return result

	def areEqual(self, v0, v1):
		return all(self.sub.areEqual(a, b) for a, b in zip(v0, v1))

class Slice:
	def __init__(self, signal, fromIndex, toIndex=None):
		self.signal = signal
		self.fromIndex = fromIndex
		self.toIndex = fromIndex+1 if toIndex is None else toIndex
		self.n_bits = self.signal.value.n_bits

		if not hasattr(self.signal, "vivumValue"):
			self.signal.vivumValue = BinaryValue(
				"z"*self.n_bits,
				n_bits=self.n_bits,
				bigEndian=True)

	def binstrFromInt(self, i):
		if i < 0:
			i = (~(-i)+1) & ((1<<(self.toIndex-self.fromIndex))-1)
			return bin(i)[3:].rjust(self.toIndex-self.fromIndex, "1")[self.fromIndex-self.toIndex:]
		return bin(i)[2:].rjust(self.toIndex-self.fromIndex, "0")[self.fromIndex-self.toIndex:]

	def rescaleBinstr(self, s):
		return s.rjust(self.toIndex-self.fromIndex, s[-1])[self.fromIndex-self.toIndex:]

	def binstrFromValue(self, value):
		if isinstance(value, BinaryValue):
			return self.rescaleBinstr(value)
		return self.binstrFromInt(value)

	@property
	def value(self):
		return BinaryValue(
			self.signal.value.binstr[self.n_bits-self.toIndex:self.n_bits-self.fromIndex],
			n_bits=(self.toIndex - self.fromIndex),
			bigEndian=True)

	@value.setter
	def value(self, value):
		b = self.signal.vivumValue.binstr
		self.signal.vivumValue = BinaryValue(
			b[0:self.n_bits-self.toIndex] + self.binstrFromValue(value) + b[self.n_bits-self.fromIndex:],
			n_bits=self.n_bits,
			bigEndian=True)
		self.signal.value = self.signal.vivumValue

class Channel:
	def __init__(self, name, valid=None, ready=None, data=None, dtype=Int()):
		self.tokens = []
		self.index = 0

		self.name = name

		self.dtype = dtype

		# These must be cocotb signals!
		self.valid = valid
		self.ready = ready
		self.data = data

	def send(self, value):
		self.tokens.append(value)

	def recv(self):
		if self.isValid():
			result = self.tokens[self.index]
			self.index += 1
			return result
		else:
			return None

	def probe(self):
		if self.isValid():
			return self.tokens[self.index]
		else:
			return None

	def isValid(self):
		return self.index < len(self.tokens)

	def writeVerilog(self, value):
		if self.data is None:
			return
		self.dtype.write(self.data, value)

	def readVerilog(self):
		if self.data is None:
			return None
		return self.dtype.read(self.data)

class Source:
	def __init__(self, chan, values=RandomInt(), log=None):
		self.chan = chan
		self.values = values

		# Python values for the signals we drive
		self.currValid = 0
		self.currData = self.values.next()

		if self.chan.valid is not None:
			self.chan.valid.value = self.currValid
		self.chan.writeVerilog(self.currData)

		# record tokens for verification later
		self.log = log

	def cycle(self):
		ready = 1
		if self.chan.ready is not None:
			ready = self.chan.ready.value.integer

		if (self.currValid == 0 or ready != 0) and (random.randint(0,1) == 0 or self.chan.valid is None):
			self.currData = self.values.next()
			self.currValid = 1

			self.chan.send(self.currData)
			if self.log is not None:
				self.log.info(f"{self.chan.name}!{self.currData}")
		elif ready != 0:
			self.currValid = 0

		if self.chan.valid is not None:
			self.chan.valid.value = self.currValid
		self.chan.writeVerilog(self.currData)

class Sink:
	def __init__(self, chan, values=RandomInt(), log=None):
		self.chan = chan
		self.values = values

		# Python values for the signals we drive
		self.currReady = 1
		if self.chan.ready is not None:
			self.currReady = 0
			self.chan.ready.value = self.currReady

		self.prevReady = self.currReady
		self.precomputed = False

		self.log = log
		self.vtokens = []

	def precomputeReady(self):
		self.prevReady = self.currReady
		n = self.values.next()
		if n == 0:
			self.currReady = 0
		else:
			self.currReady = 1
		self.chan.ready.value = self.currReady
		self.precomputed = True

	def cycle(self):
		valid = 1
		if self.chan.valid is not None:
			valid = self.chan.valid.value.integer

		if valid != 0 and self.prevReady != 0:
			value = self.chan.recv()
			if self.chan.data is not None:
				data = self.chan.readVerilog()
				self.vtokens.append(data)
				if self.log is not None:
					self.log.info(f"{self.chan.name}?{data}")

				if self.log is not None:
					self.log.check(value is not None, f"did not expect valid token in this cycle for {self.chan.name}")
					if value is not None:
						self.log.check(self.chan.dtype.areEqual(value, data), f"expected {value} found {data} for {self.chan.name}")
			elif self.log is not None:
				self.log.info(f"{self.chan.name}?{value}")

		if self.chan.ready is not None:
			if not self.precomputed:
				n = self.values.next()
				if n == 0:
					self.currReady = 0
				else:
					self.currReady = 1
				self.chan.ready.value = self.currReady
				self.prevReady = self.currReady
			self.precomputed = False
