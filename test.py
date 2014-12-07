import unittest

import clip


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
		try:
			clip.exit(1)
		except clip.ClipExit as e:
			self.assertEqual(e._status, 1)


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


class TestInvoke(BaseTest):

	def test_invoke(self):
		self.make_kitchen_sink_app().run('-ab --file pie.txt chocolate b --long-thing yum yo'.split())
		self.assertEqual(self.a, [True, True, 'pie.txt', 'chocolate'])
		self.assertEqual(self.b, [False, True, ['yum', 'yo']])

	def test_reset(self):
		app = self.make_kitchen_sink_app()
		app.run('b a n a n a'.split())
		self.assertEqual(self.b[2], 'a n a n a'.split())
		app.run('b o o p'.split())
		self.assertEqual(self.b[2], 'o o p'.split())

	def test_version(self):
		app, out, _ = self.embed()

		def print_version(value):
			clip.echo('Version 0.0.0')
			clip.exit()

		@app.main()
		@clip.flag('--version', callback=print_version, hidden=True)
		def f():
			clip.echo('Should not be called')

		try:
			app.run('--version'.split())
		except clip.ClipExit:
			pass

		self.assertEqual(out._writes, ['Version 0.0.0\n'])


class TestHelp(BaseTest):

	def test_help(self):
		pass
		# @TODO
		#self.make_kitchen_sink_app().run('b -h'.split())


class TestEmbedding(BaseTest):

	def test_streams(self):
		app, out, err = self.make_embedded_app()
		app.run('--to-out out1 --to-err err1'.split())
		self.assertEqual(out._writes, ['out1\n'])
		self.assertEqual(err._writes, ['err1\n'])

	def test_exit_message(self):
		# Exiting should print a message to err
		_, _, err = self.make_embedded_app()
		try:
			clip.exit(message='Exiting!')
		except clip.ClipExit:
			pass
		self.assertEqual(err._writes, ['Exiting!\n'])


if __name__ == '__main__':
	unittest.main()
