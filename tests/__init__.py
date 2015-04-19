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
		# Flush apps from previous tests, or they get written to again
		clip.clip_globals._streams = {}

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
			if to_out is not None:
				clip.echo(to_out)
			if to_err is not None:
				clip.echo(to_err, err=True)

		return app, out, err


class TestGlobals(BaseTest):

	def test_clip_globals(self):
		out, err = Stream(), Stream()
		cg = clip.ClipGlobals()
		cg.add_streams(out, err)
		cg.echo('My my')
		cg.echo('What have I done?', err=True)
		for i in range(10):
			cg.echo('.', nl=False)
		self.assertEqual(out._writes, ['My my\n'] + ['.'] * 10)
		self.assertEqual(err._writes, ['What have I done?\n'])

	def test_exit(self):
		self.embed()
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
		self.embed()
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

	def test_prompt(self):
		# Standard with confirm
		with mock_clip_input(['7', '7']):
			self.assertEqual(clip.prompt('?', type=int, confirm=True), 7)
		# Bad input
		_, out, _ = self.embed()
		with mock_clip_input(['', 'hehehe', '42']):
			self.assertEqual(clip.prompt('?', type=int), 42)
		self.assertEqual(len(out._writes), 2)
		# Interrupt
		def cause_interrupt():
			raise KeyboardInterrupt
		with mock_clip_input(['']):
			with self.assertRaises(clip.ClipExit):
				clip.prompt('?', default=cause_interrupt)
		# Skip
		with mock_clip_input(['', '']):
			self.assertIsNone(clip.prompt('?', skip=True))
			self.assertIsNone(clip.prompt('?', confirm=True, skip=True))


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
		app, out, err = self.make_embedded_app()
		app.run(['--to-out', 'list']).run('--to-out string').run('--to-err "two words"')
		self.assertEqual(out._writes, ['list\n', 'string\n'])
		self.assertEqual(err._writes, ['two words\n'])

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

	def test_call_command(self):
		app, out, _ = self.embed()

		@app.main()
		@clip.arg('number', type=int)
		def f(number):
			clip.echo('Hey there {}'.format(number))
			return 42 * number

		self.assertEqual(f(5), 210)
		self.assertEqual(out._writes[0], 'Hey there 5\n')

	def test_default_is_function(self):
		app, out, _ = self.embed()

		def fn():
			clip.echo('No name provided')

		@app.main()
		@clip.opt('--name', default=fn)
		def f(name):
			if name:
				clip.echo('Hello {}!'.format(name))

		app.run('').run('--name Dave')
		self.assertEqual(out._writes, ['No name provided\n', 'Hello Dave!\n'])


class TestCommand(BaseTest):

	def test_default(self):
		app, out, _ = self.embed()

		@app.main(default='x')
		def f():
			pass

		@f.subcommand()
		def x():
			clip.echo('x invoked!')

		app.run('x').run('')
		self.assertEqual(out._writes, ['x invoked!\n', 'x invoked!\n'])


class TestHelp(BaseTest):

	def test_basic_help(self):
		app, out, _ = self.embed()

		@app.main()
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
''')

	def test_full_help(self):
		app, out, _ = self.embed()

		@app.main(description='Description', epilogue='So long and thanks for all the fish!')
		@clip.arg('yo')
		@clip.opt('-s', '--something', type=int, nargs=3, default=[1, 2, 3], help='Does stuff')
		@clip.flag('-n', '--nothing')
		def f(yo, something, nothing):
			pass

		@f.subcommand(description='Oh lookee! A subcommand!')
		def x():
			pass

		try:
			app.run('-h')
		except clip.ClipExit:
			pass
		self.assertEqual(out._writes[0], '''f: Description

Usage: f {{arguments}} {{options}} {{subcommand}}

Arguments:
  yo [text]  

Options:
  -h, --help                Show this help message and exit
  -s, --something [int...]  Does stuff (default: [1, 2, 3])
  -n, --nothing             

Subcommands:
  x  Oh lookee! A subcommand!

So long and thanks for all the fish!
''')


class TestInheritance(BaseTest):

	def test_inheritance(self):
		app, out, err = self.embed()

		@app.main()
		@clip.flag('--flag')
		def f(flag):
			clip.echo(flag)

		@f.subcommand()
		def x():
			pass

		@x.subcommand(inherits=['flag'])
		def y(flag):
			clip.echo(flag, err=True)

		app.run('--flag x y')
		self.assertEqual(out._writes, ['True\n'])
		self.assertEqual(err._writes, ['True\n'])

	def test_inherits_args(self):
		app, out, _ = self.embed()

		@app.main()
		@clip.flag('-b', '--boop', inherit_only=True)
		def f():
			pass

		@f.subcommand(inherits=['boop'])
		def by_name(boop):
			clip.echo("name " + str(boop))

		@f.subcommand(inherits=['-b'])
		def by_short(boop):
			clip.echo("short " + str(boop))

		@f.subcommand(inherits=['--boop'])
		def by_long(boop):
			clip.echo("long " + str(boop))

		app.run('-b by_name').run('-b by_short').run('-b by_long')
		self.assertEqual(out._writes, ['name True\n', 'short True\n', 'long True\n'])

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

	def test_embedded_prompt(self):
		self.cache = None
		def custom_input(prompt):
			self.cache = prompt
			return 37
		self.assertEqual(clip.prompt('?', default=42, input_function=custom_input), 37)
		self.assertEqual(self.cache, '? [42]: ')


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

		# Giving tree_view something other than a flag
		with self.assertRaises(TypeError):
			app = clip.App()

			@app.main(tree_view='arg')
			@clip.arg('arg', help='whoops')
			def f(arg):
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
