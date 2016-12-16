# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import asyncio
import aiohttp_jinja2
import jinja2
import json
import os
import random
import socket

from aioservice.http import requests
from aioservice.http import controller
from aioservice.http import service

from voteapp import picasso

OPTION_A = "cats"
OPTION_B = "dogs"
HOSTNAME = socket.gethostname()
APP_NAME = str(__package__)


class Singleton(type):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class Config(object, metaclass=Singleton):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.config = self

    @classmethod
    def config_instance(cls):
        return cls._instance.config


class Votes(controller.ServiceController):
    controller_name = "vote"
    version = "v1"

    @requests.api_action(method="GET", route="vote")
    async def get_votes(self, request):
        voter = hex(random.getrandbits(64))[2:-1]
        response = aiohttp_jinja2.render_template("index.html", request, {
            "option_a": OPTION_A,
            "option_b": OPTION_B,
            "hostname": HOSTNAME,
            "vote": None,
        })
        response.set_cookie('voter_id', voter)
        return response

    @requests.api_action(method="POST", route="vote")
    async def submit_vote(self, request):
        data = await request.post()
        vote = data['vote']
        voter = hex(random.getrandbits(64))[2:-1]
        cfg = Config.config_instance()
        task_data = {
            'pg_dns': cfg.pg_dns,
            'vote': vote,
            'vote_id': voter
        }
        cfg.picassoclient.routes.execute(cfg.app_name, "/vote", **task_data)
        response = aiohttp_jinja2.render_template("index.html", request, {
            "option_a": OPTION_A,
            "option_b": OPTION_B,
            "hostname": HOSTNAME,
            "vote": None,
        })
        return response

    @requests.api_action(method="GET", route="results")
    async def get_results(self, request):
        cfg = Config.config_instance()
        task_data = {
            'pg_dns': cfg.pg_dns,
        }
        str_results = cfg.picassoclient.routes.execute(
            cfg.app_name, "/results", **task_data)
        data = json.loads(str_results)
        response = aiohttp_jinja2.render_template("results.html", request, {
            "option_a": OPTION_A,
            "option_b": OPTION_B,
            "hostname": HOSTNAME,
            "option_a_percent": data.get("{}_percent".format(OPTION_A)),
            "option_b_percent": data.get("{}_percent".format(OPTION_B)),
            "total": data.get("total")
        })
        return response


class Results(controller.ServiceController):
    controller_name = "results"
    version = "v1"

    @requests.api_action(method="GET", route="results")
    async def get_results(self, request):
        pass


class VoteApp(service.HTTPService):

    def __init__(self, host: str='0.0.0.0',
                 port: int=9999,
                 loop: asyncio.AbstractEventLoop=asyncio.get_event_loop(),
                 logger=None,
                 debug=False):

        v1 = service.VersionedService(controllers=[
            Votes, Results
        ])

        super(VoteApp, self).__init__(
            host=host,
            port=port,
            event_loop=loop,
            logger=logger,
            debug=debug,
            subservice_definitions=[
                v1
            ],
        )
        aiohttp_jinja2.setup(self.root,
                             loader=jinja2.FileSystemLoader(
                                 os.path.join(os.getcwd(), 'templates')))

        self.picasso = picasso.PicassonClient()
        app = self.picasso.client.apps.create(APP_NAME)
        print(app)
        vote_route = self.picasso.client.routes.create(
            app["app"]["name"], "async", "/vote",
            "denismakogon/vote-task", timeout=60)
        print(vote_route)
        result_route = self.picasso.client.routes.create(
            app["app"]["name"], "sync", "/results",
            "denismakogon/result-task", timeout=60)
        print(result_route)
        Config(
            picassoclient=self.picasso.client,
            app_name=app["app"]["name"],
            pg_dns='dbname=votes user=root password=root host=127.0.0.1'
        )

# TODO(denismakogon): Add click
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    VoteApp(loop=loop).initialize()
