# clip Documentation

## Contents

## FAQ

### Why use clip instead of [other CLI tool]?

I have used a whole bunch of Python CLI tools: [docopt](http://docopt.org/), [argparse](https://docs.python.org/3/library/argparse.html) (the Python standard), [Click](http://click.pocoo.org/3/), and even more obscure ones like [Aaargh](https://github.com/wbolster/aaargh), just to name a few. All of these work very well and do their intended jobs. There is nothing inherently wrong with any of them.

However, every CLI tool has different goals. clip exists to satisfy two pain points that I feel other tools don't address fully:

- **Embedding**: Many tools assume far too much about the environment they are running in. For example, Click has integrations for fetching terminal dimensions and setting environment variables. This is cool and useful, but it also means trying to use Click for an embedded CLI (say, one running in a text editor communicating via websockets) is a *huge* issue.
- **Composing**: It should be extremely easy to define subcommands, without sacrificing the simplicity of a single-command program. With clip, composability takes a front seat.

clip is not as full-featured as other CLI tools, nor does it strive to be. If you feel clip is missing something critical, file a pull request or issue! Otherwise, there are other tools out there.
