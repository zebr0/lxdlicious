#!/usr/bin/python3 -u

import subprocess
import sys

import requests_unixsocket


def run(command):
    subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr).wait()


# opens a unix socket session to call the lxd api
session = requests_unixsocket.Session()
api_url = "http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket"

# ensures the test resources don't exist before continuing
run("cat test.yml | ../src/lxd-compose delete")

# test creating a stack (twice, for idempotence)
run("cat test.yml | ../src/lxd-compose create")
run("cat test.yml | ../src/lxd-compose create")
assert session.get(api_url + "/1.0/storage-pools/test").json() == {'error': '',
                                                                   'error_code': 0,
                                                                   'metadata': {'config': {'source': '/var/lib/lxd/storage-pools/test'},
                                                                                'description': '',
                                                                                'driver': 'dir',
                                                                                'locations': ['none'],
                                                                                'name': 'test',
                                                                                'status': 'Created',
                                                                                'used_by': ['/1.0/containers/dummy', '/1.0/profiles/test']},
                                                                   'operation': '',
                                                                   'status': 'Success',
                                                                   'status_code': 200,
                                                                   'type': 'sync'}
assert session.get(api_url + "/1.0/networks/test0").json() == {'error': '',
                                                               'error_code': 0,
                                                               'metadata': {'config': {'dns.domain': 'test',
                                                                                       'dns.mode': 'dynamic',
                                                                                       'ipv4.address': '10.42.254.1/24',
                                                                                       'ipv4.nat': 'true',
                                                                                       'ipv6.address': 'none'},
                                                                            'description': '',
                                                                            'locations': ['none'],
                                                                            'managed': True,
                                                                            'name': 'test0',
                                                                            'status': 'Created',
                                                                            'type': 'bridge',
                                                                            'used_by': ['/1.0/containers/dummy']},
                                                               'operation': '',
                                                               'status': 'Success',
                                                               'status_code': 200,
                                                               'type': 'sync'}
assert session.get(api_url + "/1.0/profiles/test").json() == {'error': '',
                                                              'error_code': 0,
                                                              'metadata': {'config': {},
                                                                           'description': '',
                                                                           'devices': {'eth0': {'nictype': 'bridged',
                                                                                                'parent': 'test0',
                                                                                                'type': 'nic'},
                                                                                       'root': {'path': '/',
                                                                                                'pool': 'test',
                                                                                                'type': 'disk'}},
                                                                           'name': 'test',
                                                                           'used_by': ['/1.0/containers/dummy']},
                                                              'operation': '',
                                                              'status': 'Success',
                                                              'status_code': 200,
                                                              'type': 'sync'}
# cleans the api output of volatile information before testing
container_json = session.get(api_url + "/1.0/containers/dummy").json()
container_json.get("metadata").pop("created_at")
container_json.get("metadata").pop("config")
container_json.get("metadata").get("expanded_config").pop("volatile.base_image")
container_json.get("metadata").get("expanded_config").pop("volatile.idmap.next")
container_json.get("metadata").get("expanded_config").pop("volatile.last_state.idmap")
container_json.get("metadata").get("expanded_config").pop("volatile.eth0.hwaddr")
container_json.get("metadata").get("expanded_config").pop("image.description")
container_json.get("metadata").get("expanded_config").pop("image.serial")
assert container_json == {'error': '',
                          'error_code': 0,
                          'metadata': {'architecture': 'x86_64',
                                       'description': '',
                                       'devices': {},
                                       'ephemeral': False,
                                       'expanded_config': {'image.architecture': 'amd64',
                                                           'image.os': 'Ubuntu',
                                                           'image.release': 'bionic',
                                                           'volatile.apply_template': 'create',
                                                           'volatile.eth0.name': 'eth0',
                                                           'volatile.idmap.base': '0'},
                                       'expanded_devices': {'eth0': {'nictype': 'bridged',
                                                                     'parent': 'test0',
                                                                     'type': 'nic'},
                                                            'root': {'path': '/',
                                                                     'pool': 'test',
                                                                     'type': 'disk'}},
                                       'last_used_at': '1970-01-01T01:00:00+01:00',
                                       'location': '',
                                       'name': 'dummy',
                                       'profiles': ['test'],
                                       'stateful': False,
                                       'status': 'Stopped',
                                       'status_code': 102},
                          'operation': '',
                          'status': 'Success',
                          'status_code': 200,
                          'type': 'sync'}

# test starting a stack (twice, for idempotence)
run("cat test.yml | ../src/lxd-compose start")
run("cat test.yml | ../src/lxd-compose start")
assert session.get(api_url + "/1.0/containers/dummy").json().get("metadata").get("status") == "Running"

# test stopping a stack (twice, for idempotence)
run("cat test.yml | ../src/lxd-compose stop")
run("cat test.yml | ../src/lxd-compose stop")
assert session.get(api_url + "/1.0/containers/dummy").json().get("metadata").get("status") == "Stopped"

# test deleting a stack (twice, for idempotence)
run("cat test.yml | ../src/lxd-compose delete")
run("cat test.yml | ../src/lxd-compose delete")
assert session.get(api_url + "/1.0/networks/test0").json().get("error_code") == 404
assert session.get(api_url + "/1.0/profiles/test").json().get("error_code") == 404
assert session.get(api_url + "/1.0/containers/dummy").json().get("error_code") == 404

# tests if an empty configuration is handled without error, even if it does nothing
run("echo | ../src/lxd-compose create")
run("echo | ../src/lxd-compose start")
run("echo | ../src/lxd-compose stop")
run("echo | ../src/lxd-compose delete")

session.close()
