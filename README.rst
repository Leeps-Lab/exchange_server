Python 3.6

Docker:

::

    docker-compose up
    
creates a multicontainer Docker application. 3 servers with auction formats: CDA, FBA, IEX will listen on host ports 9001 to 9003. configured over environment variables declared in docker-compsose.yaml .

Dependencies:

::

    pip install -r requirements.txt

To run a CDA instance:

::

    python3 run_exchange_server.py --host 0.0.0.0 --port 9001 --debug --mechanism cda
    
To run a FBA instance with batch length of 3 seconds:

::

    python3 run_exchange_server.py --host 0.0.0.0 --port 9101 --debug --mechanism fba --interval 3

To run an IEX instance with a speed bump delay of 1 second:

::

    python3 run_exchange_server.py --host 0.0.0.0 --port 9201 --debug --mechanism iex --delay 1
