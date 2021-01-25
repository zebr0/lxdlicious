import subprocess
import time

import pytest

import zebr0_lxd
from zebr0_lxd import Collection


@pytest.fixture(scope="module")
def client():
    return zebr0_lxd.Client()


@pytest.fixture(autouse=True)
def clean_before_after():
    def clean():
        subprocess.Popen("lxc storage delete test-storage-pool", shell=True).wait()
        subprocess.Popen("lxc network delete test-network", shell=True).wait()
        subprocess.Popen("lxc profile delete test-profile", shell=True).wait()
        subprocess.Popen("lxc stop test-instance", shell=True).wait()
        subprocess.Popen("lxc delete test-instance", shell=True).wait()

    clean()
    yield  # see https://stackoverflow.com/questions/22627659/run-code-before-and-after-each-test-in-py-test
    clean()


EXISTS_STORAGE_POOL = """
checking /1.0/storage-pools/test-storage-pool
checking /1.0/storage-pools/test-storage-pool
""".lstrip()


def test_exists_storage_pool(client, capsys):
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    subprocess.Popen("lxc storage create test-storage-pool dir", shell=True).wait()
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    assert capsys.readouterr().out == EXISTS_STORAGE_POOL


EXISTS_NETWORK = """
checking /1.0/networks/test-network
checking /1.0/networks/test-network
""".lstrip()


def test_exists_network(client, capsys):
    assert not client.exists(Collection.NETWORKS, "test-network")
    subprocess.Popen("lxc network create test-network", shell=True).wait()
    assert client.exists(Collection.NETWORKS, "test-network")
    assert capsys.readouterr().out == EXISTS_NETWORK


EXISTS_PROFILE = """
checking /1.0/profiles/test-profile
checking /1.0/profiles/test-profile
""".lstrip()


def test_exists_profile(client, capsys):
    assert not client.exists(Collection.PROFILES, "test-profile")
    subprocess.Popen("lxc profile create test-profile", shell=True).wait()
    assert client.exists(Collection.PROFILES, "test-profile")
    assert capsys.readouterr().out == EXISTS_PROFILE


EXISTS_INSTANCE = """
checking /1.0/instances/test-instance
checking /1.0/instances/test-instance
""".lstrip()


def test_exists_instance(client, capsys):
    assert not client.exists(Collection.INSTANCES, "test-instance")
    subprocess.Popen("lxc launch test-instance --empty", shell=True).wait()
    assert client.exists(Collection.INSTANCES, "test-instance")
    assert capsys.readouterr().out == EXISTS_INSTANCE


def test_create_error(client):
    with pytest.raises(Exception) as exception:
        client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool"})
    assert '{"error":"No driver provided","error_code":400,"type":"error"}' in str(exception.value)


CREATE_STORAGE_POOL = """
checking /1.0/storage-pools/test-storage-pool
creating /1.0/storage-pools/{"name": "test-storage-pool", "driver": "dir"}
checking /1.0/storage-pools/test-storage-pool
checking /1.0/storage-pools/test-storage-pool
""".lstrip()


def test_create_storage_pool(client, capsys):
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    assert capsys.readouterr().out == CREATE_STORAGE_POOL


CREATE_NETWORK = """
checking /1.0/networks/test-network
creating /1.0/networks/{"name": "test-network"}
checking /1.0/networks/test-network
checking /1.0/networks/test-network
""".lstrip()


def test_create_network(client, capsys):
    client.create(Collection.NETWORKS, {"name": "test-network"})
    assert client.exists(Collection.NETWORKS, "test-network")
    client.create(Collection.NETWORKS, {"name": "test-network"})
    assert capsys.readouterr().out == CREATE_NETWORK


CREATE_PROFILE = """
checking /1.0/profiles/test-profile
creating /1.0/profiles/{"name": "test-profile"}
checking /1.0/profiles/test-profile
checking /1.0/profiles/test-profile
""".lstrip()


def test_create_profile(client, capsys):
    client.create(Collection.PROFILES, {"name": "test-profile"})
    assert client.exists(Collection.PROFILES, "test-profile")
    client.create(Collection.PROFILES, {"name": "test-profile"})
    assert capsys.readouterr().out == CREATE_PROFILE


CREATE_INSTANCE = """
checking /1.0/instances/test-instance
creating /1.0/instances/{"name": "test-instance", "source": {"type": "none"}}
checking /1.0/instances/test-instance
checking /1.0/instances/test-instance
""".lstrip()


def test_create_instance(client, capsys):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    assert client.exists(Collection.INSTANCES, "test-instance")
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    assert capsys.readouterr().out == CREATE_INSTANCE


DELETE_STORAGE_POOL = """
checking /1.0/storage-pools/test-storage-pool
creating /1.0/storage-pools/{"name": "test-storage-pool", "driver": "dir"}
checking /1.0/storage-pools/test-storage-pool
deleting /1.0/storage-pools/test-storage-pool
checking /1.0/storage-pools/test-storage-pool
checking /1.0/storage-pools/test-storage-pool
""".lstrip()


def test_delete_storage_pool(client, capsys):
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    client.delete(Collection.STORAGE_POOLS, "test-storage-pool")
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    client.delete(Collection.STORAGE_POOLS, "test-storage-pool")
    assert capsys.readouterr().out == DELETE_STORAGE_POOL


DELETE_NETWORK = """
checking /1.0/networks/test-network
creating /1.0/networks/{"name": "test-network"}
checking /1.0/networks/test-network
deleting /1.0/networks/test-network
checking /1.0/networks/test-network
checking /1.0/networks/test-network
""".lstrip()


def test_delete_network(client, capsys):
    client.create(Collection.NETWORKS, {"name": "test-network"})
    client.delete(Collection.NETWORKS, "test-network")
    assert not client.exists(Collection.NETWORKS, "test-network")
    client.delete(Collection.NETWORKS, "test-network")
    assert capsys.readouterr().out == DELETE_NETWORK


DELETE_PROFILE = """
checking /1.0/profiles/test-profile
creating /1.0/profiles/{"name": "test-profile"}
checking /1.0/profiles/test-profile
deleting /1.0/profiles/test-profile
checking /1.0/profiles/test-profile
checking /1.0/profiles/test-profile
""".lstrip()


def test_delete_profile(client, capsys):
    client.create(Collection.PROFILES, {"name": "test-profile"})
    client.delete(Collection.PROFILES, "test-profile")
    assert not client.exists(Collection.PROFILES, "test-profile")
    client.delete(Collection.PROFILES, "test-profile")
    assert capsys.readouterr().out == DELETE_PROFILE


DELETE_INSTANCE = """
checking /1.0/instances/test-instance
creating /1.0/instances/{"name": "test-instance", "source": {"type": "none"}}
checking /1.0/instances/test-instance
deleting /1.0/instances/test-instance
checking /1.0/instances/test-instance
checking /1.0/instances/test-instance
""".lstrip()


def test_delete_instance(client, capsys):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    client.delete(Collection.INSTANCES, "test-instance")
    assert not client.exists(Collection.INSTANCES, "test-instance")
    client.delete(Collection.INSTANCES, "test-instance")
    assert capsys.readouterr().out == DELETE_INSTANCE


IS_RUNNING = """
checking /1.0/instances/test-instance
creating /1.0/instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking status /1.0/instances/test-instance
checking status /1.0/instances/test-instance
""".lstrip()


def test_is_running(client, capsys):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    assert not client.is_running("test-instance")
    subprocess.Popen("lxc start test-instance", shell=True).wait()
    assert client.is_running("test-instance")
    assert capsys.readouterr().out == IS_RUNNING


START = """
checking /1.0/instances/test-instance
creating /1.0/instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking status /1.0/instances/test-instance
starting /1.0/instances/test-instance
checking status /1.0/instances/test-instance
checking status /1.0/instances/test-instance
""".lstrip()


def test_start(client, capsys):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    client.start("test-instance")
    assert client.is_running("test-instance")
    client.start("test-instance")
    assert capsys.readouterr().out == START


STOP = """
checking /1.0/instances/test-instance
creating /1.0/instances/{"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}}
checking status /1.0/instances/test-instance
starting /1.0/instances/test-instance
checking status /1.0/instances/test-instance
stopping /1.0/instances/test-instance
checking status /1.0/instances/test-instance
checking status /1.0/instances/test-instance
""".lstrip()


def test_stop(client, capsys):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    client.start("test-instance")
    time.sleep(0.1)
    client.stop("test-instance")
    assert not client.is_running("test-instance")
    client.stop("test-instance")
    assert capsys.readouterr().out == STOP
