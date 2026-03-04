#!/bin/bash

docker run \
    -itd \
    -v /your/project/directory:/home/workspace \
    --detach-keys="ctrl-x"\
    --name plan_kernel\
    plan_kernel:latest