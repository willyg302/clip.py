import clip

app = clip.App()

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

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
