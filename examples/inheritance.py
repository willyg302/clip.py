import clip

app = clip.App()

@app.main()
@clip.flag('-s')
def inheritance(s):
	clip.echo('s from main: {}'.format(s))

@inheritance.subcommand(inherits=['-s'])
@clip.flag('-t')
def a(s, t):
	clip.echo('s from a: {}'.format(s))
	clip.echo('t from a: {}'.format(t))

@a.subcommand(inherits=['-s', '-t'])
def b(s, t):
	clip.echo('s from b: {}'.format(s))
	clip.echo('t from b: {}'.format(t))

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
