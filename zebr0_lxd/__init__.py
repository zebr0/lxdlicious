import enum
import json
from pathlib import Path
from typing import Optional, List

import requests_unixsocket
import yaml
import zebr0

KEY_DEFAULT = "lxd-stack"
URL_DEFAULT = "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"


class Command(str, enum.Enum):
    CREATE = "create",
    START = "start",
    STOP = "stop",
    DELETE = "delete"


class Resource(str, enum.Enum):
    STORAGE_POOLS = "storage-pools",
    NETWORKS = "networks",
    PROFILES = "profiles",
    INSTANCES = "instances"

    def path(self):
        return "/1.0/" + self


class Client:
    def __init__(self, url: str = URL_DEFAULT):
        self.url = url

        # this "hook" will be executed after each request
        # see http://docs.python-requests.org/en/master/user/advanced/#event-hooks
        def hook(response, **_):
            if not response.ok:
                raise Exception(response.text)

            # this will wait for lxd asynchronous operations to be finished
            # see https://github.com/lxc/lxd/blob/master/doc/rest-api.md#background-operation
            if response.json().get("type") == "async":
                self.session.get(self.url + response.json().get("operation") + "/wait")

        self.session = requests_unixsocket.Session()
        self.session.hooks["response"].append(hook)

    def exists(self, resource, name):
        print(f"checking {resource}/{name}")
        return any(filter(
            lambda a: a == resource.path() + "/" + name,
            self.session.get(self.url + resource.path()).json().get("metadata")
        ))

    def create(self, resource, config):
        if not self.exists(resource, config.get("name")):
            print(f"creating {resource}/{json.dumps(config)}")
            self.session.post(self.url + resource.path(), json=config)

    def delete(self, resource, name):
        if self.exists(resource, name):
            print(f"deleting {resource}/{name}")
            self.session.delete(self.url + resource.path() + "/" + name)

    def is_running(self, name):
        print(f"checking {Resource.INSTANCES}/{name}")
        return self.session.get(self.url + Resource.INSTANCES.path() + "/" + name).json().get("metadata").get("status") == "Running"

    def start(self, name):
        if not self.is_running(name):
            print(f"starting {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "start"})

    def stop(self, name):
        if self.is_running(name):
            print(f"stopping {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "stop"})


def do(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, command: Command, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    value = zebr0.Client(url, levels, cache, configuration_file).get(key)
    if not value:
        print(f"key '{key}' not found on server {url}")
        exit(1)

    stack = yaml.load(value, Loader=yaml.BaseLoader)
    if not isinstance(stack, dict):
        print(f"key '{key}' on server {url} is not a proper yaml or json dictionary")
        exit(1)

    client = Client(lxd_url)

    if command == Command.CREATE:
        for resource in list(Resource):
            for config in stack.get(resource) or []:
                client.create(resource, config)
    elif command == Command.START:
        for config in stack.get(Resource.INSTANCES) or []:
            client.start(config.get("name"))
    elif command == Command.STOP:
        for config in stack.get(Resource.INSTANCES) or []:
            client.stop(config.get("name"))
    elif command == Command.DELETE:
        for resource in reversed(Resource):
            for config in stack.get(resource) or []:
                client.delete(resource, config.get("name"))


def main(args: Optional[List[str]] = None) -> None:
    argparser = zebr0.build_argument_parser(description="zebr0 client to deploy an application to a local LXD environment")
    argparser.add_argument("command", choices=list(Command))
    argparser.add_argument("key", nargs="?", default="lxd-stack", help="the stack's key, defaults to 'lxd-stack'")
    argparser.add_argument("--lxd-url", default=URL_DEFAULT, help="")
    args = argparser.parse_args(args)

    do(args.url, args.levels, args.cache, args.configuration_file, args.command, args.key, args.lxd_url)
