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
assert session.get(api_url + "/1.0/storage-pools/test").json() == {"error": "",
                                                                   "error_code": 0,
                                                                   "metadata": {"config": {
                                                                       "source": "/var/lib/lxd/storage-pools/test"},
                                                                       "description": "",
                                                                       "driver": "dir",
                                                                       "name": "test",
                                                                       "used_by": [
                                                                           "/1.0/containers/dummy",
                                                                           "/1.0/profiles/test"]},
                                                                   "operation": "",
                                                                   "status": "Success",
                                                                   "status_code": 200,
                                                                   "type": "sync"}
assert session.get(api_url + "/1.0/networks/test0").json() == {"status": "Success",
                                                               "operation": "",
                                                               "error_code": 0,
                                                               "error": "",
                                                               "type": "sync",
                                                               "status_code": 200,
                                                               "metadata": {"description": "",
                                                                            "config": {
                                                                                "ipv4.nat": "true",
                                                                                "ipv4.address": "10.42.254.1/24",
                                                                                "dns.mode": "dynamic",
                                                                                "dns.domain": "test",
                                                                                "ipv6.address": "none"},
                                                                            "type": "bridge",
                                                                            "used_by": [
                                                                                "/1.0/containers/dummy"],
                                                                            "name": "test0",
                                                                            "managed": True}}
assert session.get(api_url + "/1.0/profiles/test").json() == {"status_code": 200,
                                                              "status": "Success",
                                                              "error": "",
                                                              "error_code": 0,
                                                              "type": "sync",
                                                              "operation": "",
                                                              "metadata": {
                                                                  "name": "test",
                                                                  "used_by": ["/1.0/containers/dummy"],
                                                                  "config": {},
                                                                  "description": "",
                                                                  "devices": {
                                                                      "root": {"path": "/",
                                                                               "pool": "test",
                                                                               "type": "disk"},
                                                                      "eth0": {"type": "nic",
                                                                               "parent": "test0",
                                                                               "nictype": "bridged"}}}}
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
assert container_json == {"error": "",
                          "error_code": 0,
                          "metadata": {"architecture": "x86_64",
                                       "description": "",
                                       "devices": {},
                                       "ephemeral": False,
                                       "expanded_config": {"image.architecture": "amd64",
                                                           "image.os": "Ubuntu",
                                                           "image.release": "xenial",
                                                           "volatile.apply_template": "create",
                                                           "volatile.eth0.name": "eth0",
                                                           "volatile.idmap.base": "0"},
                                       "expanded_devices": {"eth0": {"nictype": "bridged",
                                                                     "parent": "test0",
                                                                     "type": "nic"},
                                                            "root": {"path": "/",
                                                                     "pool": "test",
                                                                     "type": "disk"}},
                                       "last_used_at": "1970-01-01T00:00:00Z",
                                       "name": "dummy",
                                       "profiles": ["test"],
                                       "stateful": False,
                                       "status": "Stopped",
                                       "status_code": 102},
                          "operation": "",
                          "status": "Success",
                          "status_code": 200,
                          "type": "sync"}

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
