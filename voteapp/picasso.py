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

from keystoneauth1.identity import generic
from keystoneauth1 import session
from picassoclient import client


class PicassonClient(object):

    def __init__(self):
        OS_AUTH_URL = "http://192.168.0.114:5000/v3"
        OS_USERNAME = "demo"
        OS_PASSWORD = "root"
        OS_PROJECT_NAME = "demo"

        auth = generic.Password(auth_url=OS_AUTH_URL,
                                username=OS_USERNAME,
                                password=OS_PASSWORD,
                                project_name=OS_PROJECT_NAME,
                                project_domain_id="default",
                                user_domain_id="default")
        auth_session = session.Session(auth=auth)
        self.__client = client.Client('v1', session=auth_session)

    @property
    def client(self):
        return self.__client
