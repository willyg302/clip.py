![clip.py](https://raw.github.com/willyg302/clip.py/master/clip-logo.png "It looks like you're trying to make a CLI.")

-----

[![Travis](https://img.shields.io/travis/willyg302/clip.py.svg?style=flat-square)](https://travis-ci.org/willyg302/clip.py)
[![docs](https://readthedocs.org/projects/clippy/badge/?style=flat-square)](http://clippy.readthedocs.org/)
[![license](http://img.shields.io/badge/license-MIT-red.svg?style=flat-square)](https://raw.githubusercontent.com/willyg302/clip.py/master/LICENSE)

Embeddable, composable **c**ommand **l**ine **i**nterface **p**arsing

## Installing

clip is just a `pip install git+https://github.com/willyg302/clip.py.git@master` away.

## Basic Example

This example is just to whet your appetite. For a more in-depth guide to using clip, please see the [docs](http://clippy.readthedocs.org/).

```python
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
```

If you save the above code in a file called `shopping.py`, you can then do the following:

```
$ python shopping.py -h
shopping: A very unhelpful shopping list CLI program

Usage: shopping {{options}} {{subcommand}}

Options:
  -h, --help  Show this help message and exit

Subcommands:
  add   Add an item to the list
  view  See all items on the list
$ python shopping.py add -h
shopping add: Add an item to the list

Usage: add {{arguments}} {{options}}

Arguments:
  item [text]  

Options:
  -h, --help            Show this help message and exit
  -q, --quantity [int]  How many of the item to get (default: 1)
$ python shopping.py add
Error: Missing parameter "item".
$ python shopping.py add cookies -q 10
Added "cookies - 10" to the list
$ python shopping.py view
This is your unsorted list
$ python shopping.py view --sorted
This is your sorted list
```

## Testing

Call tests with `python setup.py test`.

## Roadmap (v0.3.0)

v0.3.0 will be a [tock](http://en.wikipedia.org/wiki/Intel_Tick-Tock) release, focused on fixing any bugs introduced in the v0.2.0 rewrite and finishing any slated features.

- [x] Finish `@TODO` items in code and tests
- [ ] Feature freeze to exercise code and find bugs

## Credits

- **[Aaargh](https://github.com/wbolster/aaargh)**: Some parsing logic
- **[Click](http://click.pocoo.org/3/)**: Decorator systems, parameter features
- **[docopt](http://docopt.org/)**: Help text formatting
