'''
clip.py: Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing

Copyright: (c) 2015 William Gaul
License: MIT, see LICENSE for more details
'''
import itertools
import shlex
import sys
import uuid


########################################
# COMPATIBILITY & UTILITIES
########################################

PY2 = sys.version_info[0] == 2

input = raw_input if PY2 else input
text_type = basestring if PY2 else str
def is_func(e):
	return hasattr(e, '__call__')
def iteritems(d):
	return d.iteritems() if PY2 else d.items()

def get_input_fn(f=None, invisible=False):
	if f is not None:
		return f
	if not invisible:
		return input
	import getpass
	return getpass.getpass

def prompt_fn(f, s, default=None, type=None, skip=False, repeat=False):
	default = default or ''
	while True:
		try:
			ret = f(s) or (default() if is_func(default) else default)
			if skip and not ret:
				return None
			ret = type(ret) if type is not None else ret
		except (KeyboardInterrupt, EOFError):
			raise_abort()
		except ValueError:
			echo('Please provide an {}'.format(type.__name__))
		else:
			if ret or not repeat:
				return ret

def determine_type(t, default):
	if t is None:
		if default is not None:
			if isinstance(default, list):
				return type(default[0]) if len(default) > 0 else None
			return None if is_func(default) else type(default)
		return None
	return t


########################################
# GLOBAL CLASSES/METHODS
########################################

class ClipGlobals(object):

	def __init__(self):
		self._streams = {}

	def _write(self, message, stream, nl=True):
		stream.write(str(message) + ("\n" if nl else ""))
		# Custom streams may not implement a flush() method
		if hasattr(stream, 'flush'):
			stream.flush()

	def _broadcast(self, message, err=False, nl=True):
		for k, v in iteritems(self._streams):
			self._write(message, v['err' if err else 'out'], nl)

	def echo(self, message, err=False, nl=True, app=None):
		if not self._streams:
			raise AttributeError('No streams have been initialized')
		if app is None:
			self._broadcast(message, err, nl)
		else:
			self._write(message, self._streams[app]['err' if err else 'out'], nl)

	def add_streams(self, out, err, app=None):
		self._streams[app] = {
			'out': out or sys.stdout,
			'err': err or sys.stderr
		}


class ClipExit(Exception):
	def __init__(self, message=None, status=0):
		self.message = message or 'clip exiting with status {}'.format(status)
		self.status = status
	def __str__(self):
		return repr(self.message)


clip_globals = ClipGlobals()

def echo(message, err=False, nl=True, app=None):
	clip_globals.echo(message, err, nl, app)

def exit(message=None, err=False, app=None):
	if message:
		echo(message, err, app=app)
	raise ClipExit(message, 1 if err else 0)

def raise_abort():
	exit('Operation aborted by user', True)

def confirm(prompt, default=None, show_default=True, abort=False, input_function=None):
	'''Prompts for confirmation from the user.
	'''
	valid = {
		'yes': True,
		'y': True,
		'no': False,
		'n': False
	}
	input_function = get_input_fn(input_function)
	if default not in ['yes', 'no', None]:
		default = None
	if show_default:
		prompt = '{} [{}/{}]: '.format(prompt,
				'Y' if default == 'yes' else 'y',
				'N' if default == 'no' else 'n')
	while True:
		choice = prompt_fn(input_function, prompt, default).lower()
		if choice in valid:
			if valid[choice] == False and abort:
				raise_abort()
			return valid[choice]
		else:
			echo('Please respond with "yes" or "no" (or "y" or "n").')

def prompt(text, default=None, show_default=True, invisible=False,
           confirm=False, skip=False, type=None, input_function=None):
	'''Prompts for input from the user.
	'''
	t = determine_type(type, default)
	input_function = get_input_fn(input_function, invisible)
	if default is not None and show_default:
		text = '{} [{}]: '.format(text, default)
	while True:
		val = prompt_fn(input_function, text, default, t, skip, repeat=True)
		if not confirm or (skip and val is None):
			return val
		if val == prompt_fn(input_function, 'Confirm: ', default, t, repeat=True):
			return val
		echo('Error: The two values you entered do not match', True)


########################################
# PARAMETER METHODS
########################################

def _memoize_param(f, param):
	if isinstance(f, Command):
		f._params.add(param)
	else:
		if not hasattr(f, '__clip_params__'):
			f.__clip_params__ = []
		f.__clip_params__.append(param)

def _make_param(cls, param_decls, **attrs):
	def decorator(f):
		_memoize_param(f, cls(param_decls, **attrs))
		return f
	return decorator

def arg(*param_decls, **attrs):
	return _make_param(Argument, param_decls, **attrs)

def opt(*param_decls, **attrs):
	return _make_param(Option, param_decls, **attrs)

def flag(*param_decls, **attrs):
	return _make_param(Flag, param_decls, **attrs)


########################################
# PARAMETER CLASSES
########################################

class Parameter(object):
	'''Base class for all parameters associated with a command.

	A parameter consists of several *parameter declarations* followed by
	keyword *attributes*. The parameter declarations represent the parameter
	as it would be entered by users, e.g. 'arg' or ('-o', '--opt').
	'''

	def __init__(self, param_decls, name=None, nargs=1, default=None,
	             type=None, required=False, callback=None, hidden=False,
	             inherit_only=False, help=None):
		self._decls = param_decls
		self._name = name or self._make_name(param_decls)
		self._nargs = nargs
		self._default = self._make_default(default, nargs)
		self._type = determine_type(type, self._default)
		self._required = required
		self._callback = callback
		self._hidden = hidden
		self._inherit_only = inherit_only
		self._help = help

		self.reset()  # Do an initial reset to prime the parameter

	def reset(self):
		self._value = None  # The parsed value of this parameter
		self._satisfied = False  # True when this parameter has consumed tokens

	def _make_name(self, decls):
		raise NotImplementedError('_make_name/1 must be implemented by child classes')

	def _make_default(self, default, nargs):
		# The default is a function, just assume it returns the correct type
		if is_func(default):
			return default
		if nargs != 0 and nargs != 1:
			default = default or []
			if not isinstance(default, list):
				raise TypeError('Default value must be list with nargs={}'.format(nargs))
		return default

	def _get_help_name(self):
		return self._name

	def _get_help(self):
		name = [self._get_help_name()]
		if self._nargs != 0:
			name.append('[{}{}]'.format(
					self._type.__name__ if self._type else 'text',
					'' if self._nargs == 1 else '...'))
		desc = []
		if self._help is not None:
			desc.append(self._help)
		if self._default:
			desc.append('(default: {})'.format(self._default))
		return [' '.join(name), ' '.join(desc)]

	def name(self):
		return self._name

	def hidden(self):
		return self._hidden

	def inherit_only(self):
		return self._inherit_only

	def value(self):
		return self._value

	def satisfied(self):
		return self._satisfied

	def consume(self, tokens):
		'''Have this parameter consume some tokens.

		This stores the consumed value for later use and returns the
		modified tokens array for further processing.
		'''
		n = len(tokens) if self._nargs == -1 else self._nargs
		if n > len(tokens):
			exit('Error: Not enough arguments for "{}".'.format(self._name), True)
		try:
			consumed = [self._type(e) if self._type is not None else e for e in tokens[:n]]
		except ValueError as e:
			exit('Error: Invalid type given to "{}", expected {}.'.format(
					self._name, self._type.__name__), True)
		if n == 1 and self._nargs == 1:
			consumed = consumed[0]
		self.post_consume(consumed)
		return tokens[n:]

	def post_consume(self, consumed):
		self._value = consumed
		self._satisfied = True
		# Parameter has been matched, so invoke the callback if any
		if self._callback is not None:
			self._callback(self._value)

	def set_default(self):
		# If we're calling this method, then this parameter wasn't provided
		if self._required:
			exit('Error: Missing parameter "{}".'.format(self._name), True)
		# The provided default can be a function, whose return value will be used
		self._value = self._default() if is_func(self._default) else self._default

	def matches(self, token):
		return not self._satisfied


class Argument(Parameter):
	'''A positional parameter.
	'''

	def _make_name(self, decls):
		if not len(decls) == 1:
			raise TypeError('Arguments take exactly 1 parameter declaration, got {}'.format(len(decls)))
		return decls[0]


class Option(Parameter):
	'''A (usually) optional parameter.
	'''

	def __init__(self, param_decls, **attrs):
		Parameter.__init__(self, param_decls, **attrs)

	def _make_name(self, decls):
		longest = sorted(list(decls), key=lambda x: len(x))[-1]
		return longest[2:].replace('-', '_').lower() if len(longest) > 2 else longest[1:]

	def _get_help_name(self):
		return ', '.join(self._decls)

	def consume(self, tokens):
		tokens.pop(0)  # Pop the opt from the tokens array
		return Parameter.consume(self, tokens)


class Flag(Option):
	'''A special option that consumes nothing and is True only if it appears.
	'''

	def __init__(self, param_decls, **attrs):
		attrs['nargs'] = 0
		attrs['default'] = False
		Option.__init__(self, param_decls, **attrs)

	def consume(self, tokens):
		tokens.pop(0)  # Pop the flag from the tokens array
		Parameter.post_consume(self, True)
		return tokens


class ParameterDict(object):

	def __init__(self, params):
		self._args = []
		self._opts = []
		self._args_map = {}
		self._opts_map = {}
		for param in params:
			self.add(param)

	def __contains__(self, key):
		return key in self._args_map or key in self._opts_map

	def __getitem__(self, key):
		if key in self._args_map:
			return self._args[self._args_map[key]]
		return self._opts[self._opts_map[key]]

	def add(self, param):
		l, m = (self._args, self._args_map) if isinstance(param, Argument) else (self._opts, self._opts_map)
		i = len(l)
		l.append(param)
		for decl in param._decls:
			m[decl] = i
		m[param.name()] = i

	def match(self, token):
		match = None
		if token in self._opts_map:
			possible = self._opts[self._opts_map[token]]
			if possible.matches(token):
				match = possible
		if match is None:
			for arg in self._args:
				if arg.matches(token):
					match = arg
					break
		return match

	def unsatisfied(self):
		return [p for p in self.all() if not p.satisfied()]

	def all(self):
		return self._args + self._opts

	def arguments(self):
		return self._args

	def options(self):
		return self._opts


########################################
# COMMAND METHODS
########################################

def _make_command(f, name, attrs):
	if isinstance(f, Command):
		raise TypeError('Callback is already a Command')
	try:
		params = f.__clip_params__
		params.reverse()
		del f.__clip_params__
	except AttributeError:
		params = []
	return Command(name=name or f.__name__.lower(), callback=f, params=params, **attrs)

def command(name=None, **attrs):
	def decorator(f):
		return _make_command(f, name, attrs)
	return decorator


########################################
# COMMAND CLASS
########################################

class Command(object):

	def __init__(self, name, callback, params, parent=None, default=None,
	             description=None, epilogue=None, inherits=None, tree_view=None):
		self._name = name
		self._callback = callback
		self._parent = parent
		self._default = default
		self._description = description
		self._epilogue = epilogue

		self._inherited = []
		# Add help to every command and shim in inherited parameters
		params.insert(0, Flag(('-h', '--help'), callback=self.help, hidden=True,
		                      help='Show this help message and exit'))
		if inherits is not None:
			if self._parent is None:
				raise AttributeError('A main function cannot inherit parameters')
			for e in inherits:
				param = self._parent._get_inherited_param(e)
				params.append(param)
				self._inherited.append(param.name())
		self._params = ParameterDict(params)
		# Handle tree view
		if tree_view is not None:
			c = self._params[tree_view]
			if not isinstance(c, Flag):
				raise TypeError('tree_view must be a Flag')
			c._callback = self.tree_view

		self._subcommands = {}

	def reset(self):
		# Reset all parameters associated with this command
		for param in self._params.all():
			param.reset()
		# Recurse into subcommands
		for v in self._subcommands.values():
			v.reset()

	def __call__(self, *args, **kwargs):
		return self._callback(*args, **kwargs)

	def _get_help(self):
		return [self._name, self._description or '']

	def _get_path(self):
		path = self._parent._get_path() if self._parent is not None else []
		return path + [self._name]

	def _get_inherited_param(self, name):
		if name in self._params:
			return self._params[name]
		if self._parent is not None:
			return self._parent._get_inherited_param(name)
		raise AttributeError('Unable to inherit parameter "{}"'.format(name))

	def name(self):
		return self._name

	def subcommand(self, name=None, **attrs):
		def decorator(f):
			attrs['parent'] = self
			cmd = command(name, **attrs)(f)
			self._subcommands[cmd._name] = cmd
			return cmd
		return decorator

	def parse(self, tokens):
		parsed = {}

		if not tokens and self._default is not None:
			tokens = self._default.split()

		# Pass 1: Forward - fill out parameter values based on input string
		while tokens:
			token = tokens[0]
			if token in self._subcommands:
				tokens.pop(0)
				parsed[token] = self._subcommands[token].parse(tokens)
				break  # The subcommand handles the remaining tokens
			match = self._params.match(token)
			if not match:
				exit('Error: Could not understand "{}".'.format(token), True)
			tokens = match.consume(tokens)

		# Pass 2: Backward - fill out missing parameters
		for param in self._params.unsatisfied():
			param.set_default()

		# Pass 3: Build the JSON-serializable object to return
		for param in self._params.all():
			if not param.hidden() and (param.name() in self._inherited or not param.inherit_only()):
				parsed[param.name()] = param.value()

		return parsed

	def invoke(self, parsed):
		# First invoke this command's callback
		self._callback(**{k: v for k, v in iteritems(parsed) if k not in self._subcommands})
		# Invoke subcommands (realistically only one should be invoked)
		for k, v in iteritems(parsed):
			if k in self._subcommands:
				self._subcommands[k].invoke(v)

	def help(self, value):
		help_parts = []
		usage = []

		# Header
		header = ' '.join(self._get_path())
		if self._description is not None:
			header = '{}: {}'.format(header, self._description)
		help_parts.append(header)

		# Main help sections (title, followed by 2-column list)
		def make_help_section(l, title):
			data = [e._get_help() for e in l]
			width = max(len(e[0]) for e in data) + 2
			return '\n'.join([title] + ['  {}{}'.format(e[0].ljust(width), e[1]) for e in data])

		args = self._params.arguments()
		if args:
			usage.append('{{arguments}}')
			help_parts.append(make_help_section(args, 'Arguments:'))
		opts = self._params.options()
		if opts:
			usage.append('{{options}}')
			help_parts.append(make_help_section(opts, 'Options:'))
		subs = sorted(self._subcommands.values(), key=lambda e: e.name())
		if subs:
			usage.append('{{subcommand}}')
			help_parts.append(make_help_section(subs, 'Subcommands:'))

		# Now we know the usage string, so insert it
		help_parts.insert(1, 'Usage: {} {}'.format(self._name, ' '.join(usage)))

		# Epilogue
		if self._epilogue is not None:
			help_parts.append(self._epilogue)

		exit('\n\n'.join(help_parts))

	def tree_view(self, value):
		echo('{}{}'.format(" " * (value - 1), self._name))
		subs = sorted(self._subcommands.values(), key=lambda e: e.name())
		if subs:
			for sub in subs:
				sub.tree_view(value + 2)
		if value == 1:
			exit()


########################################
# APP CLASS
########################################

class App(object):

	def __init__(self, stdout=None, stderr=None, name=None):
		self._main = None
		self._name = name or str(uuid.uuid4())
		clip_globals.add_streams(stdout, stderr, self._name)

	def _ping_main(self):
		if self._main is None:
			raise AttributeError('A main function must be assigned to this app')

	def main(self, name=None, **attrs):
		def decorator(f):
			if self._main is not None:
				raise AttributeError('A main function has already been assigned to this app')
			cmd = command(name, **attrs)(f)
			self._main = cmd
			return cmd
		return decorator

	def echo(self, message, err=False, nl=True):
		echo(message, err, nl, app=self._name)

	def exit(self, message=None, err=False):
		exit(message, err, app=self._name)

	def parse(self, tokens):
		'''Parses a list of tokens into a JSON-serializable object.

		The parsing proceeds from left to right and is greedy.

		Precedence order:
		  1. Parameters with active context. For example, an Option with
		     nargs=-1 will gobble all the remaining tokens.
		  2. Subcommands.
		  3. Parameters.

		The keys of the returned object are the names of parameters or
		subcommands. Subcommands are encoded as nested objects. Multiple
		parameters are encoded as lists. All other values are encoded as
		parameter-specified data types, or strings if not specified.
		'''
		self._ping_main()

		# Pre-parsing:
		#   1. Expand globbed options: -abc --> -a -b -c
		def is_globbed(s):
			return len(s) > 2 and s.startswith('-') and not s.startswith('--')
		expanded = [["-" + c for c in list(token[1:])] if is_globbed(token) else [token] for token in tokens]

		# Parsing: pass off to main command after flattening expanded tokens list
		return self._main.parse(list(itertools.chain.from_iterable(expanded)))

	def invoke(self, parsed):
		'''Invokes the app, given a parsed token object.
		'''
		self._ping_main()
		self._main.invoke(parsed)

	def reset(self):
		'''Returns the app to its initial state.

		This is necessary because parsing/invoking causes state to be stored
		in the commands and parameters, meaning that the app cannot be run
		again. After a reset, the app is freely available for reuse.
		'''
		self._ping_main()
		self._main.reset()

	def run(self, tokens=None):
		if tokens is None:
			tokens = sys.argv[1:]
		if isinstance(tokens, text_type):
			tokens = shlex.split(tokens)
		try:
			self.invoke(self.parse(tokens))
		finally:
			self.reset()  # Clean up so the app can be used again
		return self
