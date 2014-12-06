'''
clip.py: Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing
'''
import sys
import itertools


class ClipExit(Exception):
	def __init__(self, status):
		self._status = status
	def __str__(self):
		return repr(self._status)


########################################
# PARAMETER METHODS
########################################

def _memoize_param(f, param):
	if isinstance(f, Command):
		f._params.append(param)
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

def flag(*param_decls, **attrs):
	return _make_param(Flag, param_decls, **attrs)

def opt(*param_decls, **attrs):
	return _make_param(Option, param_decls, **attrs)


########################################
# PARAMETER CLASSES
########################################

class Parameter(object):

	def __init__(self, param_decls, name=None, nargs=1, default=None, **attrs):
		self._decls = param_decls
		self._name = name or self._parse_name(param_decls)
		self._nargs = nargs
		self._default = default

		self._satisfied = False  # True when this parameter has consumed tokens

	def consume(self, tokens):
		'''Have this parameter consume some tokens.
		Returns the modified tokens array and the value associated with this
		parameter to store. For example, given ['-a', 'one', 'two'] where
		-a is an option that consumes one token, this will return:
		['two'], 'one' (and 'one' will be stored as the value of 'a').
		'''
		pass


class Argument(Parameter):
	'''A positional parameter.
	'''

	def __init__(self, param_decls, **attrs):
		Parameter.__init__(self, param_decls, **attrs)

	def _parse_name(self, decls):
		if not len(decls) == 1:
			raise TypeError('Arguments take exactly one parameter declaration, got {}'.format(len(decls)))
		return decls[0]

	def consume(self, tokens):
		self._satisfied = True
		n = len(tokens) if self._nargs == -1 else self._nargs
		ret = tokens[:n]
		return tokens[n:], ret if n > 1 else ret[0]


class Option(Parameter):
	'''Describes (usually) optional parameters.

	An option may come in either a short or long form:
	  - The long form begins with a double dash and is dash-delimited,
	    e.g. --some-option
	  - The short form begins with a single dash is one letter long,
	    e.g. -s

	Short-form options may be globbed, e.g. -e -l -f --> -elf.
	'''

	def __init__(self, param_decls, **attrs):
		Parameter.__init__(self, param_decls, **attrs)

	def _parse_name(self, decls):
		longest = sorted(list(decls), key=lambda x: len(x))[-1]
		return longest[2:].replace('-', '_').lower() if len(longest) > 2 else longest[1:]

	def consume(self, tokens):
		self._satisfied = True
		n = len(tokens) if self._nargs == -1 else self._nargs
		ret = tokens[:n]
		return tokens[n:], ret if n > 1 else ret[0]


class Flag(Option):
	'''A special kind of option that consumes zero tokens.
	A flag stores a boolean that is True only if it's specified.
	'''

	def __init__(self, param_decls, **attrs):
		attrs['default'] = False
		Option.__init__(self, param_decls, **attrs)

	def consume(self, tokens):
		self._satisfied = True
		return tokens, True


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

	def __init__(self, name, callback, params):
		self._name = name
		self._callback = callback
		self._params = params

		self._subcommands = {}

	def subcommand(self, name=None, **attrs):
		def decorator(f):
			cmd = command(name, **attrs)(f)
			self._subcommands[cmd._name] = cmd
			return cmd
		return decorator

	def invoke(self, parsed):
		direct_args = {k: v for k, v in parsed.iteritems() if k not in self._subcommands}
		if self._callback is not None:
			self._callback(**direct_args)
		# Invoke subcommands (realistically only one should be invoked)
		for k, v in parsed.iteritems():
			if k in self._subcommands:
				self._subcommands[k].invoke(v)

	def parse(self, tokens):
		parsed = {}

		# Pass 1: Forward - fill out based on input string
		while tokens:
			token = tokens.pop(0)
			# 1. Is it a subcommand? Pass off to subcommand.
			if token in self._subcommands:
				parsed[token] = self._subcommands[token].parse(tokens)
				break  # The subcommand handles the remaining tokens
			# 2. Check if it's an option, and if so let it consume tokens.
			elif token.startswith('-'):
				for param in self._params:
					if token in param._decls:
						tokens, parsed[param._name] = param.consume(tokens)
						break
			# 3. Try to satisfy positional parameters (arguments).
			else:
				for param in self._params:
					if isinstance(param, Argument) and not param._satisfied:
						tokens, parsed[param._name] = param.consume([token] + tokens)
						break
			# 4. Error out.
				else:
					# @TODO better error message
					raise AttributeError('Weird token encountered: {}'.format(token))

		# Pass 2: Backward - fill out un-called parameters
		parsed.update({param._name: param._default for param in self._params if not param._satisfied})

		return parsed


class App(object):

	def __init__(self, *args, **kwargs):
		self._main = None

	def main(self, name=None, **attrs):
		def decorator(f):
			if self._main is not None:
				raise AttributeError('A main function has already been assigned')
			cmd = command(name, **attrs)(f)
			self._main = cmd
			return cmd
		return decorator


	def parse(self, tokens):
		'''Parses a list of tokens into a JSON-serializable object.

		The parsing proceeds from left to right and is greedy.

		Precedence order:
		  1. Parameters with active context. For example, an Option with
		     nargs='+' will gobble all the remaining tokens.
		  2. Subcommands.
		  3. Parameters.

		The keys of the returned object are the names of parameters or
		subcommands. Subcommands are encoded as nested objects. Multiple
		parameters are encoded as lists. All other values are encoded as
		parameter-specified data types, or strings if not specified.

		NOTE: no validation occurs at this step. During the handle() phase
		the JSON object will be applied and any errors raised.
		'''
		# Pre-parsing:
		#   1. Expand globbed options: -elf --> -e -l -f
		def is_globbed(s):
			return len(s) > 2 and s.startswith('-') and not s.startswith('--')
		expanded = [["-" + c for c in list(token[1:])] if is_globbed(token) else [token] for token in tokens]
		flattened = list(itertools.chain.from_iterable(expanded))

		# Parsing: pass off to main command
		return self._main.parse(flattened)

	def handle(self, parsed):
		'''Takes a parsed argument object and applies it to the CLI.
		'''
		#print(parsed)
		self._main.invoke(parsed)

	def run(self, tokens=None):
		if tokens is None:
			tokens = sys.argv[1:]

		parsed = self.parse(tokens)
		self.handle(parsed)
