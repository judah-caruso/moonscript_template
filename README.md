# A rapid game development project template

## Credit

This repository was originally just a modified version of [buckle2000's](https://github.com/buckle2000/love2d_moonscript_template) repository. However, it's now different, has its own goals, and uses a newer version of Python than the original.

## Requirements

* [LÖVE](http://love2d.org/) >= 11.0
* [MoonScript](http://moonscript.org/) == 0.5.0
* [Python](https://www.python.org/) >= 3.8.3

## Features & Usage

To get started, simply edit `configuration.py` and set the locations of `love` and `moonc`. Note, if both of these are already in your PATH, you don't need to do this.

### Project Layout

The script will mirror the `source/` directory placing the libraries within the `thirdparty/` directory alongside the compiled source files. This means you can access your libraries like this `local lib = require 'lib'` rather than like this `local lib = require 'thirdparty.lib'`.

Assets, on the other hand, stay within their own `assets/` directory (even when building). This means they must be accessed like so: `love.graphics.newFont('assets/fonts/font.ttf', 12)`

### Compiling MoonScript to Lua

Building a project is done by running the `build.py` script. If no arguments are passed, a standard build will start. If you'd like to be explicit with this, use the `build` flag. To run the build after compilation, use the `run` flag.

By default, the build script will delete any nonexistent assets in between build passes. If you'd like to clear every file within the build directory, use the `clean` flag.

### Distribution

To build your project into an executable, use the `release` flag.  If no arguments are passed, the script will create an executable for the current operating system.
