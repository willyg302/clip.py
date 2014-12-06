import unittest

import clip


class TestParse(unittest.TestCase):

	def setUp(self):
		self.app = clip.App()

		@self.app.main()
		@clip.flag('-e', '--earth')
		@clip.flag('--love', '-l')
		@clip.opt('--file')
		@clip.arg('args')
		def a(earth, love, file, args):
			print('In a', earth, love, file, args)

		@a.subcommand()
		@clip.flag('-t')
		@clip.arg('args', nargs=-1)
		def b(t, args):
			print('In b', t, args)

	def test_simple(self):
		self.assertEqual(self.app.parse('-el --file too okay b -t yum yo'.split()), {
			'earth': True,
			'love': True,
			'file': 'too',
			'args': 'okay',
			'b': {
				't': True,
				'args': ['yum', 'yo']
			}
		})


if __name__ == '__main__':
	unittest.main()






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
