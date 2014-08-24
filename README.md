![clip.py](https://raw.github.com/willyg302/clip.py/master/clip-logo-922.png "It looks like you're trying to make a CLI.")

---

Embeddable, composable [c]ommand [l]ine [i]nterface [p]arsing

## Usage

clip.py is just a `pip install git+https://github.com/willyg302/clip.py.git@master` away. After installing, you can safely do `from clip import *`. This imports the two classes `App` and `ClipExit`.

clip.py is essentially a thin wrapper around argparse that abstracts much of its functionality into decorators and makes creating subcommands a breeze. Much of the API remains the same, so refer to the [argparse documentation](https://docs.python.org/2.7/library/argparse.html) for more information.

### Examples

Learning clip.py is done best by example, so let's look at a simple one:

```python
import os
import clip

__version__ = '1.0'

app = clip.App()
app.arg('--version', help='Print the version', action='version', version=__version__)

app.arg('-v', '--verbose', action='store_true')

@app.cmd
@app.cmd_arg('source')
@app.cmd_arg('-d', '--dest')
def init(source, dest, verbose):
	print source, dest, verbose

@app.cmd
@app.cmd_arg('tasks', nargs='*')
@app.cmd_arg('-d', '--dir', default=os.getcwd())
def run(tasks, dir, verbose):
	print tasks, dir, verbose

try:
	app.run()
except clip.ClipExit as e:
	print 'Exit status: {}'.format(e.status)
```

Assuming this code is saved in a file called `a.py`, we can then do:

```bash
$ python a.py
usage: a.py [-h] [--version] [-v] {init,run} ...
a.py: error: too few arguments
Exit status: 2
$ python a.py -h
usage: a.py [-h] [--version] [-v] {init,run} ...

optional arguments:
  -h, --help     show this help message and exit
  --version      Print the version
  -v, --verbose

Subcommands:
  {init,run}
    init
    run
Exit status: 0
$ python a.py --version
1.0
Exit status: 0
$ python a.py init
usage: init [-h] [-d DEST] source
init: error: too few arguments
Exit status: 2
$ python a.py init this
this None False
$ python a.py -v run dude
['dude'] /Users/Somebody/cliptest True
```

Note that, as a formality, a `ClipExit` exception is always raised upon exit even if no error occurred. This encourages applications to always handle the exit status of a program.

So that's cool, but suppose you just want a regular old single-command program? No problem. Let's see how you would do `echo`:

```python
import os
import clip

app = clip.App()
	
@app.cmd
@app.cmd_arg('words', nargs='*')
def echo(words):
	print(' '.join(words))

try:
	app.run(main=echo)
except clip.ClipExit:
	pass
```

And the functionality:

```bash
$ python b.py -h
usage: echo [-h] [words [words ...]]

positional arguments:
  words

optional arguments:
  -h, --help  show this help message and exit
$ python b.py this is    cool
this is cool
```

All you have to do is pass the main function to `App.run()` as the `main` argument. Note that this automatically handles substituting the program name in help messages.

### Helper Methods

#### `App.confirm(prompt, default='yes')`

Prompt the user for confirmation (a yes/no question). `default` must be one of `'yes'`, `'no'`, or `None` (meaning that input is required from the user).

### Advanced: Embedded CLI

One of the neat features of clip.py is that it handles modular code and stream substitution gracefully (if this doesn't make sense quite yet, that's okay). What this allows us to do is write an *embedded* application. As an example, let's look at our previous `echo` program rewritten in embedded form:

```python
'''Echoes things'''
import os

def _run(args):

	@cli.cmd
	@cli.cmd_arg('words', nargs='*')
	def echo(words):
		print(' '.join(words))

	cli.run(args, main=echo)
```

Whoa, no reference to `clip`! And what's that `cli` variable doing there, that's definitely going to throw an error! ...or will it? Let's assume this code is in `c.py`. Then we can write "wrapper" code in `wrap.py`:

```python
import sys
import clip
import c

class StdStream(object):
	def __init__(self, stream=None):
		self._stream = sys.stdout if stream is None else stream

	def write(self, message):
		self._stream.write(message)

stdout = StdStream()
stderr = StdStream(sys.stderr)

app = clip.App(stdout=stdout, stderr=stderr, module=c)
app.arg('--version', help='Print the version', action='version',
	    version=c.__version__ if '__version__' in dir(c) else 'No version specified')

c._run.func_globals['cli'] = app
try:
	c._run(sys.argv[1:])
except clip.ClipExit as e:
	print 'Exit status: {}'.format(e.status)
```

You'll notice a lot of strange Python magics going on here, but the crucial line is where we instantiated `clip.App()`, passing in arguments to our custom `stdout` and `stderr` stream, as well as a reference to our `c.py` module. What does this do? Well...

```bash
$ python wrap.py -h
usage: echo [-h] [--version] [words [words ...]]

Echoes things

positional arguments:
  words

optional arguments:
  -h, --help  show this help message and exit
  --version   Print the version
Exit status: 0
$ python wrap.py Whoa look at that
Whoa look at that
$ python wrap.py --version
No version specified
Exit status: 0
```

Of course, the real power of streams comes when you want to start dumping this stuff to a file as well. Or printing it in a GUI.

## Credits

- **[Aaargh](https://github.com/wbolster/aaargh)**: Copyright 2012-2013 Wouter Bolsterlee. Licensed under the OSI approved 3-clause "New BSD License".
