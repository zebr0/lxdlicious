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
        subprocess.Popen("lxc delete test-container", shell=True).wait()

    clean()
    yield  # see https://stackoverflow.com/questions/22627659/run-code-before-and-after-each-test-in-py-test
    clean()


def test_exists_storage_pool(client):
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    subprocess.Popen("lxc storage create test-storage-pool dir", shell=True).wait()
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_exists_network(client):
    assert not client.exists(Collection.NETWORKS, "test-network")
    subprocess.Popen("lxc network create test-network", shell=True).wait()
    assert client.exists(Collection.NETWORKS, "test-network")


def test_exists_profile(client):
    assert not client.exists(Collection.PROFILES, "test-profile")
    subprocess.Popen("lxc profile create test-profile", shell=True).wait()
    assert client.exists(Collection.PROFILES, "test-profile")


def test_exists_container(client):
    assert not client.exists(Collection.CONTAINERS, "test-container")
    subprocess.Popen("lxc launch test-container --empty", shell=True).wait()
    assert client.exists(Collection.CONTAINERS, "test-container")


def test_create_error(client):
    with pytest.raises(Exception) as exception:
        client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool"})
    assert '{"error":"No driver provided","error_code":400,"type":"error"}' in str(exception.value)


def test_create(client):
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_delete(client):
    subprocess.Popen("lxc storage create test-storage-pool dir", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    client.delete(Collection.STORAGE_POOLS, "test-storage-pool")
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_is_running(client):
    subprocess.Popen("lxc launch ubuntu:focal test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert client.is_running("test")
    subprocess.Popen("lxc stop test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")


def test_start(client):
    client.create(Collection.CONTAINERS, {"name": "test", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/daily", "protocol": "simplestreams", "alias": "bionic"}})
    assert not client.is_running("test")
    client.start("test")
    time.sleep(1)
    assert client.is_running("test")
    subprocess.Popen("lxc stop test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")


def test_stop(client):
    subprocess.Popen("lxc launch ubuntu:focal test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert client.is_running("test")
    client.stop("test")
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")
