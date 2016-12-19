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


class PicassoClient(object):

    def __init__(self, os_auth_url, os_username, os_password, os_project_name):

        auth = generic.Password(auth_url=os_auth_url,
                                username=os_username,
                                password=os_password,
                                project_name=os_project_name,
                                project_domain_id="default",
                                user_domain_id="default")
        auth_session = session.Session(auth=auth)
        self.__client = client.Client('v1', session=auth_session)

    @property
    def client(self):
        return self.__client
