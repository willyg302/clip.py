# Embedding

One of clip's strengths is its support for *embedded* applications.



<!-- @TODO This is from the old readme -->

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