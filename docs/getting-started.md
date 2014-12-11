# Getting Started




<!-- @TODO This is from the old readme -->

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