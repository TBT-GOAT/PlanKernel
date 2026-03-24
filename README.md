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

## Medial Axis Transform

### Overview

This program computes the **Medial Axis Transform (MAT)** from input `.cin` files and outputs the resulting network data. It supports configurable parameters via a JSON file and parallel processing using OpenMP.

---

### Features

* Load configurations from `configurations.json`
* Automatic scanning of input files if config is missing
* Interactive configuration editing
* Parallel processing with OpenMP
* Outputs:

  * Medial axis network
  * Vertex coordinates

---

### Directory Structure

```
<data_folder>/
├── input/            # Input .cin files
├── ma/               # Output medial axis results
├── embedding/        # (Reserved)
└── configurations.json
```

---

### Usage

#### 1. Run the Program

```
/your/path/to/main
```

#### 2. Input Data Folder Path

You will be prompted:

```
Enter the data folder path:
```

Example:

```
./data
```

---

### Configuration

#### Configuration File

If `configurations.json` exists, it will be loaded automatically.

Otherwise, default values are used and the file will be generated.

#### Configurable Parameters

| Parameter                   | Description                        |
| --------------------------- | ---------------------------------- |
| EPSILON_GRID                | Coordinate tolerance               |
| MIN_PASSENGER_WIDTH         | Minimum width threshold            |
| NODE_NUM_DESC               | Node selection (descending radius) |
| TOLERANCE                   | Radius change threshold            |
| EROSION_THICKNESS_THRESHOLD | Grassfire transform parameter      |
| SPLIT_LENGTH                | Sampling interval for output       |
| Number of threads           | OpenMP thread count                |

---

#### Interactive Editing

After loading, you can modify parameters:

```
===== Configurations =====
1. EPSILON_GRID: ...
2. MIN_PASSENGER_WIDTH: ...
...
Enter number to change (0 to continue):
```

---

### Input Files

* Format: `.cin`

* Location:

  ```
  <data_folder>/input/
  ```

* `.cin` files in the folder are used.

---

### Output

For each input file:

```
<data_folder>/ma/ma_<filename>/
```

#### Generated Files

* Network data
* `coordination.nk`

  ```
  x,y
  x,y
  ...
  ```
* `clearance.nk`

  ```
  r
  r
  ...
  ```
* `adjacency.nk`

  ```
  node_ID adjacent_node_ID adjacent_node_ID...
  node_ID adjacent_node_ID adjacent_node_ID...
  ...
  ```

---

### Parallel Processing

* Uses OpenMP
* Default thread count:

  ```
  omp_get_max_threads()
  ```
* Can be adjusted during configuration

---

### Progress Display

Real-time progress is shown:

```
Progress: 3 / 10
```

---

### Dependencies

* C++17 or later
* OpenMP
* `nlohmann::json`
* `<filesystem>`

---

### Notes

* Existing output folders are skipped (already processed cases)
* Output directories are automatically created
* High-precision floating-point output is used for vertex coordinates

---