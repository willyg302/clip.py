try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name='clip.py',
	version='0.3.0',
	url='https://github.com/willyg302/clip.py',
	license='MIT',
	author='William Gaul',
	author_email='willyg302@gmail.com',
	description='Embeddable, composable command line interface parsing',
	py_modules=['clip'],
	include_package_data=True,
	test_suite='tests',
	platforms='any',
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3.4',
	],
)
