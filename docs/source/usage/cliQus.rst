==================
2D QUS CLI Example
==================

Overview
========

This tutorial is a sample walkthrough of QUS parameterization of scan converted IQ data from a Canon system.
For reference, the sample data used in this example can be found here.

Note some aspects of this example require some interaction with the QUS GUI, so we recommend some familiarity before completing this tutorial.

Getting Started
===============

First, assuming we start from the root of the `QuantUS repository`_ using an activate :doc:`Python environment<../installation/environment>` for QuantUS,
we can start by importing relevant packages.

.. _QuantUS repository: https://github.com/TUL-DEV/QuantUS

.. code-block:: python
    
    import os
    import pickle
    from pathlib import Path

    from pyQus.spectral import SpectralAnalysis
    from pyQus.analysisObjects import UltrasoundImage
    from src.Parsers.canonBinParser import findPreset, getImage


Parse Image & Phantom
=====================

Next, we can select and parse both the image and phantom IQ data 
to run our analysis on. Note the image and phantom must be taken 
with the same transducer with identical settings to ensure correctness and 
the ability to compare results to those taken from other systems.

.. code-block:: python

    imagePath = Path("/PATH/TO/ATI-Data-CanonFatStudy/001/Preset_2/20220427104128_IQ.bin")
    phantomPath = Path("/PATH/TO/ATI-Data-CanonFatStudy/Phantom data/Preset_2/20220831121752_IQ.bin")

    # Ensure the image and phantom share a transducer preset
    imPreset = findPreset(imagePath)
    phantomPreset = findPreset(phantomPath)
    assert imPreset == phantomPreset'

    # Parse image and phantom
    imgDataStruct, imgInfoStruct, refDataStruct, refInfoStuct = getImage(
        f"{imagePath.name}", f"{imagePath.parent}", f"{phantomPath.name}", f"{phantomPath.parent}"
    )


Region of Interest Selection
============================

Here, we choose a predetermined region of interest (ROI) to run our QUS 
parameterization on. 