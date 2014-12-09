![clip.py](https://raw.github.com/willyg302/clip.py/master/clip-logo-922.png "It looks like you're trying to make a CLI.")

-----

[![license](http://img.shields.io/badge/license-MIT-red.svg?style=flat-square)](https://raw.githubusercontent.com/willyg302/clip.py/master/LICENSE)

Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing

## Installing

clip is just a `pip install git+https://github.com/willyg302/clip.py.git@master` away.

## Basic Example

This example is just to whet your appetite. For a more in-depth guide to using clip, please see the [docs](docs/main.md). Also, much thanks to the [encheferizer](http://www.tuco.de/home/jschef.htm) for translations.

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
	print('Zee cheff veell cuuk {}'.format(' '.join([food] * count)))

@chef.subcommand(description='Tell zee cheff tu beke-a a pestry')
@clip.arg('pastry', required=True, help='Neme-a ooff zee pestry')
@clip.flag('--now', help='Iff yuoo\'re-a in a hoorry')
def bake(pastry, now):
	response = 'Ookey ookey, I veell beke-a zee {} reeght evey!' if now else 'Ooh, yuoo vunt a {}?'
	print(response.format(pastry))

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

Usage: chef {arguments/options} {subcommand}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  cook  Hefe-a zee cheff cuuk sume-a fuud
  bake  Tell zee cheff tu beke-a a pestry
$ python chef.py cook -h
cook: Hefe-a zee cheff cuuk sume-a fuud

Usage: cook {arguments/options} {subcommand}

Arguments:
  food  Neme-a ooff zee fuud

Options:
  -h, --help   Show this help message and exit
  -c, --count  Hoo mooch fuud yuoo vunt
$ python chef.py cook burger
Zee cheff veell cuuk burger
$ python chef.py cook pie -c 5
Zee cheff veell cuuk pie pie pie pie pie
$ python chef.py bake --now
Missing parameter "pastry".
$ python chef.py bake cake --now
Ookey ookey, I veell beke-a zee cake reeght evey!
```

## Testing

Call `python test.py` while in the root directory of this repo.

## Roadmap (v0.2.0)

- [ ] Finish redesign
- [ ] Associated redesign tests
- [ ] Basic documentation
