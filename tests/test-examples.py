import clip

from . import BaseTest, Stream


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
		# default
		app, out, _ = self.embed()

		@app.main(default='x --num 19')
		def f():
			pass

		@f.subcommand(default='-h')
		@clip.opt('--num', type=int, required=True)
		def x(num):
			clip.echo('I was invoked with the number {}!'.format(num))

		for e in ['x --num 5', 'x', '']:
			try:
				app.run(e)
			except clip.ClipExit:
				pass
		self.assertEqual(out._writes, [
			'I was invoked with the number 5!\n',
			'''f x

Usage: x {{options}}

Options:
  -h, --help   Show this help message and exit
  --num [int]  
''',
			'I was invoked with the number 19!\n'
		])

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

		# tree_view
		app, out, _ = self.embed()

		@app.main(tree_view='-t')
		@clip.flag('-t', '--tree', hidden=True)
		def w():
			pass

		@w.subcommand()
		def x():
			pass

		@x.subcommand()
		def y():
			pass

		@y.subcommand()
		def z():
			pass

		try:
			app.run('--tree')
		except clip.ClipExit:
			pass
		self.assertEqual(out._writes, ['w\n', '  x\n', '    y\n', '      z\n'])

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

	def test_embedding(self):
		# Multiple apps (slightly modified for testing)
		out1 = Stream()
		out2 = Stream()
		app1 = clip.App(stdout=out1, name='app1')
		app2 = clip.App(stdout=out2, name='app2')
		clip.echo('App 1 via name', app='app1')
		clip.echo('App 2 via name', app='app2')
		app1.echo('App 1 directly')
		app2.echo('App 2 directly')
		clip.echo('Broadcast!')
		self.assertEqual(out1._writes, [
			'App 1 via name\n',
			'App 1 directly\n',
			'Broadcast!\n'
		])
		self.assertEqual(out2._writes, [
			'App 2 via name\n',
			'App 2 directly\n',
			'Broadcast!\n'
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
