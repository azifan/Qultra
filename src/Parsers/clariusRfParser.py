from imports import *

import sys, os
srcDirectory = os.path.dirname(os.path.abspath(__file__)) + '/..'
sys.path.append(srcDirectory)

import globals
import representations
from scipy.interpolate import interp1d
import re, yaml
from lib.data_generation.scan_convert import ScanConvertAccelerated

storage_client = storage.Client()

def info(ID, file, isPhantom=False):
    """Wrapper function of read_Clariusinfo

    Args:
        ID (string): caseID identifier (e.g., "PDG1604540332910"), for phantom use "Phantom"
        file (string): video filename within patient/phantom identifier (e.g., "2020-11-05T01-35-42+0000")
        isPhantom (bool): False (default): patient data, True: phantom data,

    Returns:
        dict: info header with Clarius parameters
    """

    path = ID + config.clarius.PATH_EXTRACTED

    Files = {}
    Files["directory"] = path
    Files["xmlName"] = config.clarius.local_store_xml_file
    # Files["ymlName"] = path + file + "_rf.yml"
    Files["ymlName"] = file + config.clarius.TRAIL_RF_YML
    Files["name"] = file + config.clarius.TRAIL_RF_RAW
    try:
        imgInfo = read_Clariusinfo(
            Files["name"],
            Files["xmlName"],
            Files["ymlName"],
            Files["directory"],
            isPhantom,
        )
    except Exception as e:
        print("Error reading ClariusInfo")
        logging.warning("Error reading ClariusInfo")
        logging.warning(e)
    
    return imgInfo

def checkWhichTransducer(par_list):
    result = 0
    MlaSlaFlag = 1
    new_p = 0
    new_r = 0
    for param in par_list:
        if "pitch" in param:
            if float(param[-7:]) == 300.0:
                #logger.info("New Transducer", caseId, filename, "gpu-linux")
                # probably set a flag here
                new_p = 1
                print('PITCH IS ', float(param[-7:]))
            elif float(param[-7:]) == 330.0:
                #logger.info("Old Transducer", caseId, filename, "gpu-linux")
                # probably set a flag here too
                #old_p = 0
                new_p = 0
                print('PITCH IS ', float(param[-7:]))
            else:
                print("Unknown settings. Going with new Transducer settings.")
                #logger.info("Unknown settings. Going with new Transducer settings.", caseId, filename, "gpu-linux")
                new_p = 1
                print('PITCH IS ELSE')
        elif "radius" in param:
            if float(param[-7:]) == 45.0:
                #logger.info("New Transducer", caseId, filename, "gpu-linux")
                # probably set a flag here
                new_r = 1
                print('RADIUS IS ', float(param[-7:]))
            elif float(param[-7:]) == 60.0:
                #logger.info("Old Transducer", caseId, filename, "gpu-linux")
                # probably set a flag here too
                #old_r = 0
                new_r = 0
                print('RADIUS IS ', float(param[-7:]))
            else:
                print("Unknown settings. Going with new Transducer settings.")
                #logger.info("Unknown settings. Going with new Transducer settings.", caseId, filename, "gpu-linux")
                new_r = 1
                print('RADIUS IS UNKNOWN')
        elif "software version" in param:
            print('Patient version number is '+ param)
            try:
                print((param[18:22]))
                if float(param[18:21])<8.3:  #-10:-7
                    #Is MLA
                    MlaSlaFlag = 1
                    print('SW VERSION < 8.3 - MLA')
                elif float(param[18:22])==10.5:
                    #Is MLA
                    MlaSlaFlag = 1
                    print('SPECIAL CASE - SW VERSION 10.5 - MLA')
                else:
                    #Is SLA
                    MlaSlaFlag = 0
                    print('SW VERSION > 8.3 - SLA')
            except:
                if float(param[-14:-10])<8.3:
                    #Is MLA
                    MlaSlaFlag = 1
                    print('SW VERSION < 8.3 - MLA')
                elif float(param[-14:-10])==10.5:
                    #Is MLA
                    MlaSlaFlag = 1
                    print('SPECIAL CASE - SW VERSION 10.5 - MLA')
                else:
                    #Is SLA
                    MlaSlaFlag = 0
                    print('SW VERSION > 8.3 - SLA')
    #print('new_p:', new_p)
    #print('new_r:', new_r)
    #print('MlaSlaFlag:', MlaSlaFlag)
    #The result value will determinate the array position from we are getting the phantomData
    # Need to match the same order as the data is being saved on clarius.load_all_phantoms_speedUp
    # Order ----> PHANTOM_LIST = [PHANTOM_C3,PHANTOM_C3H]
    # Where PHANTOM_C3[0],PHANTOM_C3H[1],......
    if new_p + new_r + MlaSlaFlag == 3:
        result = config.clarius.TRANSDUCER_FLAG_C3HMLA # 3 #New Phantom C3H + MLA
        print('loading Phantom C3H + MLA')
    elif new_p + new_r + MlaSlaFlag == 2:
        result = config.clarius.TRANSDUCER_FLAG_C3HSLA # 2 #New Phantom C3H + SLA
        print('loading Phantom C3H + SLA')
    elif new_p + new_r + MlaSlaFlag == 1:
        result = config.clarius.TRANSDUCER_FLAG_C3MLA #1 #Old Phantom C3 + MLA
        print('loading Phantom C3 + MLA')
    elif new_p + new_r + MlaSlaFlag == 0:
        result = config.clarius.TRANSDUCER_FLAG_C3SLA # 0 #Old Phantom C3 + SLA
        print('loading Phantom C3 + SLA')
    else:
        print('Error loading phantom')
        logging.warning('Error loading phantom')
        result = []
    print('Transducer Flag:', result)
    return result

# MODIFIED TO WORK WITH GOOGLE CLOUD BUCKETS
def read_Clariusinfo(
    filename=None, xmlFilename=None, ymlFileName=None, filepath=None, isPhantom=False
):
    """Obtains information for Clarius data file, including data dimensions and geometric information

    Args:
        isPhantom (bool): True: phantom data, False: other data (there is no practical difference)
        filename (string, optional): Filename of RF data to be loaded. Defaults to None.
        xmlFilename (string, optional): Location of xml file containing probe info. Defaults to None.
        ymlFileName (string, optional): Location of .yml file contain raw data header info. Defaults to None.
        filepath (string, optional): Folder where temporal files are located. Defaults to None.

    Returns:
        dict: info header with Clarius parameters (studyMode, file, filepath, probe, system, studyID, samples, lines, depthOffset, depth, width,
            rxFrequency, samplingFrequency, txFrequency, centerFrequency, targetFOV, numFocalZones, numFrames, frameSize, depthAxis, widthAxis, lineDensity, height,
            pitch, dynRange, yOffset, vOffset, lowBandFreq, upBandFreq, gain, rxGain, userGain, txPower, power, PRF, yRes, yResRF, xRes, xResRF, quad2X, Apitch, Lpitch,
            Radius, PixelsPerMm, lateralRes, axialRes)
    """

    # Some Initilization
    phantom_bucket = storage_client.get_bucket(
        config.clarius.PHANTOM_BUCKET
    )  # inserted by M&E on dec/2/2022
    studyID = filename[11 : (len(filename) - 4)]
    # studyEXT = filename[(len(filename) - 2) :]

    rfFilePath = filepath + filename

    # get from google
    if isPhantom:
        while True:
            try:
                # temp = storage.blob.Blob(rfFilePath,globals.bucket_pull_DSP_Part1) # commented out by M&E on dec/2/2022
                temp = storage.blob.Blob(rfFilePath, phantom_bucket)
                content = temp.download_as_string()
                break
            except:
                print("\t\tfile load error")
                logging.warning("File load error")
                print(traceback.format_exc())
                pass
    else:
        try:
            temp = storage.blob.Blob(rfFilePath, globals.bucket_pull_DSP_Part1)
            content = temp.download_as_string()
        except:
            print("\t\tfile load error")
            logging.warning("File load error")
            print(traceback.format_exc())
            pass
    # write to temp file, then use temp file
    try:
        if isPhantom == True:
            tempFile1 = "temp_files/tempFile1_Phantom"
        else:
            tempFile1 = "temp_files/tempFile1" + studyID[:27]
    except:
        print(traceback.format_exc())
            
    """Sergio: Immediately deleted afterwards, filename irrelevant"""

    fpoint = open(tempFile1, "wb")
    fpoint.write(content)
    fpoint.close()

    # Open RF file for reading
    while True:
        try:
            with open(tempFile1, mode="r") as fid:
                # load the header information into a structure and save under a separate file
                hinfo = np.fromfile(fid, dtype="uint32", count=5)
            break
        except:
            print("\t\terror opening ", tempFile1)
            logging.warning("Error opening", tempFile1)
            print(traceback.format_exc())
            pass

    # delete temp file
    try:
        os.remove(tempFile1)
    except OSError:
        logging.warning("Error deleting temp file")
        print(traceback.format_exc())
        pass

    header = {"id": 0, "frames": 0, "lines": 0, "samples": 0, "sampleSize": 0}
    header["id"] = hinfo[0]
    header["nframes"] = hinfo[1]  # frames
    header["w"] = hinfo[2]  # lines
    header["h"] = hinfo[3]  # samples
    header["ss"] = hinfo[4]  # sampleSize (bytes per sample?)

    ymlFilePath = filepath + ymlFileName
    # get from google
    # temp = storage.blob.Blob(ymlFilePath,globals.bucket_pull_DSP_Part1) # commented out by M&E on dec/2/2022
    if isPhantom:
        temp = storage.blob.Blob(ymlFilePath, phantom_bucket)
        content = temp.download_as_string()
    else:
        temp = storage.blob.Blob(ymlFilePath, globals.bucket_pull_DSP_Part1)
        content = temp.download_as_string()
    # write to temp file, then use temp file

    if isPhantom == True:
        tempFile2 = "temp_files/tempFile2_Phantom"
    else:
        tempFile2 = "temp_files/tempFile2" + studyID[:27]
    """Sergio: Immediately deleted aftewards, filename irrelevant"""

    fpoint = open(tempFile2, "wb")
    fpoint.write(content)
    fpoint.close()

    with open(tempFile2) as f:  # Sergio: Correct .yaml file before parsing
        lines = f.readlines()
        strtemp = lines[7].replace(",", ":").replace("}{", ",")
        lines[7] = strtemp
    with open(tempFile2 + "_corr", "w") as f:
        f.writelines(lines)

    # Load the yml file
    try:
        # Yml File of Clarius
        with open(tempFile2 + "_corr", mode="r") as yml_fid:
            yml_data = yaml.safe_load(yml_fid)
    except yaml.YAMLError as exc:
        print("Error In Parsing : %s " % exc.__cause__)
        logging.warning("Error In Parsing : %s " % exc.__cause__)
        print("Trying loading the edit_yml.......")
        try:
            ymlFilePath = ymlFilePath[:27] + "edit_" + str(ymlFilePath[27:])
            if isPhantom:
                temp = storage.blob.Blob(ymlFilePath, phantom_bucket)
                content = temp.download_as_string()
            else:
                temp = storage.blob.Blob(ymlFilePath, globals.bucket_pull_DSP_Part1)
                content = temp.download_as_string()
            if isPhantom == True:
                tempFile2 = "temp_files/tempFile2_Phantom"
            else:
                tempFile2 = "temp_files/tempFile2" + studyID[:27]

            fpoint = open(tempFile2, "wb")
            fpoint.write(content)
            fpoint.close()

            with open(tempFile2) as f:  # Sergio: Correct .yaml file before parsing
                lines = f.readlines()
                strtemp = lines[7].replace(",", ":").replace("}{", ",")
                lines[7] = strtemp
            with open(tempFile2 + "_corr", "w") as f:
                f.writelines(lines)

            with open(tempFile2 + "_corr", mode="r") as yml_fid:
                yml_data = yaml.safe_load(yml_fid)

        except:
            print("Error In Parsing second try of yml : %s " % exc.__cause__)
            logging.warning("Error In Parsing second try of yml : %s " % exc.__cause__)
            print(traceback.format_exc())

    # delete temp file
    try:
        if isPhantom == False:
            with open(tempFile2) as infile:
                temp = infile.readlines()
                print((temp))
            try:
                globals.transducerFlag = checkWhichTransducer(temp)
            except Exception as e :
                print("Could not get patient headers to determinate phantom for "+ filename +' '+ str(e))
                logging.warning("Could not get patient headers to determinate phantom for "+ filename+' '+ str(e))
                print("Loading C3 phantom by default")
                print(traceback.format_exc())
                globals.transducerFlag = config.clarius.TRANSDUCER_FLAG_C3MLA # But MLA!!!!
                pass
        os.remove(tempFile2)
        os.remove(tempFile2 + "_corr")
    except OSError:
        logging.warning("Error deleting temp file")
        pass

    # from yml file
    transFreq = yml_data["transmit frequency"]
    header["txf"] = float(
        transFreq[0 : (len(transFreq) - 3)]
    )  # transmit freq - also called center freq
    # header["txf"] = 4

    sampling_rate = yml_data["sampling rate"]
    header["sf"] = (
        float(sampling_rate[0 : (len(sampling_rate) - 3)]) * 1e6
    )  # sampling freq - also called receive freq = sampling rate
    # header["sf"]=20000000
    """Sergio(resolved): There is a contradiction here, the phantom fs is 15MHz, but we had previously hard-coded 20 MHz??"""
    """Adi: It is 15 MHz"""

    header["dr"] = config.signal_processing_alpha3_parameter.header_dr  # Fixed from Usx Probe.xml file
    """Adi: could just be number of bytes to go through to overcome header"""
    """Sergio: I think this is a distance step at transducer surface per line (in um/10), but this seems to be the wrong value"""
    header["ld"] = yml_data["size"]["number of lines"]
    # header["ld"] = 192 # lineDensity => num of lines is 192... standard.

    info = {}

    # For USX - must also read probe file for probe parameters probeStruct and the('probes.xml', header.probe);
    try:
        probeStruct = readprobe_Clarius(xmlFilename, config.clarius.PROBE_ID)
    except:
        logging.warning("Error reading probe file Clarius")
    info["probeStruct"] = probeStruct
    # assignin('base','header', header)

    # Add final parameters to info struct
    info["studyMode"] = "RF"
    info["file"] = filename
    info["filepath"] = filepath
    info["probe"] = "clarius"
    info["system"] = "Clarius"
    info["studyID"] = studyID
    info["samples"] = header["h"]
    info["lines"] = header[
        "w"
    ]  # probeStruct.numElements; % or is it > header.w; Oversampled line density?
    info["depthOffset"] = probeStruct["transmitoffset"]  # unknown for USX
    info["depth"] = (
        info["samples"] / header["sf"] * config.signal_processing_alpha3_parameter.speed_of_sound / 2 * 10**3
    )  # Depth in mm
    # info["depth"] = header["ss"] * 10 ** 1 #1275/8; % in mm; from SonixDataTool.m:603 - is it header.dr?
    info["width"] = (
        header["dr"] * 10**1
    )  # 1827/8; %info["probeStruct.pitch*1e-3*info["probeStruct.numElements; % in mm; pitch is distance between elements center to element center in micrometers
    """Sergio4: I could not make sense of this numbers.  header ["dr"] = 23"""
    """Adi: don't know either"""
    info["rxFrequency"] = header["sf"]
    info["samplingFrequency"] = header["sf"]
    info["txFrequency"] = header["txf"]
    info["centerFrequency"] = header[
        "txf"
    ]  # should be same as transmit freq - it's the freq. of transducer
    """Sergio: probeStruct["frequency"]["center"] = 5 MHz, while header["txf"] = 4. Contradiction?"""
    """Adi (resolved): xml file isn't Clarius' (not really same transducer... hybrid... mixed), work with fileheader"""
    info["targetFOV"] = 0
    info["numFocalZones"] = 1  # Hardcoded for now - should be readable
    info["numFrames"] = header["nframes"]
    info["frameSize"] = info["depth"] * info["width"]
    info["depthAxis"] = info["depth"]
    info["widthAxis"] = info["width"]
    info["lineDensity"] = header["ld"]
    info["height"] = info["depth"]  # This could be different if there is a target FOV
    info["pitch"] = probeStruct["pitch"]
    info["dynRange"] = 0  # Not sure if available
    info["yOffset"] = 0
    info["vOffset"] = 0
    info["lowBandFreq"] = (
        info["txFrequency"] - 0.5 * probeStruct["frequency"]["bandwidth"]
    )
    info["upBandFreq"] = (
        info["txFrequency"] + 0.5 * probeStruct["frequency"]["bandwidth"]
    )
    info["gain"] = 0
    info["rxGain"] = 0
    info["userGain"] = 0
    info["txPower"] = 0
    info["power"] = 0
    info["PRF"] = 0

    # One of these is the preSC, the other is postSC resolutions
    info["yRes"] = (
        (info["samples"] / info["samplingFrequency"] * config.signal_processing_alpha3_parameter.speed_of_sound / 2)
        / info["samples"]
    ) * 10**3  # >> real resolution based on curvature
    """Sergio(resolved with Adi): With sampling frequency = 15 MHz, this works -> we obtain 15 cm. Seems fs = 20 MHz is wrong..."""
    info["yResRF"] = (
        info["depth"] / info["samples"]
    )  # >> fake resolution - simulating linear probe
    info["xRes"] = (
        info["probeStruct"]["pitch"]
        * 1e-6
        * info["probeStruct"]["numElements"]
        / info["lineDensity"]
    ) * 10**3  # >> real resolution based on curvature
    info["xResRF"] = (
        info["width"] / info["lines"]
    )  # >> fake resolution - simulating linear probe
    """Sergio: Probably info["width"] is not correct, it would need the right pitch"""
    """Adi (resolved): Not currently used"""

    # Quad 2 or accounting for change in line density
    info["quad2X"] = 1

    # Ultrasonix specific - for scan conversion - from: sdk607/MATLAB/SonixDataTools/SonixDataTools.m:719
    info["Apitch"] = (
        info["samples"] / info["samplingFrequency"] * config.signal_processing_alpha3_parameter.speed_of_sound / 2
    ) / info[
        "samples"
    ]  # Axial pitch - axial pitch - in metres as expected by scanconvert.m
    info["Lpitch"] = (
        info["probeStruct"]["pitch"]
        * 1e-6
        * info["probeStruct"]["numElements"]
        / info["lineDensity"]
    )  # Lateral pitch - lateral pitch - in meters
    info["Radius"] = info["probeStruct"]["radius"] * 1e-6
    info[
        "PixelsPerMM"
    ] = (
        config.signal_processing_alpha3_parameter.info_PixelsPerMm_ScanConversion
    )  # Number used to interpolate number of pixels to be placed in a mm in image
    info["lateralRes"] = 1 / info["PixelsPerMM"]  # Resolution of postSC
    info["axialRes"] = 1 / info["PixelsPerMM"]  # Resolution of postSC

    # print ("Clarius Info : %s " % info)

    return info


def checkLengthEnvRF(rfa, rfd, rfn, env, db):
    lenEnv = env.shape[2]
    lenRf = rfa.shape[2]

    if lenEnv == lenRf:
        pass
    elif lenEnv > lenRf:
        env = env[:, :, :lenRf]
    else:
        db = db[:, :, :lenEnv]
        rfa = rfa[:, :, :lenEnv]
        rfd = rfd[:, :, :lenEnv]
        rfn = rfn[:, :, :lenEnv]

    return rfa, rfd, rfn, env, db


def readprobe_Clarius(xmlFileName, probeID=config['clarius']['PROBE_ID']):
    """Obtain information for Clarius probe as given in Clarius XML file

    Args:
        xmlFileName (string, optional): xml filename with probe info. Defaults to None.
        probeID (int, optional): probe index within Clarius list. Defaults to None.

    Returns:
        dict: Probe struct contain all probe parameters (biopsy, vendors, type, transmitoffset, center, bandwidth, maxfocusdistance,
              maxsteerangle, minFocusDistanceDoppler, minlineduration, FOV, homeMethod, minTimeBetweenPulses, steps, homeCorrection, numElements, pinOffset,
              pitch, radius, support, muxWrap, elevationLength, maxPwPrp, invertedElements, frequency (center, bandwidth),
              motor (FOV, homeMethod, minTimeBetweenPulses, motor_radius, steps, homeCorrection)
    """

    # get from google
    # temp = storage.blob.Blob(fileName,bucket_pull)
    # content = temp.download_as_string()
    # write to temp file, then use temp file
    # fpoint = open('temp_files/tempFile3', 'wb')
    # fpoint.write(content)
    # fpoint.close()
    # Open the probes.xml file and read it into mem
    # fid = open('temp_files/tempFile3', mode='r')
    fid = open(xmlFileName, mode="r")
    if fid is None:
        print("Could not find the probes.xml file ")
        Probe = {}
        return

    xmldoc = xml.dom.minidom.parse(fid)  # or xml.dom.minidom.parseString(xml_string)
    root = et.fromstring(xmldoc.toprettyxml())
    # Picking out the text relating to the probe
    probeRoot = root.find("./probe[@id='%s']" % str(probeID))

    # create empty Dictionary for saving data by its keys
    Probe = {}
    probeName = probeRoot.attrib["name"]
    Probe["name"] = probeName

    for elem in probeRoot.iter():
        # #print(elem.tag,elem.attrib,elem.text)
        if elem.tag == "biopsy":
            biopsy = elem.text
            # print("Biopsy Text %s " % biopsy)
            Probe["biopsy"] = biopsy
        elif elem.tag == "vendors":
            vendors = elem.text
            # print("Vendors Text %s " % vendors)
            Probe["vendors"] = vendors
        elif elem.tag == "type":
            probe_type = elem.text
            # print("Type Text %s " % probe_type)
            Probe["type"] = int(probe_type)
        elif elem.tag == "transmitoffset":
            transmitoffset = elem.text
            # print("transmitoffset Text %s " % transmitoffset)
            Probe["transmitoffset"] = int(float(transmitoffset))
        elif elem.tag == "center":
            freqCenter = elem.text
            # print("freCenter Text %s " % freqCenter)
        elif elem.tag == "bandwidth":
            freqBandwith = elem.text
            # print("freqBandwith Text %s " % freqBandwith)
        elif elem.tag == "maxfocusdistance":
            maxfocusdistance = elem.text
            # print("maxfocusdistance Text %s " % maxfocusdistance)
            Probe["maxfocusdistance"] = int(maxfocusdistance)
        elif elem.tag == "maxfocusdistance":
            maxfocusdistance = elem.text
            # print("maxfocusdistance Text %s " % maxfocusdistance)
            Probe["maxfocusdistance"] = int(maxfocusdistance)
        elif elem.tag == "maxsteerangle":
            maxsteerangle = elem.text
            # print("maxsteerangle Text %s " % maxsteerangle)
            Probe["maxsteerangle"] = int(maxsteerangle)
        elif elem.tag == "minFocusDistanceDoppler":
            minFocusDistanceDoppler = elem.text
            # print("minFocusDistanceDoppler Text %s " % minFocusDistanceDoppler)
            Probe["minFocusDistanceDoppler"] = int(minFocusDistanceDoppler)
        elif elem.tag == "minlineduration":
            minlineduration = elem.text
            # print("minlineduration Text %s " % minlineduration)
            Probe["minlineduration"] = int(minlineduration)
        elif elem.tag == "FOV":
            probMotorFOV = elem.text
            # print("probMotorFOV Text %s " % probMotorFOV)
        elif elem.tag == "homeMethod":
            probMotorHomeMethod = elem.text
            # print("probMotorHomeMethod Text %s " % probMotorHomeMethod)
        elif elem.tag == "minTimeBetweenPulses":
            probMotorminTimeBetweenPulses = elem.text
            # print("probMotorminTimeBetweenPulses Text %s " % probMotorminTimeBetweenPulses)
        # elif(elem.tag=="radius"):
        #     probMotorRadius=elem.text
        #     #print("probMotorRadius Text %s " % probMotorRadius)
        elif elem.tag == "steps":
            probMotorSteps = elem.text
            # print("probMotorSteps Text %s " % probMotorSteps)
        elif elem.tag == "homeCorrection":
            probMotorHomeCorrection = elem.text
            # print("probMotorHomeCorrection Text %s " % probMotorHomeCorrection)
        elif elem.tag == "numElements":
            numElements = elem.text
            # print("numElements Text %s " % numElements)
            Probe["numElements"] = int(numElements)
        elif elem.tag == "pinOffset":
            pinOffset = elem.text
            # print("pinOffset Text %s " % pinOffset)
            Probe["pinOffset"] = int(pinOffset)
        elif elem.tag == "pitch":
            pitch = elem.text
            # print("pitch Text %s " % pitch)
            Probe["pitch"] = int(pitch)
        elif elem.tag == "radius":
            radius = elem.text
            # print("radius Text %s " % radius)
            Probe["radius"] = int(radius)
        elif elem.tag == "support":
            support = elem.text
            # print("support Text %s " % support)
            Probe["support"] = support
        elif elem.tag == "muxWrap":
            muxWrap = elem.text
            # print("muxWrap Text %s " % muxWrap)
            Probe["muxWrap"] = muxWrap
        elif elem.tag == "elevationLength":
            elevationLength = elem.text
            # print("elevationLength Text %s " % elevationLength)
            Probe["elevationLength"] = int(float(elevationLength))
        elif elem.tag == "maxPwPrp":
            maxPwPrp = elem.text
            # print("maxPwPrp Text %s " % maxPwPrp)
            Probe["maxPwPrp"] = int(maxPwPrp)
        elif elem.tag == "invertedElements":
            invertedElements = elem.text
            # print("invertedElements Text %s " % invertedElements)
            Probe["invertedElements"] = int(invertedElements)

    Probe["frequency"] = {"center": int(freqCenter), "bandwidth": int(freqBandwith)}
    Probe["motor"] = {
        "FOV": int(probMotorFOV),
        "homeMethod": int(probMotorHomeMethod),
        "minTimeBetweenPulses": int(probMotorminTimeBetweenPulses),
        "motor_radius": int(0),
        "steps": int(probMotorSteps),
        "homeCorrection": int(probMotorHomeCorrection),
    }
    # print("***************************************************************************")

    return Probe

def read_Clariusimg_Phantom(Info=None, frame=None):
    """wrapper function to read phantom data from Clarius file, including rf and scan-converted b-mode

    Args:
        Info (dict, optional): info header generated with readClarius info. Defaults to None.
        frame (int, optional): frame index to load from video rf. Defaults to None (indexed from 1 onwards)

    Returns:
        dict: Data dict containing RF: (RF data Depth x Width), scBmode: scan converted B-mode,
    """

    # sys.path.append(os.path.dirname('./solution/clarius_read/'))
    # sys.path.append(os.path.dirname('./solution/convert/'))
    # from PRead_Clarius import PRead_Clarius
    # from PRead_Clarius2 import PRead_Clarius2
    # from rf2bmode import rf2bmode
    # from scanconvert_mapped import scanconvert_mapped
    # from scanconvert import scanconvert
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Read ultrasonix rf data from tablet and touch. Needs meta data stored as struct.
    # The ModeIM struct contains a map of x and y coordiantes to retrace a
    # point in a scan conerted image back to the original non-scanconverted RF
    # data.
    # Input:
    # Info - meta data with parameters for image, analysis and display, obtained from info_Phantom()
    # frame - frame number to read
    # Output:
    # Bmode - Scan converted bmode image for display.
    # Data - Contains: .orig (original RF data for image), .data (scan converted RF data), .xmap (x coordinates of point on original data), .ymap (ycoordinate of point of original data)
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # Get RF data file path using the metadata in Info
    usx_rf_filepath = Info["filepath"] + Info["file"]

    # Read the image data
    try:
        rf_atgc, rf_dtgc, ModeIM, EnvIM, dB, EnvLinear = PRead_Clarius_TGC_Correct(
            usx_rf_filepath, config.clarius.clarius_version, isPhantom=True
        )
        # else:
        #     ModeIM = PRead_Clarius(
        #         usx_rf_filepath, config.clarius.clarius_version, isPhantom=True
        #     )
    except:
        logging.warning("Error reading image data Clarius")
    # import
    # plt.imshow(ModeIM[:,:,0], vmin=-1, vmax = 1)
    # plt.savefig("test.png")

    # Here we introduce some logic in terms of phantom normalization
    if config.modes.phantom_frame_averaging == 1:
        # Average over all frames
        ModeIM = np.mean(ModeIM, axis=2)
        ModeATGC = np.mean(rf_atgc, axis=2)
        EnvIM = np.mean(EnvIM, axis=2)
        dB = np.mean(dB, axis=2)
        #EnvLinear = np.mean(EnvLinear, axis=2)
        EnvLinear = convert_env_to_rf_ntgc(EnvIM, np.power(10, dB/20))  # Fix for consistency with 0.4.1.5.1 - remove in 0.4.1.7         
    else:
        frame = frame - 1
        # Make ModeIM just one frame - the chosen frame
        ModeIM = ModeIM[:, :, frame]
        """Sergio: would it be possible to use all 24 frames for averaging? if only one frame (presently id:0), typically later frames would be more stable (movement artifacts, etc.)"""
        # Make EnvIM just one frame - the chosen frame
        ModeATGC = rf_atgc[:, :, frame]
        EnvIM = EnvIM[:,:, frame]
        dB = dB[:,:, frame]
        #EnvLinear = EnvLinear[:,:, frame]
        EnvLinear = convert_env_to_rf_ntgc(EnvIM, np.power(10, dB/20))  # Fix for consistency with 0.4.1.5.1 - remove in 0.4.1.7

    # frame=frame-1
    # Create a straightforward Bmode without scan conversion for frame number frame
    #Bmode = representations.rf2bmode(ModeIM)  # pre-scan converted b-mode
    # print(np.shape(Bmode))
    # Get the map of coordinates xmap and ymap to be able to plot a point in
    # scanconvert back to original
    # scModeIM =scanconvert(ModeIM, Info)# scanconvert_mapped(ModeIM, Info)

    # Simple scan convert of the image to be displayed.
    #scBmode = representations.scanconvert(Bmode, Info)

    # Ouput
    Data = {}
    # Data["scRF"] = scModeIM
    #Data["scBmode"] = scBmode
    Data["RF"] = ModeIM
    Data["Env"] = EnvIM
    Data["RF_ATGC"] = ModeATGC
    Data["EnvLinear"] = EnvLinear    
    # Data["Bmode"] = Bmode

    return Data

########################################################################################
# Helper Functions Related to TGC Correction
# correction_method = 'A'

def read_tgc_file(file_timestamp, rf_timestamps):
    tgc_file_name_dottgc = file_timestamp + "_env.tgc"
    tgc_file_name_dotyml = file_timestamp + "_env.tgc.yml"

    if os.path.isfile(tgc_file_name_dottgc):
        tgc_file_name = tgc_file_name_dottgc
    elif os.path.isfile(tgc_file_name_dotyml):
        tgc_file_name = tgc_file_name_dotyml
    else:
        return None

    with open(tgc_file_name, "r") as file:
        data_str = file.read()

    frames_data = data_str.split("timestamp:")[1:]
    frames_data = [
        frame
        if "{" in frame
        else frame + "  - { 0.00mm, 15.00dB }\n  - { 120.00mm, 35.00dB }"
        for frame in frames_data
    ]
    frames_dict = {
        timestamp: frame
        for frame in frames_data
        for timestamp in rf_timestamps
        if str(timestamp) in frame
    }
    filtered_frames_data = [
        frames_dict.get(timestamp)
        for timestamp in rf_timestamps
        if frames_dict.get(timestamp) is not None
    ]

    return filtered_frames_data


def clean_and_convert(value):
    clean_value = ''.join([char for char in value if char.isdigit() or char in ['.', '-']])
    return float(clean_value)

def extract_tgc_data_from_line(line):
    tgc_pattern = r'\{([^}]+)\}'
    return re.findall(tgc_pattern, line)

def read_tgc_file_v2(file_timestamp, rf_timestamps):
    tgc_file_name_dottgc = file_timestamp + "_env.tgc"
    tgc_file_name_dotyml = file_timestamp + "_env.tgc.yml"
    
    blob = globals.bucket_pull_DSP_Part1.list_blobs()
    client = storage.Client()
    tgc_file_name = 0
    for file in tqdm(client.list_blobs(globals.bucket_pull_DSP_Part1, prefix=file_timestamp)):
        if file.name.startswith(file_timestamp) and (file.name.endswith("_env.tgc.yml") or file.name.endswith("_env.tgc")):
            tgc_file_name = file.name
    if tgc_file_name == 0:
        return None
    while True:
        try:
                temp = storage.blob.Blob(tgc_file_name, globals.bucket_pull_DSP_Part1)
                data_str = temp.download_as_string()
                data_str = data_str.decode('utf-8')
                break
        except:
                print("\t\tfile load error")
                logging.warning("File load error")
                pass
    #This is for local loading
    '''if os.path.isfile(tgc_file_name_dottgc):
        tgc_file_name = tgc_file_name_dottgc
    elif os.path.isfile(tgc_file_name_dotyml):
        tgc_file_name = tgc_file_name_dotyml
    else:
        return None

    with open(tgc_file_name, "r") as file:
        data_str = file.read()'''
    frames_data = data_str.split('timestamp:')[1:]
    frames_data = [frame if "{" in frame else frame + "  - { 0.00mm, 15.00dB }\n  - { 120.00mm, 35.00dB }" for frame in frames_data]
    frames_dict = {timestamp: frame for frame in frames_data for timestamp in rf_timestamps if str(timestamp) in frame}
    missing_timestamps = [ts for ts in rf_timestamps if ts not in frames_dict]
    if len(missing_timestamps) >= 2:
        print("The number of missing timestamps for " + tgc_file_name + " is: " + str(len(missing_timestamps)) + ". Skipping this scan with current criteria.")
        return None
    elif len(missing_timestamps) == 1:
        missing_ts = missing_timestamps[0]
        print("missing timestamp is: ")
        print(missing_ts)
        index = np.where(rf_timestamps == missing_ts)[0][0]
        prev_ts = rf_timestamps[index - 1]
        next_ts = rf_timestamps[index + 1]
        prev_data = frames_dict[prev_ts]
        next_data = frames_dict[next_ts]
        interpolated_data = f" {missing_ts} "
        prev_tgc_entries = extract_tgc_data_from_line(prev_data)
        next_tgc_entries = extract_tgc_data_from_line(next_data)
        for prev_val, next_val in zip(prev_tgc_entries, next_tgc_entries):
            prev_mm_str, prev_dB_str = prev_val.split(",")
            next_mm_str, next_dB_str = next_val.split(",")
            prev_dB = clean_and_convert(prev_dB_str)
            next_dB = clean_and_convert(next_dB_str)
            prev_mm = clean_and_convert(prev_mm_str)
            next_mm = clean_and_convert(next_mm_str)
            if abs(prev_dB - next_dB) <= 4:
                interpolated_dB = (prev_dB + next_dB) / 2
            else:
                print("Difference in dB values too large for interpolation. Skipping this Scan with current criteria.")
                return None
            interpolated_data += f"{{ {prev_mm}mm, {interpolated_dB:.2f}dB }}"
        print("prev data for " + str(prev_ts) + " is: ")
        print(prev_data)
        print("interpolated data for " + str(missing_ts) + " is: ")
        print(interpolated_data)
        print("next data for " + str(next_ts) + " is: ")
        print(next_data)
        frames_dict[missing_ts] = interpolated_data
    filtered_frames_data = [frames_dict.get(timestamp) for timestamp in rf_timestamps if frames_dict.get(timestamp) is not None]
    

    return filtered_frames_data


def generate_default_tgc_matrix(num_frames):
    image_depth_mm = 150
    num_samples = 2928
    depths_mm = np.linspace(0, image_depth_mm, num_samples)
    default_mm_values = [0.00, 120.00]
    default_dB_values = [15.00, 35.00]

    default_interpolation_func = interp1d(
        default_mm_values,
        default_dB_values,
        bounds_error=False,
        fill_value=(default_dB_values[0], default_dB_values[-1]),
    )
    default_tgc_matrix = default_interpolation_func(depths_mm)[None, :]
    default_tgc_matrix = np.repeat(default_tgc_matrix, num_frames, axis=0)

    default_tgc_matrix_transpose = default_tgc_matrix.T
    linear_default_tgc_matrix_transpose = 10 ** (default_tgc_matrix_transpose / 20)
    linear_default_tgc_matrix_transpose = linear_default_tgc_matrix_transpose[None, ...]
    linear_default_tgc_matrix_transpose = np.repeat(
        linear_default_tgc_matrix_transpose, 192, axis=0
    )

    print(
        "A default TGC matrix of size {} is generated.".format(
            linear_default_tgc_matrix_transpose.shape
        )
    )
    #     for depth, tgc_value in zip(depths_mm, default_tgc_matrix[0]):
    #         print(f"Depth: {depth:.2f}mm, TGC: {tgc_value:.2f}dB")

    return linear_default_tgc_matrix_transpose


def generate_tgc_matrix(file_timestamp, rf_timestamps, num_frames, isPhantom):
    image_depth_mm = 150
    num_samples = 2928
    if isPhantom:
        tgc_data = read_tgc_file(file_timestamp, rf_timestamps)
    else:
        tgc_data = read_tgc_file_v2(file_timestamp, rf_timestamps)

    if tgc_data == None:
        return generate_default_tgc_matrix(num_frames)

    tgc_matrix = np.zeros((len(tgc_data), num_samples))
    depths_mm = np.linspace(0, image_depth_mm, num_samples)

    for i, frame in enumerate(tgc_data):
        mm_values = [float(x) for x in re.findall(r"{ (.*?)mm,", frame)]
        dB_values = [float(x) for x in re.findall(r", (.*?)dB }", frame)]
        fill_value = (dB_values[0], dB_values[-1])
        interpolation_func = interp1d(
            mm_values, dB_values, bounds_error=False, fill_value=fill_value
        )
        tgc_matrix[i, :] = interpolation_func(depths_mm)

    tgc_matrix_transpose = tgc_matrix.T
    linear_tgc_matrix_transpose = 10 ** (tgc_matrix_transpose / 20)
    linear_tgc_matrix_transpose = linear_tgc_matrix_transpose[None, ...]
    linear_tgc_matrix_transpose = np.repeat(linear_tgc_matrix_transpose, 192, axis=0)

    print(
        "A TGC matrix of size {} is generated for {} timestamp ".format(
            linear_tgc_matrix_transpose.shape, file_timestamp
        )
    )
    #     for depth, tgc_value in zip(depths_mm, tgc_matrix[0]):
    #         print(f"Depth: {depth:.2f}mm, TGC: {tgc_value:.2f}dB")

    return linear_tgc_matrix_transpose

def convert_env_to_rf_ntgc(x, linear_tgc_matrix):
    y1 =  47.3 * x + 30
    y = 10**(y1/20)-1
    y = y / linear_tgc_matrix
    return y 

def convert_rf_to_env(x):
    x[x< 0] = 0
    y = 20 * np.log10(x + 1)
    y = (y - 30)/ 47.3
    return y

def convert_env_to_rf(x):
    y1 =  47.3 * x + 30
    y = 10**(y1/20)-1
    return y


def PRead_Clarius_TGC_Correct(filename, version="6.0.3", isPhantom=False):
    """Read RF data contained in Clarius file
    Args:
        filename (string)): where is the Clarius file
        version (str, optional): indicates Clarius file version. Defaults to '6.0.3'. Currently not used.
        isPhantom (bool, optional): indicated if it is phantom (True) or patient data (False)

    Returns:
        numpy.ndarray: Corrected RF data processed from RF data contained in filename (depth: 2928, width: 192, nframes)
    """

    if version != "6.0.3":
        print("Unrecognized version")
        return []

    # Some Initilization
    studyID = filename[1 : (len(filename) - 4)]
    # studyEXT = filename[(len(filename) - 2) :]
    filenameEnv = filename.replace("rf", "env")
    dataEnv = 0
    # filename ='Phantom/extracted/2019-08-22T00-41-10+0000_rf.raw'
    phantom_bucket = storage_client.get_bucket(config.clarius.PHANTOM_BUCKET)
    # get from google
    if isPhantom:
        while True:
            try:
                temp = storage.blob.Blob(filename, phantom_bucket)
                content = temp.download_as_string()
                tempEnv = storage.blob.Blob(filenameEnv, phantom_bucket)
                contentEnv = tempEnv.download_as_string()
                break
            except:
                print("\t\tfile load error")
                logging.warning("File load error")
                pass
    else:
        while True:
            try:
                temp = storage.blob.Blob(filename, globals.bucket_pull_DSP_Part1)
                content = temp.download_as_string()
                tempEnv = storage.blob.Blob(filenameEnv, globals.bucket_pull_DSP_Part1)
                contentEnv = tempEnv.download_as_string()
                break
            except:
                print("\t\tfile load error")
                logging.warning("File load error")
                pass
    # write to temp file, then use temp file
    if isPhantom == True:
        tempFile4 = "temp_files/tempFile4_Phantom"
        tempFile4Env = "temp_files/tempFile4" + studyID[27:] + 'env'
    else:
        tempFile4 = "temp_files/tempFile4" + studyID[27:]
        tempFile4Env = "temp_files/tempFile4" + studyID[27:] + 'env'

    fpoint = open(tempFile4, "wb")
    fpoint.write(content)
    fpoint.close()
 
    if isPhantom != True:
        fpointEnv = open(tempFile4Env, "wb")
        fpointEnv.write(contentEnv)
        fpointEnv.close()
        hdr, timestamps, dataEnv = read_env(tempFile4Env)
    else:
        fpointEnv = open(tempFile4Env, "wb")
        fpointEnv.write(contentEnv)
        fpointEnv.close()
        hdr, timestamps, dataEnv = read_env(tempFile4Env)            

    while True:
        try:
            fid = open(tempFile4, mode="rb")
            break
        except:
            print("\t\terror opening ", tempFile4)
            logging.warning("Error opening ", tempFile4)
            pass

    # read the header info
    hinfo = np.fromfile(
        fid, dtype="uint32", count=5
    )  # int32 and uint32 appear to be equivalent in memory -> a = np.int32(1); np.dtype(a).itemsize
    header = {"id": 0, "nframes": 0, "w": 0, "h": 0, "ss": 0}
    header["id"] = hinfo[0]
    header["nframes"] = hinfo[1]  # frames
    header["w"] = hinfo[2]  # lines
    header["h"] = hinfo[3]  # samples
    header["ss"] = hinfo[4]  # sampleSize

    # % ADDED BY AHMED EL KAFFAS - 22/09/2018
    frames = header["nframes"]

    id = header["id"]
    if id == 2:  # RF
        ts = np.zeros(shape=(frames,), dtype="uint64")
        data = np.zeros(shape=(header["h"], header["w"], frames))
        #  read RF data
        for f in range(frames):
            ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
            v = np.fromfile(fid, count=header["h"] * header["w"], dtype="int16")
            data[:, :, f] = np.flip(
                v.reshape(header["h"], header["w"], order="F").astype(np.int16), axis=1
            )
    #######################################################################################################
    else:
        print(
            "The file does not contain RF data. Make sure RF mode is turned on while taking scans."
        )
        return []

    # Pseudocode
    # 1) Set a config flag to allow for 188 lines
    if config.debugging_mode.special_datasets['allow_184_lines'] == 1:
        if header["w"] == 184:
            # Reflect columns 2 through 5 across column 1
            left_edge = np.flip(data[:, 1:5, :], axis=1)

            # Reflect columns 180-183 across column 184
            right_edge = np.flip(data[:, 179:183, :], axis=1)

            # Concatenate the original array with the reflected sections
            data = np.hstack((left_edge, data, right_edge))
            header["w"] = 192

    # delete temp file
    try:
        os.remove(tempFile4)
        if isPhantom != True:
            os.remove(tempFile4Env)
    except OSError:
        print("\t\terror opening ", tempFile4)
        logging.warning("Error deleting ", tempFile4)
        pass

    # Check if the ROI is full
    if header["w"] != 192 or header["h"] != 2928:
        print(
            "The ROI is not full. The size of RF matrix is {}*{} thus returning an empty list.".format(
                header["w"], header["h"]
            )
        )
        return []

    data = data.astype(np.float64)
    file_timestamp = filename.split("_rf.raw")[0]
    linear_tgc_matrix = generate_tgc_matrix(file_timestamp, ts, header["nframes"],isPhantom)
    linear_tgc_matrix = np.transpose(linear_tgc_matrix, (1, 0, 2))

    if data.shape[2] != linear_tgc_matrix.shape[2]:
        print(
            "\033[31m"
            + "The timestamps for file_timestamp {} does not match between rf.raw and tgc file. Skipping this scan and returning an empty array.".format(
                file_timestamp
            )
            + "\033[0m"
        )
        return []

    rf_matrix_corrected_B = data / linear_tgc_matrix

    linear_default_tgc_matrix = generate_default_tgc_matrix(header["nframes"])
    linear_default_tgc_matrix = np.transpose(linear_default_tgc_matrix, (1, 0, 2))
    rf_matrix_corrected_A = rf_matrix_corrected_B * linear_default_tgc_matrix
    dB_tgc_matrix = 20*np.log10(linear_tgc_matrix)
    rf_ntgc = rf_matrix_corrected_B
    rf_dtgc = rf_matrix_corrected_A
    rf_atgc = data

    rf_atgc, rf_dtgc, rf_ntgc, dataEnv, dB_tgc_matrix = checkLengthEnvRF(rf_atgc,rf_dtgc,rf_ntgc,dataEnv,dB_tgc_matrix)
    linear_tgc_matrix = linear_tgc_matrix[0:dB_tgc_matrix.shape[0],0:dB_tgc_matrix.shape[1],0:dB_tgc_matrix.shape[2]]

    dataEnvL = convert_env_to_rf_ntgc(dataEnv, linear_tgc_matrix) # Linear scale env data without tgc, used in statmaps env

    return rf_atgc, rf_dtgc, rf_ntgc, dataEnv,dB_tgc_matrix, dataEnvL


# def PRead_Clarius_TGC_Correct_local(filename, version="6.0.3", isPhantom=False):
#     """Read RF data contained in Clarius file from local storage and apply TGC correction
#     Args:
#         filename (string)): where is the Clarius file
#         version (str, optional): indicates Clarius file version. Defaults to '6.0.3'. Currently not used.
#         isPhantom (bool, optional): indicated if it is phantom (True) or patient data (False)

#     Returns:
#         numpy.ndarray: Corrected RF data processed from RF data contained in filename (depth: 2928, width: 192, nframes)
#     """
#     dataEnv = []

#     if version != "6.0.3":
#         print("Unrecognized version")
#         return []

#     # Some Initilization
#     # studyID = filename[1 : (len(filename) - 4)]
#     # studyEXT = filename[(len(filename) - 2) :]
#     # filenameEnv = filename.replace("rf", "env")
#     # dataEnv = 0
#     # filename ='Phantom/extracted/2019-08-22T00-41-10+0000_rf.raw'
#     # phantom_bucket = storage_client.get_bucket(config.clarius.PHANTOM_BUCKET)
#     # get from google

#     # write to temp file, then use temp file
#     tempFile4 = filename
#     tempFile4Env = tempFile4.replace("rf", "env")
#     while True:
#         try:
#             fid = open(tempFile4, mode="rb")
#             break
#         except:
#             print("\t\terror opening ", tempFile4)
#             logging.warning("Error opening ", tempFile4)
#             pass

#     if config.controls.VERSION == "product/0.3.3" or config.controls.VERSION == "product/0.4.0" or config.controls.VERSION == "product/0.4.1.6":
#         if isPhantom != True:
#             hdr, timestamps, dataEnv = read_env(tempFile4Env)

#     # read the header info
#     hinfo = np.fromfile(
#         fid, dtype="uint32", count=5
#     )  # int32 and uint32 appear to be equivalent in memory -> a = np.int32(1); np.dtype(a).itemsize
#     header = {"id": 0, "nframes": 0, "w": 0, "h": 0, "ss": 0}
#     header["id"] = hinfo[0]
#     header["nframes"] = hinfo[1]  # frames
#     header["w"] = hinfo[2]  # lines
#     header["h"] = hinfo[3]  # samples
#     header["ss"] = hinfo[4]  # sampleSize

#     # % ADDED BY AHMED EL KAFFAS - 22/09/2018
#     frames = header["nframes"]

#     id = header["id"]
#     if id == 2:  # RF
#         ts = np.zeros(shape=(frames,), dtype="uint64")
#         data = np.zeros(shape=(header["h"], header["w"], frames))
#         #  read RF data
#         for f in range(frames):
#             ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
#             v = np.fromfile(fid, count=header["h"] * header["w"], dtype="int16")
#             data[:, :, f] = np.flip(
#                 v.reshape(header["h"], header["w"], order="F").astype(np.int16), axis=1
#             )
#     #######################################################################################################
#     else:
#         print(
#             "The file does not contain RF data. Make sure RF mode is turned on while taking scans."
#         )
#         return []

#     # delete temp file
#     # try:
#     #     os.remove(tempFile4)
#     #     if isPhantom != True:
#     #         os.remove(tempFile4Env)
#     # except OSError:
#     #     print("\t\terror opening ", tempFile4)
#     #     logging.warning("Error deleting ", tempFile4)
#     #     pass

#     # Check if the ROI is full
#     if header["w"] != 192 or header["h"] != 2928:
#         print(
#             "The ROI is not full. The size of RF matrix is {}*{} thus returning an empty list.".format(
#                 header["w"], header["h"]
#             )
#         )
#         return []

#     data = data.astype(np.float64)
#     file_timestamp = filename.split("_rf.raw")[0]

#     linear_tgc_matrix = generate_tgc_matrix(file_timestamp, ts, header["nframes"])
#     linear_tgc_matrix = np.transpose(linear_tgc_matrix, (1, 0, 2))

#     if data.shape[2] != linear_tgc_matrix.shape[2]:
#         print(
#             "\033[31m"
#             + "The timestamps for file_timestamp {} does not match between rf.raw and tgc file. Skipping this scan and returning an empty array.".format(
#                 file_timestamp
#             )
#             + "\033[0m"
#         )
#         return []

#     rf_matrix_corrected_B = data / linear_tgc_matrix

#     linear_default_tgc_matrix = generate_default_tgc_matrix(header["nframes"])
#     linear_default_tgc_matrix = np.transpose(linear_default_tgc_matrix, (1, 0, 2))
#     rf_matrix_corrected_A = rf_matrix_corrected_B * linear_default_tgc_matrix
#     rf_ntgc = rf_matrix_corrected_B  # corrected tgc
#     rf_dtgc = rf_matrix_corrected_A  # simulating default tgc
#     rf_atgc = data  # no correction at all
#     dB_tgc_matrix = 20*np.log10(linear_default_tgc_matrix)
#     return rf_atgc, rf_dtgc, rf_ntgc, dataEnv, dB_tgc_matrix


# read env data
def read_env(filename):
    hdr_info = ("id", "frames", "lines", "samples", "samplesize")
    hdr, timestamps, data = {}, None, None
    with open(filename, "rb") as raw_bytes:
        # read 4 bytes header
        for info in hdr_info:
            hdr[info] = int.from_bytes(raw_bytes.read(4), byteorder="little")
        # read timestamps and data
        timestamps = np.zeros(hdr["frames"], dtype="int64")
        sz = hdr["lines"] * hdr["samples"] * hdr["samplesize"]
        data = np.zeros((hdr["lines"], hdr["samples"], hdr["frames"]), dtype="uint8")
        for frame in range(hdr["frames"]):
            # read 8 bytes of timestamp
            timestamps[frame] = int.from_bytes(raw_bytes.read(8), byteorder="little")
            # read each frame
            data[:, :, frame] = np.frombuffer(
                raw_bytes.read(sz), dtype="uint8"
            ).reshape([hdr["lines"], hdr["samples"]])
    print(
        "Loaded {d[2]} raw frames of size, {d[0]} x {d[1]} (lines x samples)".format(
            d=data.shape
        )
    )
    target_shape = (2928, 192)
    dataEnv = np.transpose(data, [1, 0, 2])
    data = np.zeros([2928, 192, dataEnv.shape[2]])
    for ii in range(0, dataEnv.shape[2]):
        data[:, :, ii] = skimage.transform.resize(
            dataEnv[:, :, ii], target_shape, anti_aliasing=True
        )
    data = np.flip(data, axis=1)
    return hdr, timestamps, data


# def PRead_Clarius(filename, version="6.0.3", isPhantom=False):
#     """Read RF data contained in Clarius file

#     Args:
#         filename (string)): where is the Clarius file
#         version (str, optional): indicates Clarius file version. Defaults to '6.0.3'. Currently not used.
#         isPhantom (bool, optional): indicated if it is phantom (True) or patient data (False)

#     Returns:
#         numpy.ndarray: RF data contained in filename (depth: 2928, width: 192, nframes)
#     """

#     if version != "6.0.3":
#         print("Unrecognized version")
#         return []

#     # Some Initilization
#     studyID = filename[1 : (len(filename) - 4)]
#     # studyEXT = filename[(len(filename) - 2) :]
#     # filename ='Phantom/extracted/2019-08-22T00-41-10+0000_rf.raw'
#     phantom_bucket = storage_client.get_bucket(config.clarius.PHANTOM_BUCKET)
#     # get from google
#     if isPhantom:
#         while True:
#             try:
#                 temp = storage.blob.Blob(filename, phantom_bucket)
#                 content = temp.download_as_string()
#                 break
#             except:
#                 print("\t\tfile load error")
#                 logging.warning("File load error")
#                 pass
#     else:
#         while True:
#             try:
#                 temp = storage.blob.Blob(filename, globals.bucket_pull_DSP_Part1)
#                 content = temp.download_as_string()
#                 break
#             except:
#                 print("\t\tfile load error")
#                 logging.warning("File load error")
#                 pass
#     # write to temp file, then use temp file
#     if isPhantom == True:
#         tempFile4 = "temp_files/tempFile4_Phantom"
#     else:
#         tempFile4 = "temp_files/tempFile4" + studyID[27:]

#     fpoint = open(tempFile4, "wb")
#     fpoint.write(content)
#     fpoint.close()

#     while True:
#         try:
#             fid = open(tempFile4, mode="rb")
#             break
#         except:
#             print("\t\terror opening ", tempFile4)
#             logging.warning("Error opening ", tempFile4)
#             pass

#     # read the header info
#     hinfo = np.fromfile(
#         fid, dtype="uint32", count=5
#     )  # int32 and uint32 appear to be equivalent in memory -> a = np.int32(1); np.dtype(a).itemsize
#     header = {"id": 0, "nframes": 0, "w": 0, "h": 0, "ss": 0}
#     header["id"] = hinfo[0]
#     header["nframes"] = hinfo[1]  # frames
#     header["w"] = hinfo[2]  # lines
#     header["h"] = hinfo[3]  # samples
#     header["ss"] = hinfo[4]  # sampleSize

#     # % ADDED BY AHMED EL KAFFAS - 22/09/2018
#     frames = header["nframes"]

#     id = header["id"]
#     if id == 0:  # iq
#         ts = np.zeros(shape=(frames,), dtype="uint64")
#         data = np.zeros(shape=(frames, header["h"] * 2, header["w"]))
#         #  read ENV data
#         for f in range(frames):
#             # read time stamp
#             ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
#             # read one line
#             oneline = (
#                 np.fromfile(fid, dtype="int16")
#                 .reshape((header["h"] * 2, header["w"]))
#                 .T
#             )
#             data[f, :, :] = oneline
#     #######################################################################################################
#     elif id == 1:  # env
#         ts = np.zeros(shape=(frames,), dtype="uint64")
#         data = np.zeros(shape=(frames, header["h"], header["w"]))
#         #  read ENV data
#         for f in range(frames):
#             # read time stamp
#             ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
#             # read one line
#             oneline = (
#                 np.fromfile(fid, dtype="uint8").reshape((header["h"], header["w"])).T
#             )
#             data[f, :, :] = oneline
#     #######################################################################################################
#     elif id == 2:  # RF
#         ts = np.zeros(shape=(frames,), dtype="uint64")
#         data = np.zeros(shape=(header["h"], header["w"], frames))
#         #  read RF data
#         for f in range(frames):
#             ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
#             v = np.fromfile(fid, count=header["h"] * header["w"], dtype="int16")
#             data[:, :, f] = np.flip(
#                 v.reshape(header["h"], header["w"], order="F").astype(np.int16), axis=1
#             )
#     #######################################################################################################
#     elif id == 3:
#         ts = np.zeros(shape=(frames,), dtype="uint64")
#         data = np.zeros(shape=(frames, header["h"] * 2, header["w"]))
#         #  read  data
#         for f in range(frames):
#             # read time stamp
#             ts[f] = np.fromfile(fid, dtype="uint64", count=1)[0]
#             # read one line
#             oneline = (
#                 np.fromfile(fid, dtype="int16")
#                 .reshape((header["h"] * 2, header["w"]))
#                 .T
#             )
#             data[f, :, :] = oneline

#     # delete temp file
#     try:
#         os.remove(tempFile4)
#     except OSError:
#         print("\t\terror opening ", tempFile4)
#         logging.warning("Error deleting ", tempFile4)
#         pass

#     return data


def load_all_phantoms():
    srcDirectory = os.path.dirname(os.path.abspath(__file__)) + '/../lib/data_generation'
    sys.path.append(srcDirectory)
    import phantoms_globals as pg

    phantom_bucket = storage_client.get_bucket(config.clarius.PHANTOM_BUCKET)
    # C3 loading
    print("-------------LOADING C3 SLA PHANTOM--------------")
    imgInfo_Phantom = info(
        config.clarius.ID_PHANTOM,
        config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["phantom_file"],
        isPhantom=True,  # change instead config.clarius.PHANTOM_FILE
    )
    D2 = read_Clariusimg_Phantom(imgInfo_Phantom, 1)
    pg.Phantom_C3_sla = D2["RF"]
    pg.Phantom_C3_sla_ssn = D2["RF"]
    pg.Phantom_C3_sla_env = D2["Env"]
    pg.Phantom_C3_sla_envl = D2["EnvLinear"]
    pg.Phantom_C3_sla_atgc = D2["RF_ATGC"]

    '''data_interface.download_from_bucket_to_local(
        phantom_bucket,
        config.clarius.ID_PHANTOM + config.clarius.CLARIUS_C3_TRANSDUCER_SETTINGS["phantom_ssp"],
        "temp_files/" + config.clarius.CLARIUS_C3_TRANSDUCER_SETTINGS["phantom_ssp"],
    )
    pg.PhantomSSP_C3 = np.load(
        "temp_files/" + config.clarius.CLARIUS_C3_TRANSDUCER_SETTINGS["phantom_ssp"]
    )
    os.remove("temp_files/" + config.clarius.CLARIUS_C3_TRANSDUCER_SETTINGS["phantom_ssp"])'''
    #pg.q_to_z_ratio_C3H_sla = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
    #pg.q_to_z_ratio_C3_sla = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
    pg.PhantomPitch_C3_sla = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["pitch"]
    pg.PhantomRadius_C3_sla = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["radius"]
    print("-------------C3 SLA PHANTOM LOADED--------------")

    # C3H
    print("-------------LOADING C3H SLA PHANTOM--------------")
    imgInfo_Phantom = info(
        config.clarius.ID_PHANTOM,
        config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["phantom_file"],
        isPhantom=True,  # change instead config.clarius.PHANTOM_FILE
    )
    D2 = read_Clariusimg_Phantom(imgInfo_Phantom, 1)
    pg.Phantom_C3H_sla = D2["RF"]
    pg.Phantom_C3H_sla_env = D2["Env"]
    pg.Phantom_C3H_sla_envl = D2["EnvLinear"]
    pg.Phantom_C3H_sla_atgc = D2["RF_ATGC"]

    #pg.q_to_z_ratio_C3H_sla = config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
    pg.PhantomPitch_C3H_sla = config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["pitch"]
    pg.PhantomRadius_C3H_sla = config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["radius"]
    print("-------------C3H SLA PHANTOM LOADED--------------")

    # C3v1
    print("-------------LOADING C3 MLA PHANTOM--------------")
    imgInfo_Phantom = info(
        config.clarius.ID_PHANTOM,
        config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["phantom_file"],
        isPhantom=True,  # change instead config.clarius.PHANTOM_FILE
    )
    D2 = read_Clariusimg_Phantom(imgInfo_Phantom, 1)
    pg.Phantom_C3_mla = D2["RF"]
    pg.Phantom_C3_mla_env = D2["Env"]
    pg.Phantom_C3_mla_envl = D2["EnvLinear"]
    pg.Phantom_C3_mla_atgc = D2["RF_ATGC"]

    #pg.q_to_z_ratio_C3_mla = config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
    pg.PhantomPitch_C3_mla = config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["pitch"]
    pg.PhantomRadius_C3_mla = config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["radius"]
    print("-------------C3 MLA PHANTOM LOADED--------------")



def load_all_phantoms_speedUp(phantom,name):
        #This need to be changed to a particular globals variable for each phantom

        print("\t----- START PRECOMPUTES SPEED UP FOR "+name+"-----")

        srcDirectory = os.path.dirname(os.path.abspath(__file__)) + '/..'
        sys.path.append(srcDirectory)
        import configSpeedUp
        
        srcDirectory = os.path.dirname(os.path.abspath(__file__)) + '/../lib/data_generation'
        sys.path.append(srcDirectory)
        import qus_calc
        import phantoms_globals as pg
         
        if name == 'Phantom_c3_sla':
            fs = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["fs"]
            globals.PhantomC = pg.Phantom_C3_sla
            globals.PhantomC_ssn = pg.Phantom_C3_sla_ssn
            globals.PhantomEnv = pg.Phantom_C3_sla_env
            globals.PhantomEnvL = pg.Phantom_C3_sla_envl
            globals.PhantomATGC = pg.Phantom_C3_sla_atgc

            #print('REFERENCE C3 SLA PHANTOM', globals.PhantomC)
            globals.transducer["pitch"] = pg.PhantomPitch_C3_sla
            globals.transducer["radius"] = pg.PhantomRadius_C3_sla
            #globals.q_to_z_ratio =config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
            #globals.PhantomSSP = pg.PhantomSSP_C3

        elif name == 'Phantom_c3_mla':
            fs = config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["fs"]
            globals.PhantomC = pg.Phantom_C3_mla
            globals.PhantomC_ssn = pg.Phantom_C3_mla
            globals.PhantomEnv = pg.Phantom_C3_mla_env
            globals.PhantomEnvL = pg.Phantom_C3_mla_envl
            globals.PhantomATGC = pg.Phantom_C3_mla_atgc

            #print('REFERENCE C3 MLA PHANTOM', globals.PhantomC)
            globals.transducer["pitch"] = pg.PhantomPitch_C3_mla
            globals.transducer["radius"] = pg.PhantomRadius_C3_mla
            #globals. q_to_z_ratio = config.clarius.CLARIUS_C3_MLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
            #globals.PhantomSSP = pg.PhantomSSP_C3H
        
        elif name == 'Phantom_c3H_sla':
            fs = config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["fs"]
            globals.PhantomC = pg.Phantom_C3H_sla
            globals.PhantomC_ssn = pg.Phantom_C3H_sla
            globals.PhantomEnv = pg.Phantom_C3H_sla_env
            globals.PhantomEnvL = pg.Phantom_C3H_sla_envl
            globals.PhantomATGC = pg.Phantom_C3H_sla_atgc

            #print('REFERENCE C3H SLA PHANTOM', globals.PhantomC)
            globals.transducer["pitch"] = pg.PhantomPitch_C3H_sla
            globals.transducer["radius"] = pg.PhantomRadius_C3H_sla
            #globals.q_to_z_ratio = config.clarius.CLARIUS_C3H_SLA_TRANSDUCER_SETTINGS["q_to_z_ratio_O_alpha2b"]
            #globals.PhantomSSP = pg.PhantomSSP_C3
        else:
            fs = config.clarius.CLARIUS_C3_SLA_TRANSDUCER_SETTINGS["fs"]
            globals.PhantomC = pg.Phantom_C3_mla
            globals.PhantomC_ssn = pg.Phantom_C3_mla
            globals.PhantomEnv = pg.Phantom_C3_mla_env
            globals.PhantomEnvL = pg.Phantom_C3H_mla_envl
            globals.PhantomATGC = pg.Phantom_C3H_mla_atgc

        Iin = np.zeros((config.segmentation.SEGM_LEN_AXIAL, config.segmentation.SEGM_LEN_LATERAL))
        scanConvert = ScanConvertAccelerated(Iin=Iin)
        scanConvert.precompute_scanconvert()
        globals.fs = fs
        wvl_samples = (fs / config.signal_processing_alpha3_parameter.freq * 2) 
        depth = 2 * int(int(10 * wvl_samples) / 2)
        depthov = int(2.5 * wvl_samples) 
        depth_att = depth
        depth_window_att = int(3 * depth_att)
        depth_alpha2 = 2 * int(int(10 * wvl_samples) / 2)
        #ham_alpha2 = scipy.signal.hamming(depth_alpha2).reshape((depth_alpha2, 1))
        #ham_alpha2_7p5wvl = scipy.signal.hamming(int(depth_alpha2 * 0.75)).reshape((int(depth_alpha2 * 0.75), 1))
        depth_ps = depth
        globals.Nfft_ps = int(np.power(2, np.ceil(np.log(config.signal_processing_alpha3_parameter.ovfft_ps * depth_ps) / np.log(2))))

        globals.b = (depth) 
        globals.c = (config.signal_processing_alpha3_parameter.width) 
        globals.bov = math.floor(depthov)
        globals.cov = math.floor(config.signal_processing_alpha3_parameter.widthov)
        globals.bb = (depth_window_att)
        globals.SYSTEM_SCALING = config.clarius.SYSTEM_SCALING
        #globals.ham_alpha2 = ham_alpha2
        #globals.ham_alpha2_7p5wvl = ham_alpha2_7p5wvl
        globals.bend = globals.bstart + globals.b
        globals.cstart = -int(globals.c / 2)
        globals.lc = -globals.cstart
        globals.cend = globals.cstart + globals.c
        globals.qaov = int((globals.sz - globals.b) / globals.bov) + 1
        globals.wloov = (
                #int((np.shape(r)[1] - c) / cov) + 1
                int((192 - globals.c) / globals.cov) + 1 
        ) 
        globals.b7p5wvl = int(globals.b * 0.75)
        globals.b_5wvl = int(globals.b / 2)
        globals.b_7p5wvl = int(globals.b * 0.75)
        #Phantom variables for attenuation AttenuationCalculation_Alpha3_ext
        globals.bendBB = globals.bstart + globals.bb
        globals.qaovBB = int((globals.sz - globals.bb) /globals.bov) + 1
        globals.phantrf = configSpeedUp.phantomPrecompute(phantom)
        globals.phantrfAtenn = configSpeedUp.phantomPrecomputeAtte(phantom)
        globals.pPSWelch = qus_calc.welchperiodogram(globals.phantrf[:, :, :], 1) 
        globals.pPSWelch_7p5wvl = qus_calc.welchperiodogram(globals.phantrf [:,int(globals.b / 2 - globals.b7p5wvl / 2) : int(globals.b / 2 + globals.b7p5wvl / 2),int(globals.c / 2 - globals.c_4lines / 2) : int(globals.c / 2 + globals.c_4lines / 2),],7.5,) 
        globals.pPSRec = configSpeedUp.pPSRecFun(globals.phantrf)
        globals.pPSRec_5wvl = configSpeedUp.pPSRec_5wvlFunc(globals.phantrf)
        #try:
        #    globals.pPSHam = configSpeedUp.pPSHamFunc(globals.phantrf)
        #except:
        #    print("hi")
        #globals.pPSHam_7p5wvl = configSpeedUp.pPSHam_7p5wvlFunc(globals.phantrf)
        globals.pPSRec2 = np.abs(globals.pPSRec[:, 0 : int(np.floor(np.shape(globals.pPSRec)[1] / 2)), :])
        globals.pPSRec2_5wvl = np.abs(globals.pPSRec_5wvl[:, 0 : int(np.floor(np.shape(globals.pPSRec_5wvl)[1] / 2)), :])
        globals.pPSpx = np.mean(qus_calc.welchperiodogram(globals.phantrfAtenn[:, 0:depth_att, :], 3), axis= 2)
        globals.pPSds = np.mean(qus_calc.welchperiodogram(globals.phantrfAtenn[:, -depth_att:, :], 3), axis=2)
        #if config.DSP_Part1_active_computations['ps2'] == True:
        phantrfPs2 = globals.phantrf * config.clarius.SYSTEM_SCALING
        globals.phantrfPs2 = phantrfPs2[:, :, int(globals.c / 2 - 2) : int(globals.c / 2 + 2)] / config.clarius.SYSTEM_SCALING
        globals.pPSWelchPs2 = qus_calc.welchperiodogram(globals.phantrfPs2, 1)
        globals.Sxxp1, globals.Sxxp2 = configSpeedUp.spectrogramPs2()
        #Above this point until the if are the precomputes for 'ps2'
        pg.save_data_speedUp_precomputes(globals.precompute_scanconvert,globals.b,globals.c,globals.bov,globals.cov,globals.bb,globals.SYSTEM_SCALING,
                                  #ham_alpha2, ham_alpha2_7p5wvl,
                                  globals.bend,globals.cstart,globals.lc,globals.cend,globals.qaov,globals.wloov,
                                  globals.b7p5wvl,globals.b_5wvl,globals.b_7p5wvl,globals.bendBB,globals.qaovBB,globals.pPSWelch_7p5wvl,
                                  globals.phantrf,globals.pPSWelch,globals.pPSRec,globals.pPSRec_5wvl,#globals.pPSHam,globals.pPSHam_7p5wvl,
                                  globals.pPSRec2,globals.pPSRec2_5wvl,globals.phantrfAtenn,globals.pPSpx,globals.pPSds,globals.phantrfPs2,
                                  globals.pPSWelchPs2,fs,globals.Nfft_ps,globals.Sxxp1,globals.Sxxp2,globals.PhantomC, globals.PhantomEnv,
                                  globals.PhantomEnvL, globals.PhantomATGC, globals.PhantomC_ssn)#,globals.PhantomSSP)
        
        print("\t----- FINISHED PRECOMPUTES SPEED UP FOR  "+name+"-----")