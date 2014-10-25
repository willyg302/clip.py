'''
clip.py: Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing

A fork of Aaargh, Copyright 2012-2013 Wouter Bolsterlee
Repo: https://github.com/wbolster/aaargh
License: OSI approved 3-clause "New BSD License"
'''
import sys

from argparse import ArgumentParser


__all__ = ['App', 'ClipExit']
_NO_FUNC = object()

# Compatibility
text_type = basestring if sys.version_info[0] >= 32 else str
try:
	input = raw_input
except NameError:
	pass


class ClipExit(Exception):
	def __init__(self, status):
		self.status = status
	def __str__(self):
		return repr(self.status)


class ClipParser(ArgumentParser):

	def __init__(self, *args, **kwargs):
		self._stdout = kwargs.pop('stdout', sys.stdout)
		self._stderr = kwargs.pop('stderr', sys.stderr)
		module = kwargs.pop('module', None)
		if module:
			kwargs.setdefault('prog', module.__name__)
			kwargs.setdefault('description', module.__doc__)
		ArgumentParser.__init__(self, *args, **kwargs)

	def _print_message(self, message, file=None):
		if message:
			if file is None:
				file = sys.stderr
			if file == sys.stdout:
				file = self._stdout
			if file == sys.stderr:
				file = self._stderr
			file.write(message)

	def exit(self, status=0, message=None):
		if message:
			self._print_message(message, self._stderr)
		raise ClipExit(status)


class App(object):

	def __init__(self, *args, **kwargs):
		self._parser = ClipParser(*args, **kwargs)
		self._global_args = []
		self._subparsers = self._parser.add_subparsers(title='subcommands', metavar='')
		self._pending_args = []
		self._defaults = {}

	def arg(self, *args, **kwargs):
		'''Add a global application argument'''
		self._global_args.append((args, kwargs))
		return self._parser.add_argument(*args, **kwargs)

	def defaults(self, **kwargs):
		'''Set global defaults'''
		return self._parser.set_defaults(**kwargs)

	def cmd(self, _func=_NO_FUNC, name=None, alias=None, *args, **kwargs):
		'''Decorator to turn a function into a subcommand'''
		if _func is not _NO_FUNC:
			# Allows for using the decorator without parentheses
			return self.cmd()(_func)

		def wrapper(func):
			subcommand = name if name is not None else func.__name__
			kwargs.setdefault('help', '')
			# Monkey-patch kwargs to pass stream info to subparser
			kwargs['stdout'] = self._parser._stdout
			kwargs['stderr'] = self._parser._stderr
			kwargs.setdefault('prog', subcommand)
			kwargs.setdefault('description', func.__doc__)
			subparser = self._subparsers.add_parser(subcommand, *args, **kwargs)
			if alias:
				if isinstance(alias, text_type):
					aliases = [alias]
				else:
					aliases = alias
				assert isinstance(aliases, (tuple, list))
				parser_map = self._subparsers._name_parser_map
				for subcommand_alias in aliases:
					parser_map[subcommand_alias] = parser_map[subcommand]

			# Add any pending arguments
			for a, k in self._pending_args:
				subparser.add_argument(*a, **k)
			self._pending_args = []

			# Add any pending default values
			try:
				pending_defaults = self._defaults.pop(None)
			except KeyError:
				pass  # No pending defaults
			else:
				self._defaults[func] = pending_defaults

			# Store callback function and return the decorated function unmodified
			subparser.set_defaults(_func=func)
			return func

		return wrapper

	def cmd_arg(self, *args, **kwargs):
		'''Decorator to specify an argument for a subcommand'''
		if len(args) == 1 and callable(args[0]) and not kwargs:
			raise TypeError('cmd_arg() decorator requires arguments, but none were supplied')

		# Remember the passed args, since the command is not yet known
		self._pending_args.append((args, kwargs))
		return lambda func: func

	def cmd_defaults(self, **kwargs):
		'''Decorator to specify defaults for a subcommand'''
		if len(kwargs) == 1 and callable(list(kwargs.values())[0]):
			raise TypeError('defaults() decorator requires arguments, but none were supplied')

		# Work-around http://bugs.python.org/issue9351 by storing the
		# defaults outside the ArgumentParser. The special key "None" is
		# used for the pending defaults for a yet-to-be defined command.
		self._defaults[None] = kwargs
		return lambda func: func

	def run(self, args=None, namespace=None, main=None):
		'''Run the application.
		If ``main`` is defined, it will become the top-level command.
		'''
		if self._pending_args:
			raise TypeError('cmd_arg() called without matching cmd()')
		if None in self._defaults:
			raise TypeError('cmd_defaults() called without matching cmd()')

		if args is None:
			args = sys.argv[1:]

		if main is not None:
			args.insert(0, main.__name__)
			subparser = self._subparsers._name_parser_map[main.__name__]
			# Add global args to subparser namespace
			for a, k in self._global_args:
				subparser.add_argument(*a, **k)
			# Inherit description from parent module
			subparser.description = self._parser.description

		kwargs = vars(self._parser.parse_args(args=args, namespace=namespace))
		sentinel = object()
		func = kwargs.pop('_func', sentinel)

		if func is sentinel:
			self._parser.error('too few arguments')

		if func in self._defaults:
			kwargs.update(self._defaults[func])

		return func(**kwargs)


	@staticmethod
	def confirm(prompt, default='yes'):
		'''Ask a yes/no question via input() and return the answer.
		``default`` is the presumed answer if the user just hits Enter.
		It must be one of 'yes', 'no', or None (answer required from user).
		'''
		valid = {
			'yes': True,
			'y': True,
			'no': False,
			'n': False
		}
		if default not in ['yes', 'no', None]:
			default = None
		while True:
			choice = input('{} [{}/{}]: '.format(prompt, 'Y' if default == 'yes' else 'y', 'N' if default == 'no' else 'n')).lower() or default
			if choice in valid:
				return valid[choice]
			else:
				print('Please respond with "yes" or "no" (or "y" or "n").')
