#!/bin/sh -ex

# cleans a potentially failed previous test run
[ -d tmp/ ] && rm -rf tmp/

# creates tmp directory
mkdir tmp

# test creating a stack
../src/lxd-compose create
lxc network show test0 > tmp/network
diff results/network tmp/network
lxc profile show test > tmp/profile
diff results/profile tmp/profile
lxc info dummy-test-master | grep -v Created > tmp/container-create
diff results/container-stopped tmp/container-create

# test starting a stack
../src/lxd-compose start
lxc info dummy-test-master | grep -v Created | head -n6 > tmp/container-start
diff results/container-started tmp/container-start

# test stopping a stack
../src/lxd-compose stop
lxc info dummy-test-master | grep -v Created > tmp/container-stop
diff results/container-stopped tmp/container-stop

# test deleting the stack
../src/lxd-compose delete

# cleans tmp directory
rm -rf tmp
