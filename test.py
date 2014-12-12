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



'''
HANDLING ERRORS:

$ test.py -h
Usage: test.py [OPTIONS] COMMAND [ARGS]...

Error: no such option: -h
$ test.py asdajnd
Usage: test.py [OPTIONS] COMMAND [ARGS]...

Error: No such command "asdajnd".
'''


class TestInheritance(BaseTest):

	def test_inheritance(self):
		pass
		# @TODO:
		#   - All inheritance cases
		#   - Inheritance of a param two levels up (nested subcommand)
		#   - Inheritance can be specified using decls, name, etc.




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
	'''

	def test_getting_started(self):
		# Chef example in README and Getting Started section
		app, out, err = self.embed()

		@app.main(description='Hey, I em zee Svedeesh cheff!')
		def chef():
			pass

		@chef.subcommand(description='Hefe-a zee cheff cuuk sume-a fuud')
		@clip.arg('food', required=True, help='Neme-a ooff zee fuud')
		@clip.opt('-c', '--count', default=1, help='Hoo mooch fuud yuoo vunt')
		def cook(food, count):
			clip.echo('Zee cheff veell cuuk {}'.format(' '.join([food] * count)))

		@chef.subcommand(description='Tell zee cheff tu beke-a a pestry')
		@clip.arg('pastry', required=True, help='Neme-a ooff zee pestry')
		@clip.flag('--now', help='Iff yuoo\'re-a in a hoorry')
		def bake(pastry, now):
			response = 'Ookey ookey, I veell beke-a zee {} reeght evey!' if now else 'Ooh, yuoo vunt a {}?'
			clip.echo(response.format(pastry))

		inputs = [
			'cook bork --count 5',
			'bake pie --now'
		]
		for e in inputs:
			app.run(e)
		self.assertEqual(out._writes, [
			'Zee cheff veell cuuk bork bork bork bork bork\n',
			'Ookey ookey, I veell beke-a zee pie reeght evey!\n'
		])

		# Echo example
		app, out, err = self.embed()

		@app.main()
		@clip.arg('words', nargs=-1)
		def echo(words):
			clip.echo(' '.join(words))

		app.run('Hello world!').run('')
		self.assertEqual(out._writes, ['Hello world!\n', '\n'])


if __name__ == '__main__':
	unittest.main()
