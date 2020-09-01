# Declarative CLI

Declare your application's CLI in a YAML file, mapping subcommands onto functions and accepting a range of argument types.

Supports Python3.5+.


## Examples

Try out the main example with the following commands:
```bash
# Root help:  
python3 -m examples.ex1 -h
# Try running the app (venv not set up):  
python3 -m examples.ex1
# Venv help:  
python3 -m examples.ex1 venv -h
# Check venv (not set up):  
python3 -m examples.ex1 venv --check
# Set up venv:  
python3 -m examples.ex1 venv
# Check venv (set up):  
python3 -m examples.ex1 venv --check
# Run the app (now works!):  
python3 -m examples.ex1
# Running venv command again is no-harm:  
python3 -m examples.ex1 venv
# Bot help:  
python3 -m examples.ex1 bot -h
# Bot 'user' subcommand:  
python3 -m examples.ex1 bot user -h
# Bot 'user add' subcommand:  
python3 -m examples.ex1 bot user add -h
# Add a bot user:  
python3 -m examples.ex1 bot user add player1
# Run a bot command:  
python3 -m examples.ex1 bot some command
# Run a bot command with positional argument escape:    
python3 -m examples.ex1 bot -- -h
# Tests help:  
python3 -m examples.ex1 tests -h
# Pytest help (missing dependency):  
python3 -m examples.ex1 tests --pytest-help
# Check venv dev requirements (not installed):  
python3 -m examples.ex1 venv --check --dev
# Install dev requirements:  
python3 -m examples.ex1 venv --dev
# Check venv dev requirements (now installed):  
python3 -m examples.ex1 venv --check --dev
# Pytest help (now works!):  
python3 -m examples.ex1 tests --pytest-help
```


## Known Limitations

Does not seem to work properly with pyenv - uses the base python executable on Linux, which may be of a different version.
