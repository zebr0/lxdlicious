from pathlib import Path

import pytest
import zebr0

import zebr0_lxd


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


LXD_STACK = """
---
storage-pools:
- name: test-storage-pool
  driver: dir

networks:
- name: test-network

profiles:
- name: test-profile

instances:
- name: test-instance
  source:
    type: none
""".lstrip()


def test_create_ok(server, monkeypatch):
    server.data = {"lxd-stack": LXD_STACK}
    log = []

    def mock_create(_, collection, resource):
        log.append((collection, resource))

    monkeypatch.setattr(zebr0_lxd.Client, "create", mock_create)

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), zebr0_lxd.Command.CREATE)
    assert log == [("storage-pools", {"name": "test-storage-pool", "driver": "dir"}),
                   ("networks", {"name": "test-network"}),
                   ("profiles", {"name": "test-profile"}),
                   ("instances", {"name": "test-instance", "source": {"type": "none"}})]


CONTAINERS_ONLY = """
---
instances:
- name: test-instance-1
  source:
    type: none
- name: test-instance-2
  source:
    type: none
""".lstrip()


def test_create_containers_only(server, monkeypatch):
    server.data = {"lxd-stack": CONTAINERS_ONLY}
    log = []

    def mock_create(_, collection, resource):
        log.append((collection, resource))

    monkeypatch.setattr(zebr0_lxd.Client, "create", mock_create)

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), zebr0_lxd.Command.CREATE)
    assert log == [("instances", {"name": "test-instance-1", "source": {"type": "none"}}),
                   ("instances", {"name": "test-instance-2", "source": {"type": "none"}})]


def test_start(server, monkeypatch):
    server.data = {"lxd-stack": LXD_STACK}
    log = []

    def mock_start(_, instance_name):
        log.append(instance_name)

    monkeypatch.setattr(zebr0_lxd.Client, "start", mock_start)

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), zebr0_lxd.Command.START)
    assert log == ["test-instance"]
