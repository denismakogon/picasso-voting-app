Cats versus Dogs vote app
=========================

Architecture
------------

Current architecture includes 4 major components. Two of the are daemons::

    PostgreSQL 9.5
    VotingApp

Two of them are functions containers::

    denismakogon/vote-task
    denismakogon/result-task


Execution flow
--------------

When user votes (sends HTTP Post) VoteApp HTTP route handler triggers asynchronous voting function,
this function saves user's vote to persistent storage - PostgreSQL.

Once user wants to retrieve get voting results (sends HTTP Get) VoteApp HTTP route handler
triggers synchronous resulting function to retrieve voting statistics.

Building function images
------------------------

You can build your own images from given functions, but you are feel free to use pre-built and uploaded to DockerHub images::

    denismakogon/vote-task
    denismakogon/result-task


Running PostgreSQL container
----------------------------

Personally recommend to use `this PG image`_ because it has 1M+ pulls.
Use following commands to start PG container::

    docker pull sameersbn/postgresql:latest
    docker run --name postgresql -d -p 0.0.0.0:5432:5432 --env-file voteapp/voteapp.env sameersbn/postgresql:latest

VoteApp configuration
---------------------

VoteApp depends on big set of parameters like::

    API host
    API port
    PostgreSQL host
    PostgreSQL user/password
    PostgreSQL database

Not all of them are mandatory, almost all parameter can be applied as operating system environment variables::

    VOTEAPP_HOST stands for --host
    VOTEAPP_POST stands for --port
    PG_HOST stands for --pg-host
    DB_USER stands for --pg-username
    DB_PASS stands for --pg-password
    DB_NAME stands for --pg-db
    APP_NAME stands for --app-name

Not all of them are defined with default values, that is why there are only several of them are required, for our particular case::

    VOTEAPP_HOST
    VOTEAPP_PORT

are not required because they were defined with default values.

VoteApp is identified by single Python module **app.py** that is CLI tool to start a web service::

    Usage: app.py [OPTIONS]

    Options:
      --host TEXT             API service host.
      --port INTEGER          API service port.
      --pg-host TEXT          PostgreSQL connection host.
      --pg-username TEXT      VoteApp PostgreSQL user.
      --pg-password TEXT      VoteApp PostgreSQL user password.
      --pg-db TEXT            VoteApp PostgreSQL connection.
      --app-name TEXT         Existing Picasso app name
      --help                  Show this message and exit.

Building VoteApp container
--------------------------

In order to simplify VoteApp usage, i recommend to build a container from it, corresponding Dockerfile included.
Also there's a file - voteapp.env, you should be aware that it's a sample file, because it is required to adjust a lot parameters there like::

    VoteApp daemon configuration
    PosgreSQL configuration

Once env file is ready use following command to build a container::

    docker build -t voteapp .

To start a container::

    docker run --name voteapp -d -p 0.0.0.0:11111:9999 --env-file voteapp.env voteapp

Or you can use pre-built container::

    denismakogon/voteapp

To pull container::

    docker pull denismakogon/voteapp

To start container::

    docker run --name voteapp -d -p 0.0.0.0:11111:9999 --env-file voteapp.env denismakogon/voteapp

.. _this PG image: https://hub.docker.com/_/postgres/
