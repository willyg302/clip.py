import unittest

import clip


class BaseTest(unittest.TestCase):
	'''Base class for tests in this file.

	This should:
	  - Hold generic test cases and expected values, bound to self
	  - Expose generic methods useful to other tests
	'''

	def setUp(self):
		pass

	def get_app(self):
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


class TestParse(BaseTest):

	def test_simple(self):
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
			self.assertEqual(self.get_app().parse(actual.split()), expected)


class TestInvoke(BaseTest):

	def test_invoke(self):
		self.get_app().run('-ab --file pie.txt chocolate b --long-thing yum yo'.split())
		self.assertEqual(self.a, [True, True, 'pie.txt', 'chocolate'])
		self.assertEqual(self.b, [False, True, ['yum', 'yo']])









'''
try:
	app.run()
except clip.ClipExit as e:
	print(e)
'''

'''
app2 = clip.App()

@app2.main()
@clip.arg('words', nargs=-1)
def echo(words):
	print(' '.join(words))

try:
	app2.run('hello world!'.split())
except clip.ClipExit:
	pass
'''


'''
Parser should generate: {
	'words': ['hello', 'world!']
}
'''


class Stream(object):
	def __init__(self):
		self._writes = []

	def write(self, message):
		self._writes.append(message)


class TestEmbedding(BaseTest):

	def test_streams(self):
		out = Stream()
		err = Stream()
		app = clip.App(stdout=out, stderr=err)

		@app.main()
		@clip.opt('--to-out')
		@clip.opt('--to-err')
		def a(to_out, to_err):
			clip.echo(to_out)
			clip.echo(to_err, err=True)

		app.run('--to-out out1 --to-err err1'.split())
		self.assertEqual(out._writes, ['out1'])
		self.assertEqual(err._writes, ['err1'])


# Embedded example
'''

import sys
import clip
import c

class StdStream(object):
    def __init__(self, stream=None):
        self._stream = sys.stdout if stream is None else stream

    def write(self, message):
        self._stream.write(message)

stdout = StdStream()
stderr = StdStream(sys.stderr)

app = clip.App(stdout=stdout, stderr=stderr, module=c)
app.arg('--version', help='Print the version', action='version',
        version=c.__version__ if '__version__' in dir(c) else 'No version specified')

c._run.func_globals['cli'] = app
try:
    c._run(sys.argv[1:])
except clip.ClipExit as e:
    print 'Exit status: {}'.format(e.status)


'''



if __name__ == '__main__':
	unittest.main()
