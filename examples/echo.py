import clip

app = clip.App()

@app.main()
@clip.arg('words', nargs=-1)
def echo(words):
	clip.echo(' '.join(words))

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
