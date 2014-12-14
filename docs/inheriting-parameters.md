clip strives to make it easy to build composable applications, so a powerful concept in clip is parameter inheritance. To illustrate how this can be useful, let's build a little Mario math program.

## The Problem

So you're working on your little Super Mario Calculator app, and it's coming along pretty good:

```python
@app.main()
def calculator():
	pass

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
def add(numbers):
	clip.echo('Add these numbers? Okay, here we gooooo!')
	clip.echo(sum(numbers))

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
def multiply(numbers):
	clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
	clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)
```

It even works!

```diff
$ python calculator.py add 1 3 5 7
Add these numbers? Okay, here we gooooo!
16
$ python calculator.py multiply 1 3 5 7
Wa-hoo, let's-a multiply these numbers!
105
```

But sometimes you think Mario should be-a quiet, so you'd like to add a little "silent" flag to your app. How would you go about doing this? Well, one way is to attach it as a parameter to the main function:

```python
talk = True

@app.main()
@clip.flag('-s', '--silent')
def calculator(silent):
	global talk
	talk = not silent

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
def add(numbers):
	if talk:
		clip.echo('Add these numbers? Okay, here we gooooo!')
	clip.echo(sum(numbers))

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
def multiply(numbers):
	if talk:
		clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
	clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)
```

Not only is this ugly, but it doesn't obey the [Principle of Least Astonishment](http://en.wikipedia.org/wiki/Principle_of_least_astonishment):

```diff
$ python calculator.py -s multiply 1 3 5 7
105
$ python calculator.py multiply -s 1 3 5 7
Error: Invalid type given to "numbers", expected int.
```

Hmm...maybe you could just add it to each subcommand?

```python
@app.main()
def calculator():
	pass

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
@clip.flag('-s', '--silent')
def add(numbers, silent):
	if not silent:
		clip.echo('Add these numbers? Okay, here we gooooo!')
	clip.echo(sum(numbers))

@calculator.subcommand()
@clip.arg('numbers', nargs=-1, type=int)
@clip.flag('-s', '--silent')
def multiply(numbers, silent):
	if not silent:
		clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
	clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)
```

Well, that's not [DRY](http://en.wikipedia.org/wiki/Don%27t_repeat_yourself) at all. And it *still* doesn't really work:

```diff
$ python calculator.py add -s 1 3 5 7
16
$ python calculator.py -s add 1 3 5 7
Error: Could not understand "-s".
```

## Inheritance to the Rescue!

By now you should be aware of *why* inheritance is necessary, so let's get right to the *how*:

```python
@app.main()
@clip.flag('-s', '--silent')
def calculator(silent):
	pass

@calculator.subcommand(inherits=['-s'])
@clip.arg('numbers', nargs=-1, type=int)
def add(numbers, silent):
	if not silent:
		clip.echo('Add these numbers? Okay, here we gooooo!')
	clip.echo(sum(numbers))

@calculator.subcommand(inherits=['--silent'])
@clip.arg('numbers', nargs=-1, type=int)
def multiply(numbers, silent):
	if not silent:
		clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
	clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)
```

And the moment of truth:

```diff
$ python calculator.py add -s 1 3 5 7
16
$ python calculator.py -s add 1 3 5 7
16
```

As Mario would say, wa-hoo! `inherits` is an array of parameters from parent commands that you'd like to be passed into the subcommand. You'll notice that you can give any form of the parameter to inherit it; above we have specified `-s` and `--silent` in the two different subcommands, but both will be matched to the correct flag.

## `inherit_only`

At this moment you might be wondering whether the code can be made cleaner. In particular, it doesn't seem useful to pass `silent` into the `calculator()` function when it's never going to be used there. This is where `inherit_only` comes into play: it tells clip that the parameter is only meant for subcommands, so it doesn't get passed into the owning command.

While we're at it, let's also fix the other glaring issue, which is that the line `@clip.arg('numbers', nargs=-1, type=int)` is repeated twice. Here's what our final calculator app looks like:

```python
@app.main()
@clip.arg('numbers', nargs=-1, type=int, inherit_only=True)
@clip.flag('-s', '--silent', inherit_only=True)
def calculator():
	pass

@calculator.subcommand(inherits=['numbers', '-s'])
def add(numbers, silent):
	if not silent:
		clip.echo('Add these numbers? Okay, here we gooooo!')
	clip.echo(sum(numbers))

@calculator.subcommand(inherits=['numbers', '--silent'])
def multiply(numbers, silent):
	if not silent:
		clip.echo('Wa-hoo, let\'s-a multiply these numbers!')
	clip.echo(reduce(lambda x, y: x * y, numbers) if numbers else 0)
```

## We Need to Go Deeper

As a final note, a subcommand can inherit parameters from **any** level above it. This rather convoluted example demonstrates this:

```python
@app.main()
@clip.flag('-a')
def w(a):
	clip.echo('a in w: {}'.format(a))

@w.subcommand()
@clip.flag('-b')
def x(b):
	clip.echo('b in x: {}'.format(b))

@x.subcommand(inherits=['a'])
@clip.flag('-c')
def y(a, c):
	clip.echo('a in y: {}'.format(a))
	clip.echo('c in y: {}'.format(c))

@y.subcommand(inherits=['a', 'b', 'c'])
@clip.flag('-d')
def z(a, b, c, d):
	clip.echo('All together now: {}'.format((a, b, c, d)))
```

And as expected:

```diff
$ python f.py -a x -b y -c z -d
a in w: True
b in x: True
a in y: True
c in y: True
All together now: (True, True, True, True)
```

Try playing around with this example, placing flags in different positions, to see how inheritance works in clip. In no time you'll get the hang of this simple but powerful concept and be able to leverage it in your own applications!
