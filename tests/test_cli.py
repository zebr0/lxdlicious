import subprocess

import pytest
import zebr0

import zebr0_lxd


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


@pytest.fixture(autouse=True)
def clean_before_after():
    def clean():
        subprocess.Popen("lxc stop test-instance", shell=True).wait()
        subprocess.Popen("lxc delete test-instance", shell=True).wait()
        subprocess.Popen("lxc profile delete test-profile", shell=True).wait()
        subprocess.Popen("lxc network delete test-network", shell=True).wait()
        subprocess.Popen("lxc storage delete test-storage-pool", shell=True).wait()

    clean()
    yield  # see https://stackoverflow.com/questions/22627659/run-code-before-and-after-each-test-in-py-test
    clean()


LXD_STACK = """
---
storage-pools:
- name: test-storage-pool
  driver: dir

networks:
- name: test-network
  config:
    ipv4.address: 10.42.254.1/24
    ipv4.nat: true
    ipv6.address: none
    dns.mode: dynamic
    dns.domain: test

profiles:
- name: test-profile
  devices:
    root:
      path: /
      pool: test-storage-pool
      type: disk
    eth0:
      type: nic
      nictype: bridged
      parent: test-network

instances:
- name: test-instance
  profiles:
  - test-profile
  source:
    type: image
    mode: pull
    server: https://cloud-images.ubuntu.com/releases
    protocol: simplestreams
    alias: focal
""".lstrip()

CREATE = """
checking storage-pools/test-storage-pool
creating storage-pools/{"name": "test-storage-pool", "driver": "dir"}
checking networks/test-network
creating networks/{"name": "test-network", "config": {"ipv4.address": "10.42.254.1/24", "ipv4.nat": "true", "ipv6.address": "none", "dns.mode": "dynamic", "dns.domain": "test"}}
checking profiles/test-profile
creating profiles/{"name": "test-profile", "devices": {"root": {"path": "/", "pool": "test-storage-pool", "type": "disk"}, "eth0": {"type": "nic", "nictype": "bridged", "parent": "test-network"}}}
checking instances/test-instance
creating instances/{"name": "test-instance", "profiles": ["test-profile"], "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
""".lstrip()

START = """
checking instances/test-instance
starting instances/test-instance
""".lstrip()

STOP = """
checking instances/test-instance
stopping instances/test-instance
""".lstrip()

DELETE = """
checking instances/test-instance
deleting instances/test-instance
checking profiles/test-profile
deleting profiles/test-profile
checking networks/test-network
deleting networks/test-network
checking storage-pools/test-storage-pool
deleting storage-pools/test-storage-pool
""".lstrip()


def test_ok(server, capsys):
    server.data = {"lxd-stack": LXD_STACK}

    zebr0_lxd.main("create -u http://localhost:8000".split())
    assert capsys.readouterr().out == CREATE

    zebr0_lxd.main("start -u http://localhost:8000".split())
    assert capsys.readouterr().out == START

    zebr0_lxd.main("stop -u http://localhost:8000".split())
    assert capsys.readouterr().out == STOP

    zebr0_lxd.main("delete -u http://localhost:8000".split())
    assert capsys.readouterr().out == DELETE
