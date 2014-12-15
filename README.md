![clip.py](https://raw.github.com/willyg302/clip.py/master/clip-logo.png "It looks like you're trying to make a CLI.")

-----

[![docs](https://readthedocs.org/projects/clippy/badge/?style=flat-square)](http://clippy.readthedocs.org/)
[![license](http://img.shields.io/badge/license-MIT-red.svg?style=flat-square)](https://raw.githubusercontent.com/willyg302/clip.py/master/LICENSE)

Embeddable, composable **c**ommand **l**ine **i**nterface **p**arsing

## Installing

clip is just a `pip install git+https://github.com/willyg302/clip.py.git@master` away.

## Basic Example

This example is just to whet your appetite. For a more in-depth guide to using clip, please see the [docs](http://clippy.readthedocs.org/). Also, much thanks to the [encheferizer](http://www.tuco.de/home/jschef.htm) for translations.

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

If you save the above code in a file called `chef.py`, you can then do the following:

```
$ python chef.py -h
chef: Hey, I em zee Svedeesh cheff!

Usage: chef {{options}} {{subcommand}}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  cook  Hefe-a zee cheff cuuk sume-a fuud
  bake  Tell zee cheff tu beke-a a pestry
$ python chef.py cook -h
chef cook: Hefe-a zee cheff cuuk sume-a fuud

Usage: cook {{arguments}} {{options}}

Arguments:
  food [text]  Neme-a ooff zee fuud

Options:
  -h, --help         Show this help message and exit
  -c, --count [int]  Hoo mooch fuud yuoo vunt (default: 1)
$ python chef.py cook burger
Zee cheff veell cuuk burger
$ python chef.py cook pie -c 5
Zee cheff veell cuuk pie pie pie pie pie
$ python chef.py bake --now
Error: Missing parameter "pastry".
$ python chef.py bake cake --now
Ookey ookey, I veell beke-a zee cake reeght evey!
```

## Testing

Call test with

    python setup.py test

Or

    nosetests

## Roadmap (v0.3.0)

v0.3.0 will be a [tock](http://en.wikipedia.org/wiki/Intel_Tick-Tock) release, focused on fixing any bugs introduced in the v0.2.0 rewrite and finishing any slated features.

- [ ] Finish `@TODO` items in code and tests

## Credits

- **[Aaargh](https://github.com/wbolster/aaargh)**: Some parsing logic
- **[Click](http://click.pocoo.org/3/)**: Decorator systems, parameter features
- **[docopt](http://docopt.org/)**: Help text formatting
