Voting app using OpenStack Picasso
==================================

Design
------

Building components
-------------------




Running PostgreSQL and VoteApp on Docker
----------------------------------------

Personally recommend to use `this PG image`_ because it has 1M+ pulls.
Use following commands to start PG container::

    docker pull sameersbn/postgresql:latest
    docker run --name postgresql -d -p --restart always \
      --publish 0.0.0.0:5432:5432 --env-file voteapp/voteapp.env sameersbn/postgresql:latest



.. _this PG image: https://hub.docker.com/r/sameersbn/postgresql/
