from setuptools import setup

setup(
	name='PUFFS',
	version='1.0.0',	
	description='Pytest Unified Framework for FPGA Simulation',
	url='https://github.com/evolvablehardware/PUFFS.git',
	author='Vivum Inc.',
	author_email='logan@vivum.ai',
	license='GPL-3.0',
	packages=['puffs'],
	install_requires=['cocotb','numpy'],

	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'Intended Audience :: Science/Research',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',  
		'Operating System :: POSIX :: Linux',		
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
	],
)

