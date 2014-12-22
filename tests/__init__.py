import unittest
import contextlib

import clip


@contextlib.contextmanager
def mock_clip_input(s):
	cache = clip.input
	def step(_):
		return s.pop(0)
	clip.input = step
	yield
	clip.input = cache


class Stream(object):
	def __init__(self):
		self._writes = []

	def write(self, message):
		self._writes.append(message)


class BaseTest(unittest.TestCase):
	'''Base class for tests in this file.

	This should:
	  - Hold generic test apps and expected values, bound to self
	  - Expose generic methods useful to other tests
	'''

	def setUp(self):
		pass

	def make_kitchen_sink_app(self):
		app = clip.App()
		self.a = []
		self.b = []

		@app.main()
		@clip.flag('-a', '--apple')
		@clip.flag('--banana', '-b')
		@clip.opt('--file', name='filename')
		@clip.arg('donut')
		def a(apple, banana, filename, donut):
			self.a = [apple, banana, filename, donut]

		@a.subcommand()
		@clip.flag('-t')
		@clip.flag('--long-thing')
		@clip.arg('args', nargs=-1)
		def b(t, long_thing, args):
			self.b = [t, long_thing, args]

		return app

	def embed(self):
		out, err = Stream(), Stream()
		app = clip.App(stdout=out, stderr=err)
		return app, out, err

	def make_embedded_app(self):
		app, out, err = self.embed()

		@app.main()
		@clip.opt('--to-out')
		@clip.opt('--to-err')
		def f(to_out, to_err):
			clip.echo(to_out)
			clip.echo(to_err, err=True)

		return app, out, err


class TestGlobals(BaseTest):

	def test_clip_globals(self):
		out, err = Stream(), Stream()
		cg = clip.ClipGlobals()
		cg.set_stdout(out)
		cg.set_stderr(err)
		cg.echo('My my')
		cg.echo('What have I done?', err=True)
		self.assertEqual(out._writes, ['My my\n'])
		self.assertEqual(err._writes, ['What have I done?\n'])

	def test_exit(self):
		# Standard case, custom message
		try:
			clip.exit('Woot!')
		except clip.ClipExit as e:
			self.assertEqual(e.message, 'Woot!')
		# Error condition
		try:
			clip.exit(err=True)
		except clip.ClipExit as e:
			self.assertTrue(e.message.startswith('clip exiting'))
			self.assertEqual(e.status, 1)

	def test_confirm(self):
		# All the standard accepted entries
		with mock_clip_input(['y', 'n', 'Y', 'N', 'yEs', 'No', 'YES', 'no']):
			for e in [True, False, True, False, True, False, True, False]:
				self.assertEqual(clip.confirm('?'), e)
		# Abort
		with mock_clip_input(['n']):
			with self.assertRaises(clip.ClipExit):
				clip.confirm('?', abort=True)
		# Mistaken entries
		_, out, _ = self.embed()
		with mock_clip_input(['', 'boop', 'PAHHHHHH', 'NO']):
			self.assertFalse(clip.confirm('?'))
		self.assertEqual(len(out._writes), 3)


class TestParse(BaseTest):

	def test_kitchen_sink(self):
		expected = {
			'apple': True,
			'banana': True,
			'filename': 'pie.txt',
			'donut': 'chocolate',
			'b': {
				't': False,
				'long_thing': True,
				'args': ['yum', 'yo']
			}
		}
		actuals = [
			'-ab --file pie.txt chocolate b --long-thing yum yo',
			'chocolate -a --file pie.txt --banana b --long-thing yum yo'
		]
		for actual in actuals:
			self.assertEqual(self.make_kitchen_sink_app().parse(actual.split()), expected)

	def test_required(self):
		app, _, err = self.embed()

		@app.main()
		@clip.opt('-o')
		@clip.flag('-r', required=True)
		def f(o, r):
			pass

		with self.assertRaises(clip.ClipExit):
			app.run('-o joe')
		self.assertTrue('Missing' in err._writes[0])

	def test_common_errors(self):
		app, _, err = self.embed()

		@app.main()
		def f():
			pass

		@f.subcommand()
		@clip.opt('--tokens', nargs=4)
		def nargs(tokens):
			pass

		@f.subcommand()
		@clip.opt('--int', type=int)
		@clip.arg('ints', type=int, nargs=3)
		def coerce(int, ints):
			pass

		for e in ['nargs --tokens 1 2 3', 'coerce --int pie', 'coerce this aint right']:
			with self.assertRaises(clip.ClipExit):
				app.run(e)
		for i, e in enumerate(['Not enough', 'Invalid type', 'Invalid type']):
			self.assertTrue(e in err._writes[i])


	# @TODO:
	#   - Test type (should be part of kitchen sink)
	#   - Test required/nargs (should be part of kitchen sink)
	#   - Test default. This includes a case where default is a function!

	# Add tests for calling a Command-wrapped function as if it were a function.
	# This includes functions that return something, validate that they do so correctly.


class TestInvoke(BaseTest):

	def test_invoke(self):
		self.make_kitchen_sink_app().run('-ab --file pie.txt chocolate b --long-thing yum yo')
		self.assertEqual(self.a, [True, True, 'pie.txt', 'chocolate'])
		self.assertEqual(self.b, [False, True, ['yum', 'yo']])

	def test_reset(self):
		app = self.make_kitchen_sink_app()
		app.run('b a n a n a')
		self.assertEqual(self.b[2], 'a n a n a'.split())
		# If reset works, we should be able to run another command right away
		app.run('b o o p')
		self.assertEqual(self.b[2], 'o o p'.split())

	def test_run(self):
		app, out, _ = self.make_embedded_app()
		app.run(['--to-out', 'list']).run('--to-out string')
		self.assertEqual(out._writes, ['list\n', 'string\n'])

	def test_version(self):
		app, out, _ = self.embed()

		def print_version(value):
			clip.exit('Version 0.0.0')

		@app.main()
		@clip.flag('--version', callback=print_version, hidden=True)
		def f():
			clip.echo('Should not be called')

		with self.assertRaises(clip.ClipExit):
			app.run('--version')
		self.assertEqual(out._writes, ['Version 0.0.0\n'])


class TestHelp(BaseTest):

	def test_help(self):
		pass
		# @TODO
		#self.make_kitchen_sink_app().run('b -h')


class TestInheritance(BaseTest):

	def test_inheritance(self):
		pass
		# @TODO:
		#   - All inheritance cases
		#   - Inheritance of a param two levels up (nested subcommand)
		#   - Inheritance can be specified using decls, name, etc.

	def test_inherits_args(self):
		pass

	def test_inherit_only(self):
		app, out, err = self.embed()

		@app.main()
		@clip.flag('-s', inherit_only=True)
		@clip.flag('-t')
		def f(t):
			clip.echo(t)

		@f.subcommand(inherits=['-s', '-t'])
		def sub(s, t):
			clip.echo(s, err=True)
			clip.echo(t, err=True)

		parsed = app.parse(['-st', 'sub'])
		self.assertEqual(parsed, {
			't': True,
			'sub': {
				's': True,
				't': True
			}
		})
		app.invoke(parsed)
		self.assertEqual(out._writes, ['True\n'])
		self.assertEqual(err._writes, ['True\n', 'True\n'])


class TestEmbedding(BaseTest):

	def test_streams(self):
		app, out, err = self.make_embedded_app()
		app.run('--to-out out1 --to-err err1')
		self.assertEqual(out._writes, ['out1\n'])
		self.assertEqual(err._writes, ['err1\n'])

	def test_exit_message(self):
		# Exiting should print a message
		_, out, _ = self.make_embedded_app()
		with self.assertRaises(clip.ClipExit):
			clip.exit('Exiting!')
		self.assertEqual(out._writes, ['Exiting!\n'])

	def test_embedded_confirm(self):
		self.cache = None
		def custom_input(prompt):
			self.cache = prompt
			return 'y'
		self.assertTrue(clip.confirm('?', default='no', input_function=custom_input))
		self.assertEqual(self.cache, '? [y/N]: ')


class TestMistakes(BaseTest):
	'''These are mistakes a programmer would make using clip.
	'''

	def test_app_mistakes(self):
		# App should not define more than one main command
		app = self.make_kitchen_sink_app()
		with self.assertRaises(AttributeError):

			@app.main()
			def f():
				pass

		# App should define at least one main command
		with self.assertRaises(AttributeError):
			clip.App().run('something')

	def test_command_mistakes(self):
		# Giving a command a callback that is already a command
		with self.assertRaises(TypeError):
			app = clip.App()

			@app.main()
			def f():
				pass

			@f.subcommand()
			@f.subcommand()
			def sub():
				pass

		# Giving main an "inherits"
		with self.assertRaises(AttributeError):
			app = clip.App()

			@app.main(inherits=['whoops'])
			def f(whoops):
				pass

		# Inheriting a parameter that doesn't exist
		with self.assertRaises(AttributeError):
			app = clip.App()

			@app.main()
			def f():
				pass

			@f.subcommand(inherits=['whoops'])
			def sub(whoops):
				pass

	def test_parameter_mistakes(self):
		# If nargs != 1 and default is not a list
		with self.assertRaises(TypeError):
			app = clip.App()

			@app.main()
			@clip.opt('-a', nargs=-1, default='whoops')
			def f(a):
				pass

	def test_argument_mistakes(self):
		# Specifying more than one name for an argument
		with self.assertRaises(TypeError):
			app = clip.App()

			@app.main()
			@clip.arg('name', 'whoops')
			def f(name):
				pass


class TestExamples(BaseTest):
	'''Test documentation examples to protect against regressions.

	If any of these tests fail, then the associated docs need to be updated.
	Similarly, if any of the examples are updated they should be reflected
	in the tests here.
	'''

	def test_readme(self):
		# Shopping list example in README and Getting Started section
		app, out, err = self.embed()

		@app.main(description='A very unhelpful shopping list CLI program')
		def shopping():
			pass

		@shopping.subcommand(description='Add an item to the list')
		@clip.arg('item', required=True)
		@clip.opt('-q', '--quantity', default=1, help='How many of the item to get')
		def add(item, quantity):
			clip.echo('Added "{} - {}" to the list'.format(item, quantity))

		@shopping.subcommand(description='See all items on the list')
		@clip.flag('--sorted', help='View items in alphabetical order')
		def view(sorted):
			clip.echo('This is your {}sorted list'.format('' if sorted else 'un'))

		inputs = [
			'-h',
			'add -h',
			'add',
			'add cookies -q 10',
			'view',
			'view --sorted'
		]
		for e in inputs:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, [
			'''shopping: A very unhelpful shopping list CLI program

Usage: shopping {{options}} {{subcommand}}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  add   Add an item to the list
  view  See all items on the list
''',
			'''shopping add: Add an item to the list

Usage: add {{arguments}} {{options}}

Arguments:
  item [text]  

Options:
  -h, --help            Show this help message and exit
  -q, --quantity [int]  How many of the item to get (default: 1)
''',
			'Added "cookies - 10" to the list\n',
			'This is your unsorted list\n',
			'This is your sorted list\n'
		])
		self.assertEqual(err._writes, [
			'Error: Missing parameter "item".\n'
		])

	def test_getting_started(self):
		# Echo example
		app, out, _ = self.embed()

		@app.main()
		@clip.arg('words', nargs=-1)
		def echo(words):
			clip.echo(' '.join(words))

		app.run('Hello world!').run('idk     what i doinggggg      hahahaa a')
		self.assertEqual(out._writes, ['Hello world!\n', 'idk what i doinggggg hahahaa a\n'])

	def test_commands(self):
		# description
		app, out, _ = self.embed()

		@app.main(description='This thing does awesome stuff!')
		def f():
			pass

		@f.subcommand(description='This is a sweet subcommand!')
		def sub():
			pass

		for e in ['-h', 'sub -h']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, [
			'''f: This thing does awesome stuff!

Usage: f {{options}} {{subcommand}}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  sub  This is a sweet subcommand!
''',
			'''f sub: This is a sweet subcommand!

Usage: sub {{options}}

Options:
  -h, --help  Show this help message and exit
'''
		])

		# epilogue
		app, out, _ = self.embed()

		@app.main(epilogue='So long and thanks for all the fish!')
		def f():
			pass

		try:
			app.run('-h')
		except clip.ClipExit:
			pass
		self.assertEqual(out._writes[0], '''f

Usage: f {{options}}

Options:
  -h, --help  Show this help message and exit

So long and thanks for all the fish!
''')

	def test_parameters(self):
		# nargs
		app, out, err = self.embed()

		@app.main()
		@clip.arg('stuff', nargs=3)
		def f(stuff):
			clip.echo('You entered: {}'.format(stuff))

		for e in ['a', 'a b', 'a b c']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, ["You entered: ['a', 'b', 'c']\n"])
		self.assertEqual(err._writes, ['Error: Not enough arguments for "stuff".\n'] * 2)

		# default
		app, out, _ = self.embed()

		@app.main()
		@clip.opt('--name', default='Joe')
		def f(name):
			clip.echo('Hello {}!'.format(name))

		app.run('').run('--name Dave')
		self.assertEqual(out._writes, ['Hello Joe!\n', 'Hello Dave!\n'])

		# type
		app, out, err = self.embed()

		@app.main()
		@clip.arg('numbers', nargs=-1, default=[1, 2, 3])
		def f(numbers):
			clip.echo(sum(numbers))

		for e in ['2 4 6 8 10', 'wuuutttt']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, ['30\n'])
		self.assertEqual(err._writes, ['Error: Invalid type given to "numbers", expected int.\n'])

		# required
		app, out, err = self.embed()

		@app.main()
		@clip.flag('--needed', required=True)
		def f(needed):
			clip.echo('Ahh, I needed that.')

		for e in ['', '--needed']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, ['Ahh, I needed that.\n'])
		self.assertEqual(err._writes, ['Error: Missing parameter "needed".\n'])

		# callback
		app, out, _ = self.embed()

		def shout(value):
			clip.echo(' '.join(value).upper())

		@app.main()
		@clip.arg('words', nargs=-1, callback=shout)
		def f(words):
			pass

		app.run('i feel da powah!')
		self.assertEqual(out._writes[0], 'I FEEL DA POWAH!\n')

		# help
		app, out, _ = self.embed()

		@app.main()
		@clip.flag('--panic', help='Don\'t do this')
		def f(panic):
			pass

		try:
			app.run('-h')
		except clip.ClipExit:
			pass
		self.assertEqual(out._writes[0], '''f

Usage: f {{options}}

Options:
  -h, --help  Show this help message and exit
  --panic     Don't do this
''')

	def test_inheriting_parameters(self):
		# Calculator (here we only test the final version for expected output)
		from functools import reduce

		app, out, _ = self.embed()

		@app.main()
		@clip.arg('numbers', nargs=-1, type=int, inherit_only=True)
		@clip.flag('-s', '--silent', inherit_only=True)
		def calculator():
			pass

		@calculator.subcommand(inherits=['numbers', '-s'])
		def add(numbers, silent):
			if not silent:
				clip.echo('Add these numbers? Okay, here we gooooo!')
			clip.echo(sum(numbers))

		@calculator.subcommand(inherits=['numbers', '--silent'])
		def multiply(numbers, silent):
			if not silent:
				clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
			clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)

		for e in ['add 1 3 5 7', 'multiply 1 3 5 7', 'add -s 1 3 5 7', '-s add 1 3 5 7']:
			app.run(e)
		self.assertEqual(out._writes, [
			'Add these numbers? Okay, here we gooooo!\n', '16\n',
			'Wa-hoo, let\'s-a multiply these numbers!\n', '105\n',
			'16\n',
			'16\n'
		])

		# Going deeper
		app, out, _ = self.embed()

		@app.main()
		@clip.flag('-a')
		def w(a):
			clip.echo('a in w: {}'.format(a))

		@w.subcommand()
		@clip.flag('-b')
		def x(b):
			clip.echo('b in x: {}'.format(b))

		@x.subcommand(inherits=['a'])
		@clip.flag('-c')
		def y(a, c):
			clip.echo('a in y: {}'.format(a))
			clip.echo('c in y: {}'.format(c))

		@y.subcommand(inherits=['a', 'b', 'c'])
		@clip.flag('-d')
		def z(a, b, c, d):
			clip.echo('All together now: {}'.format((a, b, c, d)))

		app.run('-a x -b y -c z -d')
		self.assertEqual(out._writes, [
			'a in w: True\n',
			'b in x: True\n',
			'a in y: True\n',
			'c in y: True\n',
			'All together now: (True, True, True, True)\n'
		])

	def test_extending_clip(self):
		# The sorting program
		class Choice(clip.Option):
			'''A special option that must be chosen from a list of valid values.

			The default value will be the first item of the list.
			'''

			def __init__(self, param_decls, **attrs):
				try:
					self._choices = attrs.pop('choices')
				except KeyError:
					raise AttributeError('You must specify the choices to select from')
				if not isinstance(self._choices, list) or len(self._choices) == 0:
					raise AttributeError('"choices" must be a nonempty list of valid values')
				attrs['nargs'] = 1
				attrs['default'] = self._choices[0]
				clip.Option.__init__(self, param_decls, **attrs)

			def consume(self, tokens):
				tokens.pop(0)  # Pop the choice from the tokens array
				selected = tokens.pop(0)
				if selected not in self._choices:
					clip.exit('Error: "{}" is not a valid choice (choose from {}).'.format(selected, ', '.join(self._choices)), True)
				clip.Parameter.post_consume(self, selected)
				return tokens

		def choice(*param_decls, **attrs):
			return clip._make_param(Choice, param_decls, **attrs)

		app, out, err = self.embed()

		@app.main()
		@choice('-t', '--type', name='sort_type', choices=['quicksort', 'bubblesort', 'mergesort'])
		def sort(sort_type):
			clip.echo('You selected {}'.format(sort_type))

		for e in ['', '-t spaghettisort', '-t mergesort']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, ['You selected quicksort\n', 'You selected mergesort\n'])
		self.assertEqual(err._writes, ['Error: "spaghettisort" is not a valid choice (choose from quicksort, bubblesort, mergesort).\n'])
