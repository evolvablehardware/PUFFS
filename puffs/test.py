import os
from pathlib import Path
import inspect

import cocotb
from cocotb.clock import Clock
from cocotb.utils import get_sim_time
from cocotb.triggers import RisingEdge
import cocotb_test.simulator

class Bench:
	def __init__(self, top, test=None):
		self.root = Bench.findRoot()
		self.sim = os.getenv("SIM", "icarus")
		self.top = top
		self.test = test
		self.sources = []
		self.params = {}

	def findRoot():
		# 1) explicit override
		env_root = os.environ.get("PUFFS_TEST_ROOT")
		if env_root:
			p = Path(env_root).resolve()
			if (p / "pytest.ini").is_file():
				return p

		candidates = [Path.cwd().resolve(), Path(__file__).resolve()]
		seen = set()

		for base in candidates:
			for parent in [base] + list(base.parents):
				if parent in seen:
					continue
				seen.add(parent)
				if (parent / "pytest.ini").is_file():
					return parent

		raise FileNotFoundError("pytest.ini not found starting from CWD or puffs/test.py")

	def source(self, sources):
		if isinstance(sources, list):
			self.sources += [self.pathTo(src) for src in sources]
		else:
			self.sources.append(self.pathTo(sources))

	def param(self, params, value=None):
		if isinstance(params, dict):
			self.params = self.params | params
		elif isinstance(params, Params):
			self.params = self.params | params.toDict()
		else:
			self.params[params] = value

	def run(self):
		# Get the frame of the caller
		caller_frame = inspect.stack()[1]
		filename = caller_frame.filename

		module = os.path.splitext(os.path.basename(filename))[0]

		extra_env = {
			"PARAM_" + k: str(v) for k, v in self.params.items()
		}
		extra_env["COCOTB_RESOLVE_X"] = "RANDOM"
		if self.test:
			extra_env["COCOTB_TESTCASE"] = self.test

		testId = "_".join([str(p) for p in self.params.values()])
		buildDir = f"sim_build/{self.test}_{testId}"

		cocotb_test.simulator.run(
			verilog_sources = self.sources,
			toplevel        = self.top,
			module          = module,
			parameters      = self.params,
			extra_env       = extra_env,
			sim_build       = buildDir,
			extra_args = [
				# "--timescale", "1ns/1ps",  # Verilator
				# "-t", "1ps"           # Questa/ModelSim
				# "-g2012", "-T", "1ns"           # Icarus Verilog
			]
		)

	def pathTo(self, src):
		return str(self.root / src)

class Params:
	def __init__(self):
		prefix = "PARAM_"
		for key, value in os.environ.items():
			if key.startswith(prefix):
				attr = key[len(prefix):]
				setattr(self, attr, Params.parseEnv(value))
		cocotb.log.info("Test Parameters: " + str(self))

	def toDict(self):
		result = {}
		for key in dir(self):
			if key.startswith('_'):
				continue
			value = getattr(self, key)
			if callable(value):
				continue
			result[key] = value
		return result

	def __str__(self):
		return str(self.toDict())

	def parseEnv(value):
		try:
			return int(value)
		except ValueError:
			pass
		try:
			return float(value)
		except ValueError:
			pass
		if value.lower() in {"true", "false"}:
			return value.lower() == "true"
		return value

class Logger:
	ERROR = 0
	WARNING = 1

	def __init__(self):
		self.log = open("test.log", "w")
		self.hasError = False
		self.msgs = []

	def info(self, msg):
		print(f"{get_sim_time('ns')}\tinfo: {msg}", file=self.log)

	def check(self, cond, msg):
		if not cond:
			self.error(msg)

	def error(self, msg):
		self.hasError = True
		self.msgs.append((Logger.ERROR, get_sim_time('step'), msg))
		print(f"{get_sim_time('ns')}\terror: {msg}", file=self.log)

	def warn(self, msg):
		#self.msgs.append((Logger.WARNING, get_sim_time('step'), msg))
		print(f"{get_sim_time('ns')}\twarning: {msg}", file=self.log)

	def done(self):
		with open("dump.gtkw", "w") as gtkw:
			gtkw.write("[dumpfile] \"dump.vcd\"\n")
			gtkw.write("[savefile] \"dump.gtkw\"\n")
			line = "*1.0 0"
			for kind, t, msg in self.msgs:
				line += f" {t}"
			gtkw.write(line+"\n")
			id_char = ord('A')
			for kind, t, msg in self.msgs:
				gtkw.write(f"[markername] {chr(id_char)} {msg}\n")
				id_char += 1

		self.log.close()
		assert not self.hasError, f"test failed with {len(self.msgs)} errors."
