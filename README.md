# QuantUS

QuantUS is a free, standalone, native graphical user interface (GUI) supporting 2D Ultrasound Tissue Characterization (UTC) via spectral analysis of radiofrequency (RF) and in-phase and quadrature (IQ) data, 2D Contrast-Enhanced Ultrasound (CEUS) Time Intensity Curve (TIC) Analysis with Motion Compensation, and 3D CEUS TIC Analysis. The tool provides an end-to-end workflow for clinical researchers on Mac OS X, Windows, and Linux. Notably, QuantUS addresses gaps in existing tools by offering unique features, such as 3D parametric map generation, motion compensation for 2D CEUS with TIC analysis, an ultrasound system-independent approach, and an intuitive user interface.

More information about the software can be found on our [webpage]([http](https://quantus.webflow.io/)).

![3D CEUS Parametric Map Example](Images/3dCeusParamap.png)

## Requirements

* [Docker](docker.com/products/docker-desktop/) (only required for Philips RF parser, which is not currently supported)
* [Python3.9](https://www.python.org/downloads/)

## Building

### Mac

```shell
git clone https://github.com/TUL-Dev/QuantUS.git
cd QuantUS
pip install --upgrade pip
python3.9 -m pip install virtualenv
virtualenv --python="python3.9" venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x saveQt.sh
./saveQt.sh
deactivate
```

#### Troubleshooting

To run these commands, make sure you have [HomeBrew](https://brew.sh/) installed.

If you encounter an error after running `pip install -r requirements.txt`, try the following code and then run the command again:

```shell
brew install qt5

brew link qt5 --force

pip install wheel setuptools pip --upgrade
```

### Windows

```shell
git clone https://github.com/TUL-Dev/QuantUS.git
cd QuantUS
pip install --upgrade pip
python3.9 -m pip install virtualenv
virtualenv --python="python3.9" venv
call venv\scripts\activate.bat
pip install -r requirements.txt
ren saveQt.sh saveQt.bat
.\saveQt.bat
deactivate
```

From here, compile Parsers\philips_rf_parser.c into Parsers\philips_rf_parser executable using Windows C compiler of choice.

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
