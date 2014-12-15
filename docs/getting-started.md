Learning clip is best done by example, so this guide will walk you through making the shopping list program in the README. Here it is again, in case you've forgotten:

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

## The Walkthrough

```python
import clip
```

The first step is, of course, to import clip. Always prefer a direct `import` to `from clip import ...` when working with clip, because the library contains internal state that would be lost when using `from`. Arguably, this also makes it easier to see which parts of your code are CLI-specific.

```python
app = clip.App()
```

Every CLI program you make with clip is encapsulated within an `App`. Scoping your program to this single variable has many advantages: you can have more than one app if you want, and you can even pass apps around like hot potatoes!

```python
@app.main(description='A very unhelpful shopping list CLI program')
def shopping():
	pass
```

Every app must have a single main function. This defines the entry point of your CLI. To specify the main function, you use the `@app.main()` decorator.

What this decorator does is turn your boring `shopping()` function into a superpowered clip `Command`. In this particular example there's not much to see because we haven't associated any parameters with our main function, so let's look at a more interesting example of a command now:

```python
@shopping.subcommand(description='Add an item to the list')
@clip.arg('item', required=True)
@clip.opt('-q', '--quantity', default=1, help='How many of the item to get')
def add(item, quantity):
	clip.echo('Added "{} - {}" to the list'.format(item, quantity))
```

One of the cool things about clip is that every command can have unlimited subcommands. You attach a subcommand to a command by using its name in a decorator. In this case, our main command was called `shopping()`, so we use the `@shopping.subcommand()` decorator.

Now let's have some real fun and give this subcommand some parameters! The first thing to understand is that there are basically two types of parameters: positional and optional. A positional parameter, most commonly called an *argument*, gets associated with a variable based on its position in the user input. An optional parameter, usually called an *option*, must be prefixed with the option name, e.g. `-c` or `--count`.

Here we are defining one argument called "item" by using the `@clip.arg()` decorator. We are also defining an option called "quantity" by using the `@clip.opt()` decorator. These will automagically get passed into our `add()` function as the `item` and `quantity` parameters, respectively.

In each decorator we can pass additional keyword arguments, internally called *parameter attributes*, to customize our parameters. Above, we make the "item" argument required by setting `required=True`; an error will be thrown if an item is not specified by the user. Similarly, we give a default value for the "quantity" in case it is not given by the user via `default=1`.

Finally, notice the function `clip.echo()`. This works exactly like `print()` most of the time -- the exception is when you are creating [embedded](embedding.md) CLI programs, but that's a more advanced topic. It is recommended you use `clip.echo()` in place of `print()` where possible, again to clearly denote that the code is CLI-related.

```python
@shopping.subcommand(description='See all items on the list')
@clip.flag('--sorted', help='View items in alphabetical order')
def view(sorted):
	clip.echo('This is your {}sorted list'.format('' if sorted else 'un'))
```

Here's another subcommand. The one interesting feature here is the `@clip.flag()` decorator. A *flag* is a special kind of option that's true if it appears and false otherwise. Thus if the user types "view", `sorted` will be `False`, whereas if the user types "view --sorted", `sorted` will be `True`.

Although all parameters are either arguments or options, there are some common patterns in CLI parameters. A flag is one of them, and if you've ever had to type `netstat -plant` you've seen five flags already. Flags are so useful and prevalent that they get their own decorator! In a [later section](extending-clip.md) you'll see how you can make your very own decorators for common patterns in your command-line applications.

```python
if __name__ == '__main__':
	try:
		app.run()
	except clip.ClipExit:
		pass
```

Every app you make with clip will likely have this boilerplate right at the end. In order to get your app to actually *do* something, you need to call `app.run()`. Note that this pulls user input from `sys.argv`, but you could just as easily pass your own in: `app.run('view --sorted')`.

Finally, you should catch the `ClipExit` exception, which is a normal way for clip to exit your app. Most of the time you will not need to do anything else except catch the exception, but each `ClipExit` has a `status` (0 in the case of no error) and `message` in the event that you need to inspect an error.

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

```diff
$ python echo.py Hello world!
Hello world!
$ python echo.py idk     what i doinggggg      hahahaa a
idk what i doinggggg hahahaa a
```

## Now What?

Congratulations! If you've made it this far, you probably already know enough to handle 99% of the apps you will make with clip. But clip can do more...a whole lot more. Feel free to explore the docs to uncover the hidden 1%!
