#!/bin/sh -ex

# cleans a potentially failed previous test run
[ -f tmp/pid ] && kill $(cat tmp/pid)
[ -d tmp/ ] && rm -rf tmp/

# creates tmp directory
mkdir tmp

# starts the mock server
cd mock
python3 -m http.server &
echo $! > ../tmp/pid
sleep 1
cd ..

# test creating a stack
../src/lxd-compose create test master
lxc network show test0 > tmp/network
diff results/network tmp/network
lxc profile show test > tmp/profile
diff results/profile tmp/profile
lxc info dummy-test-master | grep -v Created > tmp/container-create
diff results/container-stopped tmp/container-create

# test starting a stack
../src/lxd-compose start test master
lxc info dummy-test-master | grep -v Created | head -n6 > tmp/container-start
diff results/container-started tmp/container-start

# test stopping a stack
../src/lxd-compose stop test master
lxc info dummy-test-master | grep -v Created > tmp/container-stop
diff results/container-stopped tmp/container-stop

# test deleting the stack
../src/lxd-compose delete test master

# stops the mock server
kill $(cat tmp/pid) && rm tmp/pid

# cleans tmp directory
rm -rf tmp
