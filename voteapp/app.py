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
import click
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
        cfg = Config.config_instance()
        task_data = {
            'pg_dns': cfg.pg_dns,
            'vote': vote,
            'vote_id': voter
        }
        res = cfg.picassoclient.routes.execute(cfg.app_name, "/vote", **task_data)
        response = aiohttp_jinja2.render_template("index.html", request, {
            "option_a": OPTION_A,
            "option_b": OPTION_B,
            "hostname": HOSTNAME,
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
        data = json.loads(str_results['result'])
        response = aiohttp_jinja2.render_template("results.html", request, {
            "option_a": OPTION_A,
            "option_b": OPTION_B,
            "option_a_percent": data.get("{}_percent".format(OPTION_A)),
            "option_b_percent": data.get("{}_percent".format(OPTION_B)),
            "total": data.get("total")
        })
        return response


class VoteApp(service.HTTPService):

    def __init__(self, host: str='0.0.0.0',
                 port: int=9999,
                 pg_dns: str=None,
                 app_name: str=None,
                 picassoclient: picasso.PicassoClient=None,
                 loop: asyncio.AbstractEventLoop=asyncio.get_event_loop(),
                 logger=None,
                 debug=False):

        tmpl_path = os.path.join(os.getcwd(), 'templates')

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

        def check_route(app_name, *args, **kwargs):
            try:
                _route = picassoclient.client.routes.create(
                    app_name, *args, **kwargs)
                print('Route created', _route['route'])
            except Exception as ex:
                print('Route found',
                      picassoclient.client.routes.show(app_name, args[1]))
                return

        print('App found', picassoclient.client.apps.show(app_name)['app'])
        check_route(app_name, "async", "/vote",
                    "denismakogon/vote-task", timeout=60)
        check_route(app_name, "sync", "/results",
                    "denismakogon/result-task", timeout=60)

        Config(
            picassoclient=picassoclient.client,
            app_name=app_name,
            pg_dns=pg_dns,
        )
        print("Initialization finished.")


@click.command(name='picasso-api')
@click.option('--host',
              default=os.getenv("VOTEAPP_HOST", '0.0.0.0'),
              help='API service host.')
@click.option('--port', default=int(os.getenv("VOTEAPP_PORT", 9999)),
              help='API service port.')
@click.option('--pg-host',
              default=os.getenv("PG_HOST"),
              help='VoteApp PostgreSQL connection.')
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
@click.option("--app-name", help="Fn/Picasso", default=os.getenv('APP_NAME'))
@click.option("--os-auth-url", default=os.getenv("OS_AUTH_URL"))
@click.option("--os-username", default=os.getenv("OS_USERNAME"))
@click.option("--os-password", default=os.getenv("OS_PASSWORD"))
@click.option("--os-project-name", default=os.getenv("OS_PROJECT_NAME"))
def server(host, port, pg_host,
           pg_username, pg_password,
           pg_db, app_name, os_auth_url,
           os_username, os_password, os_project_name):
    pg_dns = (
        'dbname={database} user={user} password={passwd} host={host}'
        .format(
            host=pg_host,
            database=pg_db,
            user=pg_username,
            passwd=pg_password)
    )
    picassoclient = picasso.PicassoClient(
        os_auth_url, os_username,
        os_password, os_project_name)
    loop = asyncio.get_event_loop()
    VoteApp(app_name=app_name,
            port=port,
            picassoclient=picassoclient,
            host=host, pg_dns=pg_dns,
            loop=loop).initialize()

if __name__ == "__main__":
    server()
