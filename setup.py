try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='clip.py',
	author='William Gaul',
	author_email='willyg302@gmail.com',
	version='0.2.2',
	url='https://github.com/willyg302/clip.py',
	license='MIT',
	py_modules=['clip'],
	include_package_data=True,
	description='Embeddable, composable command line interface parsing',
	test_suite='tests',
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3.4',
	],
)
