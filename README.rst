Voting app using OpenStack Picasso
==================================

Design
------

Building components
-------------------

You can build your own images from given functions, but you are feel free to use pre-built and uploaded to DockerHub images::

    denismakogon/vote-task
    denismakogon/result-task


Running PostgreSQL and VoteApp on Docker
----------------------------------------

Personally recommend to use `this PG image`_ because it has 1M+ pulls.
Use following commands to start PG container::

    docker pull sameersbn/postgresql:latest
    docker run --name postgresql -d -p 0.0.0.0:5432:5432 --env-file voteapp/voteapp.env sameersbn/postgresql:latest

Running VoteApp
---------------

There's main script to start VoteApp::

    voteapp/app.py

It requires additional configuration::

    Usage: app.py [OPTIONS]

    Options:
      --host TEXT             API service host.
      --port INTEGER          API service port.
      --pg-host TEXT          VoteApp PostgreSQL connection.
      --pg-host TEXT          PostgreSQL connection host.
      --pg-password TEXT      VoteApp PostgreSQL user password.
      --pg-db TEXT            VoteApp PostgreSQL connection.
      --app-name TEXT         Existing Picasso app name
      --os-auth-url TEXT      OpenStack Auth URL
      --os-username TEXT      OpenStack User
      --os-password TEXT      OpenStack User password
      --os-project-name TEXT  OpenStack User project
      --help                  Show this message and exit.

All parameters given above are not mandatory, here's a list of required ones::

      --pg-host TEXT          VoteApp PostgreSQL connection.
      --pg-host TEXT          PostgreSQL connection host.
      --pg-password TEXT      VoteApp PostgreSQL user password.
      --pg-db TEXT            VoteApp PostgreSQL connection.
      --app-name TEXT         Existing Picasso app name
      --os-auth-url TEXT      OpenStack Auth URL
      --os-username TEXT      OpenStack User
      --os-password TEXT      OpenStack User password
      --os-project-name TEXT  OpenStack User project

How it works?
-------------

When user makes his choice through API, he triggers an async voting action that goes to PostgreSQL and saves his vote that is defined by::

    vote ID
    vote

As the result he gets a redirect to resulting page, where redirecting triggers another function - sync result that pulls out voting statistics.


.. _this PG image: https://hub.docker.com/r/sameersbn/postgresql/
