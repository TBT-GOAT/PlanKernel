###############
#
# Environment Setup for PlanKernel
#
###############

##### Python #####
# Setting Python base image version to 3.11
FROM python:3.11-slim

##### Setup #####
RUN apt update

# Package management system
RUN apt install -y \
    apt-file \
    iproute2 \
    wget

# C++ libraries
RUN apt install -y \
    build-essential \
    gdb \
    heaptrack \
    heaptrack-gui \
    libboost-dev \
    libgmp3-dev \
    libmpfr-dev \
    libcgal-dev \
    libgl1 \
    libglib2.0-0 \
    nlohmann-json3-dev

# cmake
RUN apt install -y \
    cmake

# Python
RUN apt install -y \
    python3-tk \
    python3-dev \
    python3-pip \
    python3-venv 

# Remove unnecessary cache to reduce image size
RUN apt clean \
    && rm -rf /var/lib/apt/lists/*


##### Python environment setup #####

### Virtual environment setup ###
ARG virtual_env_name=plan_kernel
ARG virtual_env_path=/venv/${virtual_env_name}
# Create virtual environment and set path
RUN python3 -m venv ${virtual_env_path}
ENV PATH="${virtual_env_path}/bin:$PATH"

### Install libraries ###
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip \
    && pip3 install -r /tmp/requirements.txt \
    && rm -fr /tmp/requirements.txt


##### Command to run when container starts #####
CMD ["/bin/bash"]