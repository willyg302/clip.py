# Getting Started

Learning clip is best done by example, so this guide will walk you through making the Swedish Chef program in the README. Here it is again, in case you've forgotten:

```python
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
```

## The Walkthrough

<!-- @TODO -->

## Single-command Programs?

"But wait!" you say. "Subcommands are cool and all, but I just want to make a *really* simple program. Can clip do that, too?"

Why yes. Yes it can.

In fact, clip makes it *really* easy to make a really simple program: just don't attach any subcommands to the main command. For example, here's the famous echo program in clip:

```python
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
```

And the functionality:

```
$ python echo.py Hello world!
Hello world!
$ python echo.py idk     what i doinggggg      hahahaa a
idk what i doinggggg hahahaa a
```
