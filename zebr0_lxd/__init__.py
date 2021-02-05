import argparse
import enum
import json
from typing import Optional, List

import requests_unixsocket
import yaml
import zebr0

KEY_DEFAULT = "lxd-stack"
URL_DEFAULT = "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"


class Resource(str, enum.Enum):
    """
    Enumerates the various LXD resource types managed by the library.
    """

    STORAGE_POOLS = "storage-pools",
    NETWORKS = "networks",
    PROFILES = "profiles",
    INSTANCES = "instances"

    def path(self) -> str:
        """
        :return: the corresponding path relative to the LXD API base URL
        """
        return "/1.0/" + self


class Client:
    """
    A simple wrapper around the LXD REST API to manage resources either directly or via "stacks".

    This Client connects to the LXD API through the Unix socket (for now).
    Apart from how asynchronous operations are handled, it's mainly a convenient, idempotent passthrough.
    Therefore, the official documentation is where you'll find all the configuration details you'll need to create LXD resources:

    * storage-pools: https://linuxcontainers.org/lxd/docs/master/rest-api#10storage-pools and https://linuxcontainers.org/lxd/docs/master/storage
    * networks: https://linuxcontainers.org/lxd/docs/master/rest-api#10networks and https://linuxcontainers.org/lxd/docs/master/networks
    * profiles: https://linuxcontainers.org/lxd/docs/master/rest-api#10profiles and https://linuxcontainers.org/lxd/docs/master/profiles
    * instances: https://linuxcontainers.org/lxd/docs/master/rest-api#10instances and https://linuxcontainers.org/lxd/docs/master/instances

    A "stack" is very a convenient way to manage a group of resources linked together.
    Heavily inspired by the LXD "preseed" format (see https://linuxcontainers.org/lxd/docs/master/preseed), the structure is almost identical, except:

    * "storage_pools" has been renamed "storage-pools" to match the API
    * the root "config" element is ignored (use a real preseed file if you want to configure LXD that way)
    * instances are managed through a new root element, "instances"

    A typical stack example can be found in tests/test_cli.py.
    Check the various functions to see what you can do with stacks and resources.

    :param url: URL of the LXD API (scheme is "http+unix", socket path is percent-encoded into the host field), defaults to "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"
    """

    def __init__(self, url: str = URL_DEFAULT):
        self.url = url

        # this "hook" will be executed after each request (see http://docs.python-requests.org/en/master/user/advanced/#event-hooks)
        def hook(response, **_):
            if not response.ok:
                raise Exception(response.text)

            # some lxd operations are asynchronous (see https://linuxcontainers.org/lxd/docs/master/rest-api#async-operations)
            # this can be problematic so we have to wait for them to finish before continuing (see https://linuxcontainers.org/lxd/docs/master/rest-api#10operationsuuidwait)
            if response.json().get("type") == "async":
                self.session.get(self.url + response.json().get("operation") + "/wait")

        self.session = requests_unixsocket.Session()
        self.session.hooks["response"].append(hook)

    def exists(self, resource: Resource, name: str) -> bool:
        """
        :param resource: the resource's type
        :param name: the resource's name
        :return: whether the resource exists or not
        """

        print(f"checking {resource}/{name}")
        return any(filter(
            lambda a: a == resource.path() + "/" + name,
            self.session.get(self.url + resource.path()).json().get("metadata")  # returns a list of existing resources
        ))

    def create(self, resource: Resource, config: dict) -> None:
        """
        Creates a resource if it doesn't exist (based on its name).
        The required configuration depends on the resource's type (see zebr0_lxd.Client).

        :param resource: the resource's type
        :param config: the resource's desired configuration
        """

        if not self.exists(resource, config.get("name")):
            print(f"creating {resource}/{json.dumps(config)}")
            self.session.post(self.url + resource.path(), json=config)

    def delete(self, resource: Resource, name: str) -> None:
        """
        Deletes a resource if it exists (based on its name).

        :param resource: the resource's type
        :param name: the resource's name
        """

        if self.exists(resource, name):
            print(f"deleting {resource}/{name}")
            self.session.delete(self.url + resource.path() + "/" + name)

    def is_running(self, name: str) -> bool:
        """
        :param name: the instance's name
        :return: whether the instance is running or not
        """

        print(f"checking {Resource.INSTANCES}/{name}")
        return self.session.get(self.url + Resource.INSTANCES.path() + "/" + name).json().get("metadata").get("status") == "Running"

    def start(self, name: str) -> None:
        """
        Starts an instance if it's not running (based on its name).

        :param name: the instance's name
        """

        if not self.is_running(name):
            print(f"starting {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "start"})

    def stop(self, name: str) -> None:
        """
        Stops an instance if it's running (based on its name).

        :param name: the instance's name
        """

        if self.is_running(name):
            print(f"stopping {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "stop"})

    def create_stack(self, stack: dict) -> None:
        """
        Creates the resources in the given stack if they don't exist (based on their name).
        The required configurations depend on the resource's type (see zebr0_lxd.Client).

        :param stack: the stack as a dictionary
        """

        for resource in list(Resource):  # order: storage pools, networks, profiles, instances
            for config in stack.get(resource) or []:
                self.create(resource, config)

    def delete_stack(self, stack: dict) -> None:
        """
        Deletes the resources in the given stack if they exist (based on their name).

        :param stack: the stack as a dictionary
        """

        for resource in reversed(Resource):  # order: instances, profiles, networks, storage pools
            for config in stack.get(resource) or []:
                self.delete(resource, config.get("name"))

    def start_stack(self, stack: dict) -> None:
        """
        Starts the instances in the given stack if they're not running (based on their name).

        :param stack: the stack as a dictionary
        """

        for config in stack.get(Resource.INSTANCES) or []:
            self.start(config.get("name"))

    def stop_stack(self, stack: dict) -> None:
        """
        Stops the instances in the given stack if they're running (based on their name).

        :param stack: the stack as a dictionary
        """

        for config in stack.get(Resource.INSTANCES) or []:
            self.stop(config.get("name"))


def main(args: Optional[List[str]] = None) -> None:
    """
    usage: zebr0-lxd [-h] [-u <url>] [-l [<level> [<level> ...]]] [-c <duration>] [-f <path>] [--lxd-url <url>] {create,delete,start,stop} [key]

    LXD provisioning based on zebr0 key-value system.
    Fetches a stack from the key-value server and manages it on LXD.

    positional arguments:
      {create,delete,start,stop}
                            operation to execute on the stack
      key                   the stack's key, defaults to 'lxd-stack'

    optional arguments:
      -h, --help            show this help message and exit
      -u <url>, --url <url>
                            URL of the key-value server, defaults to https://hub.zebr0.io
      -l [<level> [<level> ...]], --levels [<level> [<level> ...]]
                            levels of specialization (e.g. "mattermost production" for a <project>/<environment>/<key> structure), defaults to ""
      -c <duration>, --cache <duration>
                            in seconds, the duration of the cache of http responses, defaults to 300 seconds
      -f <path>, --configuration-file <path>
                            path to the configuration file, defaults to /etc/zebr0.conf for a system-wide configuration
      --lxd-url <url>       URL of the LXD API (scheme is "http+unix", socket path is percent-encoded into the host field), defaults to "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"
    """

    argparser = zebr0.build_argument_parser(description="LXD provisioning based on zebr0 key-value system.\nFetches a stack from the key-value server and manages it on LXD.", formatter_class=argparse.RawDescriptionHelpFormatter)
    argparser.add_argument("command", choices=["create", "delete", "start", "stop"], help="operation to execute on the stack")
    argparser.add_argument("key", nargs="?", default="lxd-stack", help="the stack's key, defaults to 'lxd-stack'")
    argparser.add_argument("--lxd-url", default=URL_DEFAULT, help='URL of the LXD API (scheme is "http+unix", socket path is percent-encoded into the host field), defaults to "http+unix://%%2Fvar%%2Fsnap%%2Flxd%%2Fcommon%%2Flxd%%2Funix.socket"', metavar="<url>")
    args = argparser.parse_args(args)

    value = zebr0.Client(args.url, args.levels, args.cache, args.configuration_file).get(args.key)
    if not value:
        print(f"key '{args.key}' not found on server {args.url}")
        exit(1)

    stack = yaml.load(value, Loader=yaml.BaseLoader)
    if not isinstance(stack, dict):
        print(f"key '{args.key}' on server {args.url} is not a proper yaml or json dictionary")
        exit(1)

    getattr(Client(args.lxd_url), args.command + "_stack")(stack)
