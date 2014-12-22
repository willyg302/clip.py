import clip
from functools import reduce

app = clip.App()

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

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
