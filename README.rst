installation
==============
create a virtual environment and install dependencies.
there are various tools to help you to this.

here is one way:

start by checking if you have virtualenv installed.

::
    
    virtualenv --version

the version should print on the console, if it does not 
install the virtualenv library.

::
  
    pip3 install virtualenv

and create virtual environment.

::
    
    mkdir exchange_env
    virtualenv -p python3.6 exchange_env

then activate it.

for macos/linux

::

    source exchange_env/bin/activate

for windows

::
    
    exchange_env/Scripts/activate

clone this repository and install dependencies

::

    git clone https://github.com/Leeps-Lab/exchange_server.git
    cd exchange_server

download and install dependencies:

::

    pip3 install -r requirements.txt

usage
=======

run an CDA instance:

::

    python3 run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda
    
run an FBA instance with batch length of 3 seconds:

::

    python3 run_exchange_server.py --host 0.0.0.0 --port 9101 --debug --mechanism fba --interval 3

