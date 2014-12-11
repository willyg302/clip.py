# How clip Works

> **NOTE**: This section is intended for those who want to understand the inner workings of clip. If you just want to *use* clip, you can stop reading right now. On the other hand, if you want to contribute to clip development, read on!

Handling command line input seems deceptively simple up front: it's just a string of tokens, right? However, there are many things that can go wrong and, perhaps even worse, many subtleties to CLI token parsing that complicate the matter a thousand-fold.

Here, we will illustrate how clip works by walking through a single invocation of the Swedish Chef program in the README:

```
$ python chef.py cook bork --count 3
```

Along the way we will also address certain features that aren't covered by the above command, such as default values and inherited parameters. Ready? Great, let's get started!

## Step 1: Building the CLI

## Step 2: Parsing

## Step 3: Invoking

## Step 4: Cleaning Up

<!-- @TODO -->
