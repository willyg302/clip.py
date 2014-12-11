import clip

app = clip.App()

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

if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
