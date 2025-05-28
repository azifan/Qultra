<p align="center">
  <img src="Images/qultra.jpg" alt="drawing" width="700"/>
</p>

#

Qultra unites the QuantUS initiative and Virginia Tech’s QUS expertise into a single open-source platform for ultrasonic tissue characterization and contrast-enhanced imaging. By decoupling algorithms from any specific scanner, it lets researchers import raw RF data from any probe type and apply a standardized, reproducible pipeline—including gain compensation, beam-profile correction and attenuation mapping—via a simple, well-documented API. Its plugin architecture supports rapid prototyping and sharing of modules for spectral analysis, elastography or contrast-agent kinetics, all validated automatically against phantom and in vivo test suites. A modern GUI and fully scriptable CLI run natively on macOS, Windows and Linux, while integrated machine-learning tools enable end-to-end workflows from data acquisition to quantitative prediction. Backed by continuous integration, tutorials and example datasets, Qultra establishes a community-driven standard for transparent, scalable ultrasound research worldwide.

The primary features of Qultra include:

* 2D Ultrasound Tissue Characterization (UTC) via spectral analysis of RF and IQ data
* 2D Dynamic Contrast-Enhanced Ultrasound (DCE-US) Perfusion Imaging Analysis with optional Motion Compensation
* 3D DCE-US Perfusion Imaging Analysis

Notably, Qultra addresses shortcomings in existing state-of-the-art tools by supporting 3D parametric map generation, motion compensation for 2D DCE-US analysis, an ultrasound system-independent approach, and by providing a standardized and reproducible platform for quantitative ultrasound research. 

## UTC Overview

Qultra already includes all features previoulsy included in QuantUS. Given user-inputted RF or IQ ultrasound data, this feature runs spectral analysis to compute quantitative ultrasound parameters and parametric maps on a custom region of interest (ROI). The midband fit (MBF), spectral slope (SS), and spectral intercept (SI) spectral parameters as described by [El Kaffas et al.](https://pubmed.ncbi.nlm.nih.gov/26233222/) have been validated and used in numerous ultrasound studies. Additionally, the backscatter coefficient, attenuation coefficient, Nakagami parameter, effective scatterer size, and effecive scatterer concentration have all been implemented and are in the validation process.

The UTC feature of Qultra also supports a CLI for scalable batch processing. More information and an example can be found in [scCanonUtc.ipynb](CLI-Demos/scCanonUtc.ipynb) and [terasonUtc.ipynb](CLI-Demos/terasonUtc.ipynb).


## DCE-US Overview

For both 2D and 3D cine loops, Qultra performs quantitative analysis on bolus contrast injections by computing a time intensity curve (TIC) for a given ROI or volume of interest (VOI). 2D cine loops can optionally run a 2D motion compensation algorithm developed by [Tiyarattanachai et al.](https://pubmed.ncbi.nlm.nih.gov/35970658/) before the TIC is computed to reduce motion-induced noise.

From here, a lognormal curve is fitted, returning the area under the curve (AUC), peak enhancement (PE), mean transit time (MTT), time to peak (TP), normalization factor (TMPPV), and region area/volume values. For processors with high computational power, a parametric map of each parameter can be generated in both 2D and 3D as well.

![3D DCE-US Parametric Map Example](Images/3dDceusParamap.png)

## Requirements

* [Python](https://www.python.org/downloads/)
* [Homebrew](https://brew.sh/) (MacOS only)

## Environment

First, download [Python3.11.8](https://www.python.org/downloads/release/python-3118/) (non-Conda version) from the Python website. Once installed, note its path. We will refer to this path as `$PYTHON` below.

Next, complete the following steps. Note lines commented with `# Unix` should only be run on MacOS or Linux while lines commented with `# Windows (cmd)` should only be run on the Windows command prompt.

```shell
git clone https://github.com/TUL-Dev/Qultra.git
cd Qultra
$PYTHON -m pip install virtualenv
$PYTHON -m virtualenv .venv
source .venv/bin/activate # Unix
.venv\Scripts\activate # Windows (cmd)
sudo apt-get update & sudo apt-get install python3-dev # Linux
pip install -r requirements.txt
```

Following this example, this environment can be accessed via the `source .venv/bin/activate`
command from the repository directory on Unix systems, and by `.venv\Scripts\activate` on Windows command prompt.

## Building

After configuring a Python virtual environment, finish preparing Qultra to be run using the following commands:

```shell
# Using Python virtual env (Mac/Linux)
chmod +x saveQt.sh
./saveQt.sh

# Using Python virtual env (Windows (cmd))
.\saveQt.sh
```

## Running

### Mac/Linux

```shell
source .venv/bin/activate
python main.py
```

### Windows (cmd)

```shell
.venv\scripts\activate
python main.py
```

## Sample Data

This folder  contains minimal sample data required to get each feature of
Qultra working. Note that since phantom data must be collected using
identical transducer settings as the images they're compared to, we
do not recommend using phantoms from this folder for analysis on custom
data.

This dataset can be installed locally using our Python virtual environment. Specifically, the commands for installation are

```shell
source .venv/bin/activate | .venv\Scripts\activate
python sampleData.py
```

## Reference Phantom Dataset

(in progress)
