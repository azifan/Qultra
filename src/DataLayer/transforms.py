import numpy as np
import pyvista as pv
import scipy.interpolate as interpolate
from numpy.matlib import repmat

class OutImStruct():
    def __init__(self):
        self.scArr = None
        self.preScArr = None
        self.xmap = None # sc (y,x) --> preSC x
        self.ymap = None # sc (y,x) --> preSC y

def rgbtoint32(rgb):
    color = 0
    for c in rgb[::-1]:
        color = (color<<8) + c
    return color

def int32torgb(color):
    rgb = []
    for _ in range(3):
        rgb.append(color&0xff)
        color = color >> 8
    return rgb

def condenseArr(image: np.ndarray) -> np.ndarray:
    """Condense (M,N,3) arr to (M,N) with uint32 data to preserve info"""
    assert len(image.shape) == 3
    assert image.shape[-1] == 3
    
    condensedArr = np.zeros((image.shape[0], image.shape[1])).astype('uint32')
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            condensedArr[i,j] = rgbtoint32(image[i,j])
    
    return condensedArr

def expandArr(image: np.ndarray) -> np.ndarray:
    """Inverse of condenseArr"""
    assert len(image.shape) == 2
    
    fullArr = np.zeros((image.shape[0], image.shape[1], 3))
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            fullArr[i,j] = int32torgb(image[i,j])

    return fullArr.astype('uint8')

def scanConvert(inIm, width, tilt, startDepth, stopDepth, desiredHeight=500):
    # ScanConvert sector image
    # Inputs:
    #      InIm          Input image
    #      Width         Sector width of input image in degrees 
    #      Tilt          Tilt of sector image in degrees  
    #      StartDepth    Axial depth of first sample in meters 
    #      EndDepth      Axial depth of last sample in meters   
    #      DesiredHeight Desired vertical size of output image in pixels 
    #      (default 500)
    # 
    #    Outputs:
    #      OutIm         Output (scanconverted) image(s)  
    #      HCm,WCm       Height and Width of image in centimeters 

    #Convert to radians
    samples, beams = inIm.shape
    depthIncrement = (stopDepth-startDepth)/(samples - 1)
    startAngle = np.deg2rad(270 + tilt - width/2)
    angleIncrement = np.deg2rad(width)/(beams-1)

    outIm = inIm
    background = 0
    height = desiredHeight

    # Subtract 180 degrees to get transudcer in top of image if startAngle > pi
    startAngle = startAngle % np.pi
    stopAngle = startAngle + np.deg2rad(width)
    angleRange = np.arange(startAngle, stopAngle+angleIncrement, angleIncrement)

    # Define physical limits of image
    xmin = -1*max(np.cos(startAngle)*np.array([startDepth, stopDepth]))
    xmax = -1*min(np.cos(stopAngle)*np.array([startDepth, stopDepth]))
    ymin = min(np.sin(angleRange)*startDepth)
    ymax = max(np.sin(angleRange)*stopDepth)
    widthScale = abs((xmax-xmin)/(ymax-ymin))
    width = int(np.ceil(height*widthScale))

    heightCm = (ymax-ymin)*100
    widthCm = (xmax-xmin)*100

    # Make (x,y)-plane representation of physical image
    xmat = (np.transpose(np.ones((1, height)))*np.arange(0, width, 1))/(width-1)
    ymat = (np.transpose(np.arange(0, height, 1).reshape((1, height)))*np.ones((1, width)))/(height-1)
    xmat = (xmat*(xmax-xmin)) + xmin
    ymat = (ymat*(ymax-ymin)) + ymin

    # Transform into polar coordinates (angle, range)
    anglemat = np.arctan2(ymat, -1*xmat)
    rmat = np.sqrt((xmat**2) + (ymat**2))

    # Convert phys. angle and range into beam and sample
    anglemat = np.ceil((anglemat - startAngle)/angleIncrement)
    rmat = np.ceil((rmat - startDepth)/depthIncrement)

    # Find pixels outside active sector
    backgr = np.argwhere((rmat<1))
    backgr = np.concatenate((backgr, np.argwhere(rmat>=samples)), axis=0)
    backgr = np.concatenate((backgr, np.argwhere(anglemat<1)), axis=0)
    backgr = np.concatenate((backgr, np.argwhere(anglemat>beams)), axis=0)
    scMap = (anglemat-1)*samples + rmat

    for i in range(backgr.shape[0]):
        scMap[backgr[i,0],backgr[i,1]] = background
    inIm_indx = repmat(np.arange(0, outIm.shape[1]), int(outIm.shape[0]), 1) # <-- maps (y,x) in Iin to indt in Iin
    inIm_indy = np.transpose(repmat(np.arange(0, outIm.shape[0]), int(outIm.shape[1]), 1)) # <-- maps (y,x) in Iout to indr in Iin
        
    outIm = np.append(np.transpose(outIm), background)
    inIm_indy = np.append(np.transpose(inIm_indy), background)
    inIm_indx = np.append(np.transpose(inIm_indx), background)

    scMap = np.array(scMap).astype(np.uint64) - 1
    outIm = outIm[scMap]
    inIm_indy = inIm_indy[scMap]
    inIm_indx = inIm_indx[scMap]

    outIm = np.reshape(outIm, (height, width))
    inIm_indy = np.reshape(inIm_indy, (height, width))
    inIm_indx = np.reshape(inIm_indx, (height, width))
    
    hCm = heightCm
    wCm = widthCm
    
    OutIm = OutImStruct()
    OutIm.scArr = outIm
    OutIm.preScArr = inIm
    OutIm.ymap = inIm_indy
    OutIm.xmap = inIm_indx
    return OutIm, hCm, wCm

def removeDuplicates(ar):
    # Credit: https://stackoverflow.com/questions/480214/how-do-i-remove-duplicates-from-a-list-while-preserving-order
    seen = set()
    seenAdd = seen.add
    return [x for x in ar if not (tuple(x) in seen or seenAdd(tuple(x)))]

def calculateSpline(xpts, ypts):  # 2D spline interpolation
    cv = []
    for i in range(len(xpts)):
        cv.append([xpts[i], ypts[i]])
    cv = np.array(cv)
    if len(xpts) == 2:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=1)
    elif len(xpts) == 3:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=2)
    else:
        tck, _ = interpolate.splprep(cv.T, s=0.0, k=3)
    x, y = np.array(interpolate.splev(np.linspace(0, 1, 1000), tck))
    return x, y


def ellipsoidFitLS(pos):
    # centre coordinates on origin
    pos = pos - np.mean(pos, axis=0)

    # build our regression matrix
    A = pos**2

    # vector of ones
    Ones = np.ones(len(A))

    # least squares solver
    B, _, _, _ = np.linalg.lstsq(A, Ones, rcond=None)

    # solving for a, b, c
    a_ls = np.sqrt(1.0 / B[0])
    b_ls = np.sqrt(1.0 / B[1])
    c_ls = np.sqrt(1.0 / B[2])

    return (a_ls, b_ls, c_ls)


def calculateSpline3D(points):
    # Calculate ellipsoid of best fit
    # points = np.array(points)
    # a,b,c = ellipsoidFitLS(points)
    # output = set()

    # u = np.linspace(0., np.pi*2., 1000)
    # v = np.linspace(0., np.pi, 1000)
    # u, v = np.meshgrid(u,v)

    # x = a*np.cos(u)*np.sin(v)
    # y = b*np.sin(u)*np.sin(v)
    # z = c*np.cos(v)

    # # turn this data into 1d arrays
    # x = x.flatten()
    # y = y.flatten()
    # z = z.flatten()
    # x += np.mean(points, axis=0)[0]
    # y += np.mean(points, axis=0)[1]
    # z += np.mean(points, axis=0)[2]

    # for i in range(len(x)):
    #     output.add((int(x[i]), int(y[i]), int(z[i])))
    # return output

    cloud = pv.PolyData(points, force_float=False)
    volume = cloud.delaunay_3d(alpha=100.0)
    shell = volume.extract_geometry()
    final = shell.triangulate()
    final.smooth(n_iter=1000)
    faces = final.faces.reshape((-1, 4))
    faces = faces[:, 1:]
    arr = final.points[faces]

    arr = np.array(arr)

    output = set()
    for tri in arr:
        slope_2 = tri[2] - tri[1]
        start_2 = tri[1]
        slope_3 = tri[0] - tri[1]
        start_3 = tri[1]
        for i in range(100, -1, -1):
            bound_one = start_2 + ((i / 100) * slope_2)
            bound_two = start_3 + ((i / 100) * slope_3)
            cur_slope = bound_one - bound_two
            cur_start = bound_two
            for j in range(100, -1, -1):
                cur_pos = cur_start + ((j / 100) * cur_slope)
                output.add((int(cur_pos[0]), int(cur_pos[1]), int(cur_pos[2])))

    return output