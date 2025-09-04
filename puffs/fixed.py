import math
import random

def clamp(value, lo, hi):
	return lo if value < lo else hi if value > hi else value

def toU(value, width, prec):
	return clamp(int(math.floor(value*(2.0**prec))), 0, 2**width-1)

def toS(value, width, prec):
	return clamp(int(math.floor(value*(2.0**prec))), -2**(width-1), 2**(width-1)-1)

def uToFloat(value, prec):
	return float(value)/(2.0**prec)

def sToFloat(value, width, prec):
	return float(value)/(2.0**prec)

def uMaxFloat(width, prec):
	return (2.0**(width-prec))

def sMaxFloat(width, prec):
	return (2.0**(width-prec-1))

def sMinFloat(width, prec):
	return -(2.0**(width-prec-1))

def floatStep(prec):
	return (0.5**prec)

def floatEqual(v0, v1, prec):
	return abs(v0 - v1) <= floatStep(prec)

def uRandFloat(width, prec):
	step = floatStep(prec)
	hi = uMaxFloat(width, prec)
	return math.floor(random.uniform(0.0, hi)/step)*step

def uRand(width):
	return random.randint(0, 2**width-1)

def sRand(width):
	return random.randint(-2**(width-1), 2**(width-1)-1)

def sRandFloat(width, prec):
	step = floatStep(prec)
	lo = sMinFloat(width, prec)
	hi = sMaxFloat(width, prec)
	return math.floor(random.uniform(lo, hi)/step)*step

def uClampFloat(value, width, prec):
	return clamp(value, 0.0, uMaxFloat(width, prec))

def sClampFloat(value, width, prec):
	return clamp(value, sMinFloat(width, prec), sMaxFloat(width, prec))
