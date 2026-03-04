# PlanKernel
## Environment Setting
### Setting Using Docker
First, run the commands below to build a docker container.
```
cd /your/project/directory/path
cd ./docker
sh build_image.sh
sh run_container.sh
```
Then, attach the container on VS Code.  
### Setting on Local Environment
Run the following commands in order.
```
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

sudo apt update

sudo apt install -y \
    apt-file \
    iproute2 \
    wget \
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
    nlohmann-json3-dev \
    cmake \
    python3-tk \
    python3-dev \
    python3-pip \
    python3-venv

mkdir -p ~/venv
python3.11 -m venv ~/venv/plan_kernel

source ~/venv/plan_kernel/bin/activate

cd /your/project/directory/path
cd ./docker
pip install --upgrade pip
pip install -r requirements.txt
```
