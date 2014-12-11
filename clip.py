'''
clip.py: Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing

Copyright: (c) 2014 William Gaul
License: MIT, see LICENSE for more details
'''
import sys
import itertools


########################################
# COMPATIBILITY
########################################

PY2 = sys.version_info[0] == 2

input = raw_input if PY2 else input


''' @TODO:

- A prompt function:
  - text: To show for prompt
  - default: Default if no input given, if None then prompt will repeat until aborted (None)
  - invisible: For password prompts (False)
  - confirm: Ask for confirmation (False)
  - type: The type to coerce input to (None)
  - show_default: Whether to display the default value to users (True)


GLOBAL OPTIONS INHERITANCE SYSTEM

@app.main()
@clip.flag('-s')
def a(s):
	pass

@a.subcommand()
def b():
	pass

Valid: a -s b
Invalid: a b -s

But then:

@a.subcommand()
@a.inherit(['-s'])
def b(s):
	pass

And now `a b -s` is valid. Furthermore:

@app.main()
@clip.flag('-s', global=False)
def a(s):
	pass

And now `a -s b` is invalid.

A subcommand can inherit an option from any level above it.



PRINT USAGE TO THE USER WHEN THEY ENTER SOMETHING WEIRD.
This means that usage should be a separate method?
'''


########################################
# GLOBAL CLASSES/METHODS
########################################

class ClipGlobals(object):

	def __init__(self):
		self._stdout = None
		self._stderr = None

	def echo(self, message, err=False):
		stream = self._stderr if err else self._stdout
		if stream is None:
			raise TypeError('clip {} stream has not been initialized'.format('err' if err else 'out'))
		stream.write(str(message) + "\n")

	def set_stdout(self, stream):
		self._stdout = stream

	def set_stderr(self, stream):
		self._stderr = stream


class ClipExit(Exception):
	def __init__(self, message=None, status=0):
		self._message = message or 'clip exiting with status {}'.format(status)
		self._status = status
	def __str__(self):
		return repr(self._message)


clip_globals = ClipGlobals()

def echo(message, err=False):
	clip_globals.echo(message, err)

def exit(message=None, err=False):
	if message:
		echo(message, err)
	raise ClipExit(message, 1 if err else 0)

def confirm(prompt, default=None, show_default=True, abort=False, input_function=None):
	'''Prompts for confirmation from the user.

	Arguments:
	  - prompt: The prompt to show to the user.
	  - default: Default value for the prompt, one of 'yes'/'no'/None.
	  - show_default: Whether to display the prompt defaults, e.g. [y/n]
	  - abort: If True and the user enters 'no' this will raise a ClipExit.
	'''
	valid = {
		'yes': True,
		'y': True,
		'no': False,
		'n': False
	}
	if input_function is None:
		input_function = input
	if default not in ['yes', 'no', None]:
		default = None
	if show_default:
		prompt = '{} [{}/{}]: '.format(prompt, 'Y' if default == 'yes' else 'y', 'N' if default == 'no' else 'n')
	while True:
		choice = input_function(prompt).lower() or default
		if choice in valid:
			if valid[choice] == False and abort:
				exit('Operation aborted by user', True)
			return valid[choice]
		else:
			echo('Please respond with "yes" or "no" (or "y" or "n").')


########################################
# PARAMETER METHODS
########################################

def _convert_type(t, default=None):
	return t or (type(default) if default is not None else None)

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

	Attributes:
	  - name: The name of this parameter. If not specified, a name will be
	    inferred based on the parameter declarations.
	  - nargs: The number of args this parameter consumes, -1 for infinite.
	  - default: The value for this parameter if none is given.
	  - type: A type to coerce the parameter's value into. If no type is
	    provided, the type of the default value is used. If no default value
	    is provided, the type remains a string.
	  - required: If true, the parameter must be specified in the input.
	  - callback: A function to invoke once this parameter has been matched
	    in the input. It takes a single argument, the value of the parameter.
	  - hidden: If True, this parameter will not be passed to the owning
	    command's function. This is useful for help/version flags.
	  - help: Help text for this parameter.
	'''

	def __init__(self, param_decls, name=None, nargs=1, default=None,
		         type=None, required=False, callback=None, hidden=False,
		         help=None):
		self._decls = param_decls
		self._name = name or self.parse_name(param_decls)
		self._nargs = nargs
		self._default = default
		self._type = _convert_type(type, default)
		self._required = required
		self._callback = callback
		self._hidden = hidden
		self._help = help

		self.reset()  # Do an initial reset to prime the parameter

	def reset(self):
		self._satisfied = False  # True when this parameter has consumed tokens

	def name(self):
		return self._name

	def required(self):
		return self._required

	def hidden(self):
		return self._hidden

	def satisfied(self):
		return self._satisfied

	def parse_name(self, decls):
		raise NotImplementedError('parse_name/1 must be implemented by child classes')

	def consume(self, tokens):
		'''Have this parameter consume some tokens.

		Returns the modified tokens array and the value associated with this
		parameter to store. For example, given:

		    ['-a', 'one', 'two']

		where -a is an option that consumes one token, this will return:

		    ['two'], 'one'

		That is, 'one' was consumed and is this parameter's value.
		'''
		n = len(tokens) if self._nargs == -1 else self._nargs
		# @TODO: Wrap ValueError when an invalid parameter type is given
		l = [self._type(e) if self._type is not None else e for e in tokens[:n]]
		consumed = l if n != 1 else l[0]
		self.post_consume(consumed)
		return tokens[n:], consumed

	def post_consume(self, consumed):
		self._satisfied = True
		# Parameter has been matched, so invoke the callback if any
		if self._callback is not None:
			self._callback(consumed)

	def get_default(self):
		# The provided default can be a function, whose return value will be used
		return self._default() if hasattr(self._default, '__call__') else self._default

	def matches(self, token):
		return not self.satisfied()


class Argument(Parameter):
	'''A positional parameter.
	'''

	def __init__(self, param_decls, **attrs):
		Parameter.__init__(self, param_decls, **attrs)

	def parse_name(self, decls):
		if not len(decls) == 1:
			raise TypeError('Arguments take exactly 1 parameter declaration, got {}'.format(len(decls)))
		return decls[0]

	def consume(self, tokens):
		return Parameter.consume(self, tokens)

	def matches(self, token):
		return Parameter.matches(self, token) and not token.startswith('-')


class Option(Parameter):
	'''A (usually) optional parameter.
	'''

	''' @TODO:

	- global: If false, this can only be used by subcommands (True)

	Should we do this?

	- prompt: True, or a non-empty string to prompt for user input if not set (False)
	- confirm: If prompt is also True, this asks for confirmation (False)
	- invisible: If prompt is also True, this hides input from the user (False)
	'''

	def __init__(self, param_decls, **attrs):
		Parameter.__init__(self, param_decls, **attrs)

	def parse_name(self, decls):
		# @TODO: Validate parameter declaration logic?
		longest = sorted(list(decls), key=lambda x: len(x))[-1]
		return longest[2:].replace('-', '_').lower() if len(longest) > 2 else longest[1:]

	def consume(self, tokens):
		tokens.pop(0)  # Pop the opt from the tokens array
		return Parameter.consume(self, tokens)

	def matches(self, token):
		return Parameter.matches(self, token) and token.startswith('-') and token in self._decls


class Flag(Option):
	'''A special option that consumes nothing and is True only if it appears.
	'''

	def __init__(self, param_decls, **attrs):
		attrs['nargs'] = 0
		attrs['default'] = False
		Option.__init__(self, param_decls, **attrs)

	def consume(self, tokens):
		tokens.pop(0)  # Pop the flag from the tokens array
		consumed = True
		Parameter.post_consume(self, consumed)
		return tokens, consumed


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

	def __init__(self, name, callback, params, description=None, epilogue=None):
		self._name = name
		self._callback = callback
		self._params = params
		self._description = description
		self._epilogue = epilogue

		self._subcommands = {}
		# Add help to every command
		self._params.insert(0, Flag(('-h', '--help'), callback=self.help, hidden=True, help='Show this help message and exit'))

	def subcommand(self, name=None, **attrs):
		def decorator(f):
			cmd = command(name, **attrs)(f)
			self._subcommands[cmd._name] = cmd
			return cmd
		return decorator

	def parse(self, tokens):
		# @TODO: Clean up
		parsed = {}

		# Pass 1: Forward - fill out based on input string
		while tokens:
			token = tokens[0]
			# 1. Is it a subcommand? Pass off to subcommand.
			if token in self._subcommands:
				tokens.pop(0)
				parsed[token] = self._subcommands[token].parse(tokens)
				break  # The subcommand handles the remaining tokens
			# 2. Try to find a parameter that will consume it.
			else:
				for param in self._params:
					if param.matches(token):
						tokens, consumed = param.consume(tokens)
						if not param.hidden():
							parsed[param.name()] = consumed
						break
			# 3. Error out.
				else:
					# @TODO better error message
					exit('Error: could not understand "{}".'.format(token), True)

		# Pass 2: Backward - fill out un-called parameters
		for param in self._params:
			if not param.satisfied() and not param.hidden():
				if param.required():
					exit('Missing parameter "{}".'.format(param.name()), True)
				parsed[param.name()] = param.get_default()

		return parsed

	def invoke(self, parsed):
		# First invoke this command's callback
		self._callback(**{k: v for k, v in parsed.iteritems() if k not in self._subcommands})
		# Invoke subcommands (realistically only one should be invoked)
		for k, v in parsed.iteritems():
			if k in self._subcommands:
				self._subcommands[k].invoke(v)

	def reset(self):
		# Reset all parameters associated with this command
		for param in self._params:
			param.reset()
		# Recurse into subcommands
		for v in self._subcommands.values():
			v.reset()

	def help(self, value):
		# @TODO: Clean up
		# Also, add all the other things like defaults, types, etc.
		help_parts = []

		# Header
		header = self._name
		if self._description is not None:
			header = '{}: {}'.format(header, self._description)
		help_parts.append(header)

		# Usage
		help_parts.append('Usage: {} {{arguments/options}} {{subcommand}}'.format(self._name))

		# Arguments
		args = [param for param in self._params if isinstance(param, Argument)]
		if args:
			args_width = max(len(arg._name) for arg in args) + 2
			arguments = ['  {}{}'.format(arg._name.ljust(args_width), arg._help or '') for arg in args]
			help_parts.append('\n'.join(['Arguments:'] + arguments))

		# Options
		opts = [param for param in self._params if isinstance(param, Option)]
		if opts:
			opts_width = max(len(', '.join(opt._decls)) for opt in opts) + 2
			options = ['  {}{}'.format(', '.join(opt._decls).ljust(opts_width), opt._help or '') for opt in opts]
			help_parts.append('\n'.join(['Options:'] + options))

		# Subcommands
		if self._subcommands:
			subs_width = max(len(k) for k, v in self._subcommands.iteritems()) + 2
			subcommands = ['  {}{}'.format(k.ljust(subs_width), v._description or '') for k, v in self._subcommands.iteritems()]
			help_parts.append('\n'.join(['Subcommands:'] + subcommands))

		# Epilogue
		if self._epilogue is not None:
			help_parts.append(self._epilogue)

		echo('\n\n'.join(help_parts))
		exit()


########################################
# APP CLASS
########################################

class App(object):

	def __init__(self, stdout=None, stderr=None):
		clip_globals.set_stdout(stdout or sys.stdout)
		clip_globals.set_stderr(stderr or sys.stderr)

		self._main = None

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
		self.invoke(self.parse(tokens))
		self.reset()  # Clean up so the app can be used again
