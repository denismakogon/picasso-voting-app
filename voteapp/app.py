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
import aiohttp
import aiohttp_jinja2
import click
import jinja2
import json
import os
import random
import socket

from aiohttp import web

from aioservice.http import requests
from aioservice.http import controller
from aioservice.http import service


OPTION_A = "cats"
OPTION_B = "dogs"
HOSTNAME = socket.gethostname()


class PicassoClient(object):

    def __init__(self):
        pass


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
    version = "voteapp"

    @requests.api_action(method="GET", route="vote")
    async def index(self, request):
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
        voter = dict(request.cookies)['voter_id']
        print(voter)
        cfg = Config.config_instance()
        task_data = {
            "pg_host": cfg.pg_host,
            "pg_port": cfg.pg_port,
            "pg_db": cfg.pg_db,
            "pg_user": cfg.pg_user,
            "pg_pswd": cfg.pg_pswd,
            "vote": vote,
            "vote_id": voter
        }
        with aiohttp.ClientSession() as s:
            resp = await s.post(
                "{}/r/{}{}".format(cfg.api_url, cfg.app_name, cfg.vote_route),
                json=task_data
            )
            resp.raise_for_status()
        return web.HTTPFound("/voteapp/results")

    @requests.api_action(method="GET", route="results")
    async def get_results(self, request):
        with aiohttp.ClientSession() as s:
            cfg = Config.config_instance()
            task_data = {
                "pg_host": cfg.pg_host,
                "pg_port": cfg.pg_port,
                "pg_db": cfg.pg_db,
                "pg_user": cfg.pg_user,
                "pg_pswd": cfg.pg_pswd,
            }
            str_results = await s.post(
                "{}/r/{}{}".format(cfg.api_url, cfg.app_name, cfg.results_route),
                json=task_data
            )
            str_results.raise_for_status()
            txt = await str_results.text()
            data = json.loads(txt)
            response = aiohttp_jinja2.render_template("results.html", request, {
                "option_a": OPTION_A,
                "option_b": OPTION_B,
                "option_a_percent": data.get("{}_percent".format(OPTION_A)),
                "option_b_percent": data.get("{}_percent".format(OPTION_B)),
                "total": data.get("total")
            })
            return response

    @requests.api_action(method="POST", route="results")
    async def go_back_to_votes(self, request):
        return web.HTTPFound("/voteapp/vote")


class VoteApp(service.HTTPService):

    def __init__(self, host: str='0.0.0.0',
                 port: int=9999,
                 pg_host: str=None,
                 pg_port: str= None,
                 pg_db: str=None,
                 pg_user: str=None,
                 pg_pswd: str=None,
                 app_name: str=None,
                 api_url: str=None,
                 loop: asyncio.AbstractEventLoop=asyncio.get_event_loop(),
                 logger=None,
                 debug=False):

        tmpl_path = os.path.join(os.getcwd(), 'templates')
        self.api_url = api_url
        self.app_name = app_name

        def jinja_hook(subapp):
            aiohttp_jinja2.setup(subapp,
                                 loader=jinja2.FileSystemLoader(tmpl_path))

        v1 = service.VersionedService(controllers=[
            Votes,
        ], service_hooks=[jinja_hook, ])

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

        def check_route(app_name, ftype, route, image, fformat="default", timeout=60):
                # creating function's app/route
                async def do_request():
                    with aiohttp.ClientSession() as session:
                        try:
                            _route = await session.post(
                                "{}/v1/apps/{}/routes".format(api_url, app_name),
                                json={
                                    "route": {
                                            "image": image,
                                            "path": route,
                                            "type": ftype,
                                            "timeout": timeout,
                                            "format": fformat,
                                        }
                                })
                            _route.raise_for_status()
                            _route = await _route.json()
                            _app = await session.get("{}/v1/apps/{}".format(api_url, app_name))
                            _app.raise_for_status()
                            _app = await _app.json()
                            print('Route created', _route['route'])
                            print('App found', _app['app'])
                        except Exception as _:
                            _app = await session.get("{}/v1/apps/{}".format(api_url, app_name))
                            _app.raise_for_status()
                            _app = await _app.json()
                            print('App found', _app['app'])
                            _route = await session.get(
                                "{}/v1/apps/{}/routes{}".format(api_url, app_name, route))
                            _route.raise_for_status()
                            _route = await _route.json()
                            print("Route found: ", _route['route'])
                            return

                loop.run_until_complete(do_request())

        check_route(app_name, "async", "/vote",
                    "denismakogon/vote-task:0.0.4", fformat="default", timeout=60)
        check_route(app_name, "sync", "/results",
                    "denismakogon/result-task:0.0.4", fformat="default", timeout=60)
        check_route(app_name, "async", "/vote-hot",
                    "denismakogon/votetask-hot:0.0.14", fformat="http", timeout=60)

        Config(
            api_url=api_url,
            app_name=app_name,
            pg_host=pg_host,
            pg_port=pg_port,
            pg_db=pg_db,
            pg_user=pg_user,
            pg_pswd=pg_pswd,
            vote_route="/vote-hot",
            results_route="/results"
        )

        super(VoteApp, self).apply_swagger()
        print("Initialization finished.")


@click.command(name='picasso-api')
@click.option('--host',
              default=os.getenv("VOTEAPP_HOST", '0.0.0.0'),
              help='API service host.')
@click.option('--port', default=int(os.getenv("VOTEAPP_PORT", 9999)),
              help='API service port.')
@click.option('--pg-host',
              default=os.getenv("PG_HOST", "localhost"),
              help='PostgreSQL connection host.')
@click.option('--pg-port',
              default=os.getenv("PG_PORT", "5432"),
              help='PostgreSQL connection port.')
@click.option('--pg-username',
              default=os.getenv("DB_USER", "postgres"),
              help='VoteApp PostgreSQL user.')
@click.option('--pg-password',
              default=os.getenv("DB_PASS", "postgres"),
              help='VoteApp PostgreSQL user password.')
@click.option('--pg-db',
              default=os.getenv(
                  "DB_NAME", 'votes'),
              help='VoteApp PostgreSQL connection.')
@click.option("--app-name", help="Existing Picasso app name",
              default=os.getenv('APP_NAME', 'votes'))
@click.option("--api-url", help="Existing Picasso app name",
              default=os.getenv('API_URL', "http://localhost:8080"))
def server(host, port, pg_host, pg_port,
           pg_username, pg_password,
           pg_db, app_name, api_url):
    loop = asyncio.get_event_loop()
    VoteApp(
        app_name=app_name,
        api_url=api_url,
        port=port,
        host=host,
        pg_host=pg_host,
        pg_port=pg_port,
        pg_db=pg_db,
        pg_user=pg_username,
        pg_pswd=pg_password,
        loop=loop
    ).initialize()

if __name__ == "__main__":
    server()
