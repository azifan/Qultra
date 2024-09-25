<p align="center">
  <img src="Images/logo.png" alt="drawing" width="700"/>
</p>

#

QuantUS is a free, standalone, native graphical user interface (GUI) facilitating ultrasound research compatible on Mac OS X, Windows, and Linux. The tool provides an end-to-end workflow for analysis using radiomics approaches including:
* 2D Ultrasound Tissue Characterization (UTC) via spectral analysis of radiofrequency (RF) and in-phase and quadrature (IQ) data
* 2D Contrast-Enhanced Ultrasound (CEUS) Time Intensity Curve (TIC) Analysis with optional Motion Compensation
* 3D CEUS TIC Analysis

Notably, QuantUS addresses shortcomings in existing state-of-the-art tools by supporting 3D parametric map generation, motion compensation for 2D CEUS TIC analysis, an ultrasound system-independent approach, and an intuitive user interface. For more information, see our [website](https://quantus.webflow.io).

![3D CEUS Parametric Map Example](Images/3dCeusParamap.png)

## Requirements

* [Docker](docker.com/products/docker-desktop/) (only required for Philips RF parser, which is not currently supported)
* [Python](https://www.python.org/downloads/)
* [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

## Environment

### Conda (preferred)

Once you have Conda installed on your machine (Miniconda and Anaconda Distribution each suffice), use `env.yml` to create a conda-enabled virtual environment. This can be completed using the following commands:

```shell
git clone https://github.com/TUL-Dev/QuantUS.git
cd QuantUS
conda env create -f env.yml
```

From here, this environment can be activated using the `conda activate QuantUS-env` command.

### VirtualEnv (deprecated)

Deprecated but continued for historic purposes, this environment uses `pip` and the `virtualenv` Python library to create a Pip-enabled virtual environment. This can be completed using the following commands:

```shell
git clone https://github.com/TUL-Dev/QuantUS.git
cd QuantUS
pip install --upgrade pip
python -m pip install virtualenv
virtualenv --python="python3.9" venv
source venv/bin/activate # Unix
call venv\bin\activate.bat # Windows
pip install -r requirements.txt
```

Following this example, this environment can be accessed via the `source venv/bin/activate` command from the repository directory.

#### Troubleshooting for Mac

To run these commands, make sure you have [HomeBrew](https://brew.sh/) installed.

If you encounter an error after running `pip install -r requirements.txt`, try the following code and then run the command again:

```shell
brew install qt5

brew link qt5 --force

pip install wheel setuptools pip --upgrade

pip install pyqt5==5.15.9 --config-settings --confirm-license= --verbose
```

If an error persists after running `python main.py`, try `export QT_QPA_PLATFORM_PLUGIN_PATH=/opt/homebrew/Cellar/qt@5/5.15.13_1/plugins`.

## Building

After configuring a Python virtual environment, finish preparing QuantUS to be run using the following commands:

```shell
# Using Python virtual env
chmod +x saveQt.sh # Mac
./saveQt.sh # Mac
ren saveQt.sh saveQt.bat # Windows
.\saveQt.bat # Windows
```

### Extra step for Windows

To finish preparing QuantUS to be run, to support the Philips RF parser, compile `Parsers\philips_rf_parser.c` into a `Parsers\philips_rf_parser` executable using Windows C compiler of choice.

## Running

### Mac/Linux

```shell
source venv/bin/activate
python main.py
deactivate
```

### Windows

```shell
call venv\scripts\activate.bat
python main.py
deactivate
```

## Phantom Collection Google Folder

This folder contains minimal sample data required to get each feature of
QuantUS working. Note that since phantom data must be collected using
identical transducer settings as the images they're compared to, we
do not recommend using phantoms from this folder for analysis on custom
data.

### Installation

This dataset can be installed locally using our Python virtual environment. Specifically, the commands for installation are

```shell
[source venv/bin/activate | call venv\Scripts\activate.bat]
python sampleData.py
```
