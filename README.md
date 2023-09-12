# Quantitative Ultrasound Tool

## Overview

This program supports spectral tissue characterization analysis on 2D radiofrequency (RF) and in-phase and quadrature phase (IQ) data.

Additionally, it supports 2D and 3D contrast-enhanced ultrasound (CEUS) analysis for bolus injections. The 2D software uses motion correction software developed by [Thodsawit Tiyarattanachai MD, PhD](https://pubmed.ncbi.nlm.nih.gov/35970658/). Currently, the 3D software does not have motion correction software, but enables users to manually edit their time intensity curve (TIC) as shown in the tutorial below.

## Requirements

* [Docker](docker.com/products/docker-desktop/) (only required for Philips RF parser)
* Any version of [Python3.9](https://www.python.org/downloads/)

## Building

### Mac

```shell
git clone https://github.com/davidspector67/QusTools.git
cd QusTools
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

If you encounter an error after running `pip install -r requirements.txt`, try the following code and then run the command again:

```shell
brew install qt5

brew link qt5 --force

pip install wheel setuptools pip --upgrade
```

### Windows

```shell
git clone https://github.com/davidspector67/QusTools.git
cd QusTools
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

## Downloading Phantom Collection

### Mac/Linux

```shell
source venv/bin/activate
pip install gdown
gdown --no-check-certificate --folder \
https://drive.google.com/drive/folders/1IQeHYJNu6G7WO2XwlPPmc_ZsfUpzYQgM
deactivate
```

## Dev Practices

The main branch of this repository is read-only for all users. To contribute to this repository, email [David Spector](davidspector9@gmail.com) to become a contributer.

### Branch Naming

When working on any feature of the software, use the NAME-FEATURE branch naming convention. When finished, submit a pull request to merge with the main branch.
