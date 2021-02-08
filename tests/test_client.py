import subprocess
import time

import pytest

import zebr0_lxd
from zebr0_lxd import Resource


@pytest.fixture(scope="module")
def client():
    return zebr0_lxd.Client()


@pytest.fixture(autouse=True)
def clean_before_and_after():
    def clean():
        subprocess.run("lxc stop test-instance", shell=True)
        subprocess.run("lxc delete test-instance", shell=True)
        subprocess.run("lxc profile delete test-profile", shell=True)
        subprocess.run("lxc network delete test-network", shell=True)
        subprocess.run("lxc storage delete test-storage-pool", shell=True)

    clean()
    yield  # see https://stackoverflow.com/questions/22627659/run-code-before-and-after-each-test-in-py-test
    clean()


EXISTS_STORAGE_POOL_OUTPUT = """
checking storage-pools/test-storage-pool
checking storage-pools/test-storage-pool
""".lstrip()


def test_exists_storage_pool(client, capsys):
    assert not client.exists(Resource.STORAGE_POOLS, "test-storage-pool")
    subprocess.run("lxc storage create test-storage-pool dir", shell=True)
    assert client.exists(Resource.STORAGE_POOLS, "test-storage-pool")

    assert capsys.readouterr().out == EXISTS_STORAGE_POOL_OUTPUT


EXISTS_NETWORK_OUTPUT = """
checking networks/test-network
checking networks/test-network
""".lstrip()


def test_exists_network(client, capsys):
    assert not client.exists(Resource.NETWORKS, "test-network")
    subprocess.run("lxc network create test-network", shell=True)
    assert client.exists(Resource.NETWORKS, "test-network")

    assert capsys.readouterr().out == EXISTS_NETWORK_OUTPUT


EXISTS_PROFILE_OUTPUT = """
checking profiles/test-profile
checking profiles/test-profile
""".lstrip()


def test_exists_profile(client, capsys):
    assert not client.exists(Resource.PROFILES, "test-profile")
    subprocess.run("lxc profile create test-profile", shell=True)
    assert client.exists(Resource.PROFILES, "test-profile")

    assert capsys.readouterr().out == EXISTS_PROFILE_OUTPUT


EXISTS_INSTANCE_OUTPUT = """
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_exists_instance(client, capsys):
    assert not client.exists(Resource.INSTANCES, "test-instance")
    subprocess.run("lxc launch test-instance --empty", shell=True)
    assert client.exists(Resource.INSTANCES, "test-instance")

    assert capsys.readouterr().out == EXISTS_INSTANCE_OUTPUT


CREATE_STORAGE_POOL_OUTPUT = """
checking storage-pools/test-storage-pool
creating storage-pools/{"name": "test-storage-pool", "driver": "dir"}
checking storage-pools/test-storage-pool
checking storage-pools/test-storage-pool
""".lstrip()


def test_create_storage_pool(client, capsys):
    client.create(Resource.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    assert client.exists(Resource.STORAGE_POOLS, "test-storage-pool")
    client.create(Resource.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})  # idempotent

    assert capsys.readouterr().out == CREATE_STORAGE_POOL_OUTPUT


CREATE_NETWORK_OUTPUT = """
checking networks/test-network
creating networks/{"name": "test-network"}
checking networks/test-network
checking networks/test-network
""".lstrip()


def test_create_network(client, capsys):
    client.create(Resource.NETWORKS, {"name": "test-network"})
    assert client.exists(Resource.NETWORKS, "test-network")
    client.create(Resource.NETWORKS, {"name": "test-network"})  # idempotent

    assert capsys.readouterr().out == CREATE_NETWORK_OUTPUT


CREATE_PROFILE_OUTPUT = """
checking profiles/test-profile
creating profiles/{"name": "test-profile"}
checking profiles/test-profile
checking profiles/test-profile
""".lstrip()


def test_create_profile(client, capsys):
    client.create(Resource.PROFILES, {"name": "test-profile"})
    assert client.exists(Resource.PROFILES, "test-profile")
    client.create(Resource.PROFILES, {"name": "test-profile"})  # idempotent

    assert capsys.readouterr().out == CREATE_PROFILE_OUTPUT


CREATE_INSTANCE_OUTPUT = """
checking instances/test-instance
creating instances/{"name": "test-instance", "source": {"type": "none"}}
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_create_instance(client, capsys):
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    assert client.exists(Resource.INSTANCES, "test-instance")
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})  # idempotent

    assert capsys.readouterr().out == CREATE_INSTANCE_OUTPUT


DELETE_STORAGE_POOL_OUTPUT = """
checking storage-pools/test-storage-pool
creating storage-pools/{"name": "test-storage-pool", "driver": "dir"}
checking storage-pools/test-storage-pool
deleting storage-pools/test-storage-pool
checking storage-pools/test-storage-pool
checking storage-pools/test-storage-pool
""".lstrip()


def test_delete_storage_pool(client, capsys):
    client.create(Resource.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})  # given

    client.delete(Resource.STORAGE_POOLS, "test-storage-pool")
    assert not client.exists(Resource.STORAGE_POOLS, "test-storage-pool")
    client.delete(Resource.STORAGE_POOLS, "test-storage-pool")  # idempotent

    assert capsys.readouterr().out == DELETE_STORAGE_POOL_OUTPUT


DELETE_NETWORK_OUTPUT = """
checking networks/test-network
creating networks/{"name": "test-network"}
checking networks/test-network
deleting networks/test-network
checking networks/test-network
checking networks/test-network
""".lstrip()


def test_delete_network(client, capsys):
    client.create(Resource.NETWORKS, {"name": "test-network"})  # given

    client.delete(Resource.NETWORKS, "test-network")
    assert not client.exists(Resource.NETWORKS, "test-network")
    client.delete(Resource.NETWORKS, "test-network")  # idempotent

    assert capsys.readouterr().out == DELETE_NETWORK_OUTPUT


DELETE_PROFILE_OUTPUT = """
checking profiles/test-profile
creating profiles/{"name": "test-profile"}
checking profiles/test-profile
deleting profiles/test-profile
checking profiles/test-profile
checking profiles/test-profile
""".lstrip()


def test_delete_profile(client, capsys):
    client.create(Resource.PROFILES, {"name": "test-profile"})  # given

    client.delete(Resource.PROFILES, "test-profile")
    assert not client.exists(Resource.PROFILES, "test-profile")
    client.delete(Resource.PROFILES, "test-profile")  # idempotent

    assert capsys.readouterr().out == DELETE_PROFILE_OUTPUT


DELETE_INSTANCE_OUTPUT = """
checking instances/test-instance
creating instances/{"name": "test-instance", "source": {"type": "none"}}
checking instances/test-instance
deleting instances/test-instance
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_delete_instance(client, capsys):
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})  # given

    client.delete(Resource.INSTANCES, "test-instance")
    assert not client.exists(Resource.INSTANCES, "test-instance")
    client.delete(Resource.INSTANCES, "test-instance")  # idempotent

    assert capsys.readouterr().out == DELETE_INSTANCE_OUTPUT


IS_RUNNING_OUTPUT = """
checking instances/test-instance
creating instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_is_running(client, capsys):
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})  # given

    assert not client.is_running("test-instance")
    subprocess.run("lxc start test-instance", shell=True)
    time.sleep(0.2)
    assert client.is_running("test-instance")

    assert capsys.readouterr().out == IS_RUNNING_OUTPUT


START_OUTPUT = """
checking instances/test-instance
creating instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking instances/test-instance
starting instances/test-instance
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_start(client, capsys):
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})  # given

    client.start("test-instance")
    time.sleep(0.2)
    assert client.is_running("test-instance")
    client.start("test-instance")  # idempotent

    assert capsys.readouterr().out == START_OUTPUT


STOP_OUTPUT = """
checking instances/test-instance
creating instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking instances/test-instance
starting instances/test-instance
checking instances/test-instance
stopping instances/test-instance
checking instances/test-instance
checking instances/test-instance
""".lstrip()


def test_stop(client, capsys):
    # given
    client.create(Resource.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    client.start("test-instance")
    time.sleep(0.2)

    client.stop("test-instance")
    assert not client.is_running("test-instance")
    client.stop("test-instance")  # idempotent

    assert capsys.readouterr().out == STOP_OUTPUT


def test_ko_create(client):
    with pytest.raises(Exception) as exception:
        client.create(Resource.STORAGE_POOLS, {"name": "test-storage-pool"})

    assert '{"error":"No driver provided","error_code":400,"type":"error"}' in str(exception.value)
