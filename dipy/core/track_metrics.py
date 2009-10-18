''' Metrics for tracks, where tracks are arrays of points '''

import math
import numpy as np
import mdp


def length(xyz, along=False):
    ''' Euclidean length of track line

    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    along : bool, optional
       If True, return array giving cumulative length along track,
       otherwise (default) return scalar giving total length.

    Returns
    -------
    L : scalar or array shape (N-1,)
       scalar in case of `along` == False, giving total length, array if
       `along` == True, giving cumulative lengths.

    Examples
    --------
    >>> xyz = np.array([[1,1,1],[2,3,4],[0,0,0]])
    >>> expected_lens = np.sqrt([1+2**2+3**2, 2**2+3**2+4**2])
    >>> length(xyz) == expected_lens.sum()
    True
    >>> len_along = length(xyz, along=True)
    >>> np.allclose(len_along, expected_lens.cumsum())
    True
    >>> length([])
    0
    >>> length([[1, 2, 3]])
    0
    >>> length([], along=True)
    array([0])
    '''
    xyz = np.asarray(xyz)
    if xyz.shape[0] < 2:
        if along:
            return np.array([0])
        return 0
    dists = np.sqrt((np.diff(xyz, axis=0)**2).sum(axis=1))
    if along:
        return np.cumsum(dists)
    return np.sum(dists)


def midpoint(xyz):
    ''' Midpoint of track line

    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track

    Returns
    -------
    mp : array shape (3,)
       Middle point of line, such that, if L is the line length then
       `np` is the point such that the length xyz[0] to `mp` and from
       `mp` to xyz[-1] is L/2.  If the middle point is not a point in
       `xyz`, then we take the interpolation between the two nearest
       `xyz` points.  If `xyz` is empty, return a ValueError

    Examples
    --------
    >>> midpoint([])
    Traceback (most recent call last):
       ...
    ValueError: xyz array cannot be empty
    >>> midpoint([[1, 2, 3]])
    array([1, 2, 3])
    >>> xyz = np.array([[1,1,1],[2,3,4]])
    >>> midpoint(xyz)
    array([ 1.5,  2. ,  2.5])
    >>> xyz = np.array([[0,0,0],[1,1,1],[2,2,2]])
    >>> midpoint(xyz)
    array([ 1.,  1.,  1.])
    >>> xyz = np.array([[0,0,0],[1,0,0],[3,0,0]])
    >>> midpoint(xyz)
    array([ 1.5,  0. ,  0. ])
    >>> xyz = np.array([[0,9,7],[1,9,7],[3,9,7]])
    >>> midpoint(xyz)
    array([ 1.5,  9. ,  7. ])
    '''
    xyz = np.asarray(xyz)
    n_pts = xyz.shape[0]
    if n_pts == 0:
        raise ValueError('xyz array cannot be empty')
    if n_pts == 1:
        return xyz.copy().squeeze()
    cumlen = np.zeros(n_pts)
    cumlen[1:] = length(xyz, along=True)
    midlen=cumlen[-1]/2.0
    ind=np.where((cumlen-midlen)>0)[0][0]
    len0=cumlen[ind-1]        
    len1=cumlen[ind]
    Ds=midlen-len0
    Lambda = Ds/(len1-len0)
    return Lambda*xyz[ind]+(1-Lambda)*xyz[ind-1]


def center_of_mass(xyz):
    ''' Center of mass of streamline

    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track

    Returns
    -------
    com : array shape (3,)
       center of mass of streamline

    Examples
    --------
    >>> center_of_mass([])
    Traceback (most recent call last):
       ...
    ValueError: xyz array cannot be empty
    >>> center_of_mass([[1,1,1]])
    array([ 1.,  1.,  1.])
    >>> xyz = np.array([[0,0,0],[1,1,1],[2,2,2]])
    >>> center_of_mass(xyz)
    array([ 1.,  1.,  1.])
    '''
    xyz = np.asarray(xyz)
    if xyz.size == 0:
        raise ValueError('xyz array cannot be empty')
    return np.mean(xyz,axis=0)

def magn(xyz,n=1):
    ''' magnitude of vector
        
    '''    
    mag=np.sum(xyz**2,axis=1)**0.5
    imag=np.where(mag==0)
    mag[imag]=np.finfo(float).eps

    if n>1:
        return np.tile(mag,(n,1)).T
    return mag.reshape(len(mag),1)    
    

def frenet_serret(xyz):
    ''' Frenet-Serret Space Curve Invarients
 
    Calculates the 3 vector and 2 scaler invarients of a space curve defined
    by vectors x,y and z.  If z is omitted then the curve is only a 2D,
    but the equations are still valid.
    
    Similar to
    http://www.mathworks.com/matlabcentral/fileexchange/11169

    _    r'
    T = ----  (Tangent)
        |r'|
 
    _    T'
    N = ----  (Normal)
        |T'|
    _   _   _
    B = T x N (Binormal)

    k = |T'|  (Curvature)
 
    t = dot(-B',N) (Torsion)
    
    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    
    
    Returns
    ---------
    T : array shape (N,3)
        array representing the tangent of the curve xyz
    N : array shape (N,3)
        array representing the normal of the curve xyz    
    B : array shape (N,3)
        array representing the binormal of the curve xyz
    k : array shape (N,1)
        array representing the curvature of the curve xyz
    t : array shape (N,1)
        array representing the torsion of the curve xyz

    Examples
    --------
    Create a helix and calculate its tangent,normal, binormal, curvature and torsion
    
    >>> from dipy.core import track_metrics as tm
    >>> import numpy as np
    >>> theta = 2*np.pi*np.linspace(0,2,100)
    >>> x=np.cos(theta)
    >>> y=np.sin(theta)
    >>> z=theta/(2*np.pi)
    >>> xyz=np.vstack((x,y,z)).T
    >>> T,N,B,k,t=tm.frenet_serret(xyz)
    
    '''
    xyz = np.asarray(xyz)
    n_pts = xyz.shape[0]
    if n_pts == 0:
        raise ValueError('xyz array cannot be empty')
    
    dxyz=np.gradient(xyz)[0]        
    
    ddxyz=np.gradient(dxyz)[0]
    
    #Tangent        
    T=np.divide(dxyz,magn(dxyz,3))
    
    #Derivative of Tangent
    dT=np.gradient(T)[0]
    
    #Normal
    N = np.divide(dT,magn(dT,3))
    
    #Binormal
    B = np.cross(T,N)
    
    #Curvature 
    k = magn(np.cross(dxyz,ddxyz),1)/(magn(dxyz,1)**3)    
    
    #Torsion 
    #(In matlab was t=dot(-B,N,2))
    t = np.sum(-B*N,axis=1)
    
    #return T,N,B,k,t,dxyz,ddxyz,dT   
    return T,N,B,k,t
    
def mean_curvature(xyz):    
    ''' Calculates the mean curvature of a curve
    
    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a curve
        
    Returns
    ---------
    m : float 
        float representing the mean curvature
    
    Examples
    --------
    Create a straight line and a semi-circle and print their mean curvatures
    
    >>> from dipy.core import track_metrics as tm
    >>> import numpy as np
    >>> x=np.linspace(0,1,100)
    >>> y=0*x
    >>> z=0*x
    >>> xyz=np.vstack((x,y,z)).T
    >>> m=tm.mean_curvature(xyz)
    >>> print('Mean curvature for straight line',m)
    >>> 
    >>> theta=np.pi*np.linspace(0,1,100)
    >>> x=np.cos(theta)
    >>> y=np.sin(theta)
    >>> z=0*x
    >>> xyz=np.vstack((x,y,z)).T
    >>> m=tm.mean_curvature(xyz)
    >>> print('Mean curvature for semi-circle',m)        
    '''
    xyz = np.asarray(xyz)
    n_pts = xyz.shape[0]
    if n_pts == 0:
        raise ValueError('xyz array cannot be empty')
    
    dxyz=np.gradient(xyz)[0]            
    ddxyz=np.gradient(dxyz)[0]
    
    #Curvature
    k = magn(np.cross(dxyz,ddxyz),1)/(magn(dxyz,1)**3)    
        
    return np.mean(k)

def frechet_distance(xyz1,xyz2):
    ''' Frechet distance
    http://www.cim.mcgill.ca/~stephane/cs507/Project.html
    http://www.cs.uu.nl/groups/AA/multimedia/matching/shame.html
    '''
    pass        
    
def mahnaz_distance(xyz1,xyz2):
    ''' Look Mahnaz's thesis
    '''
    pass

def zhang_distance(xyz1,xyz2):
    '''
    '''
    pass
    
def mean_orientation(xyz):
    pass
    

def startpoint(xyz):
    return xyz[0]

def endpoint(xyz):
    return xyz[-1]

def arbitrarypoint(xyz,distance):
    ''' Select an arbitrary point along distance on the track (curve)

    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    distance : float
        float representing distance travelled from the xyz[0] point of the curve along the curve.

    Returns
    -------
    ap : array shape (3,)
       arbitrary point of line, such that, if the arbitrary point is not a point in
       `xyz`, then we take the interpolation between the two nearest
       `xyz` points.  If `xyz` is empty, return a ValueError
    
    Examples
    -----------
    >>> from dipy.core import track_metrics as tm
    >>> import numpy as np
    >>> theta=np.pi*np.linspace(0,1,100)
    >>> x=np.cos(theta)
    >>> y=np.sin(theta)
    >>> z=0*x
    >>> xyz=np.vstack((x,y,z)).T
    >>> ap=tm.arbitrarypoint(xyz,tm.length(xyz)/3)
    >>> print('The point along the curve that traveled the given distance is ',ap)        
    '''
    
    xyz = np.asarray(xyz)
    n_pts = xyz.shape[0]
    if n_pts == 0:
        raise ValueError('xyz array cannot be empty')
    if n_pts == 1:
        return xyz.copy().squeeze()
    
    cumlen = np.zeros(n_pts)
    cumlen[1:] = length(xyz, along=True)    
    if cumlen[-1]<distance:
        raise ValueError('Given distance is bigger than the length of the curve')
            
    ind=np.where((cumlen-distance)>0)[0][0]
    len0=cumlen[ind-1]        
    len1=cumlen[ind]
    Ds=distance-len0
    Lambda = Ds/(len1-len0)
    return Lambda*xyz[ind]+(1-Lambda)*xyz[ind-1]

def _extrap(xyz,cumlen,distance):
    ''' Helper function for extrapolate    
    '''    
    ind=np.where((cumlen-distance)>0)[0][0]
    len0=cumlen[ind-1]        
    len1=cumlen[ind]
    Ds=distance-len0
    Lambda = Ds/(len1-len0)
    return Lambda*xyz[ind]+(1-Lambda)*xyz[ind-1]

def extrapolate(xyz,n_pols=3):
    ''' Extrapolate a specific number of points along the curve.
    It works similarly with midpoint and arbitrarypoint
    
    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    n_pol : int
        integer representing number of points (poles) we need along the curve.

    Returns
    -------
    xyz2 : array shape (M,3)
        array representing x,z,z of M points that where extrapolated. M should be
        equal to n_pols
    
    Examples
    -----------
    >>> from dipy.core import track_metrics as tm
    >>> import numpy as np
    >>> # a semi-circle
    >>> theta=np.pi*np.linspace(0,1,100)
    >>> x=np.cos(theta)
    >>> y=np.sin(theta)
    >>> z=0*x
    >>> xyz=np.vstack((x,y,z)).T
    >>> xyz2=tm.extrapolate(xyz,3)    
    >>> # a cosine
    >>> x=np.pi*np.linspace(0,1,100)
    >>> y=np.cos(theta)
    >>> z=0*y
    >>> xyz=np.vstack((x,y,z)).T
    >>> xyz2=tm.extrapolate(xyz,3)
    >>> xyz3=tm.extrapolate(xyz,10)
    '''
        
    xyz = np.asarray(xyz)
    n_pts = xyz.shape[0]
    if n_pts == 0:
        raise ValueError('xyz array cannot be empty')
    if n_pts == 1:
        return xyz.copy().squeeze()
        
    cumlen = np.zeros(n_pts)
    cumlen[1:] = length(xyz, along=True)    
    
    step=cumlen[-1]/(n_pols-1)
    if cumlen[-1]<step:
        raise ValueError('Given numper of points n_pols is incorrect. ')
    if n_pols<=2:
        raise ValueError('Given numper of points n_pols needs to be higher than 2. ')
    
    xyz2=[_extrap(xyz,cumlen,distance) for distance in np.arange(0,cumlen[-1],step) ]
        
    return np.vstack((np.array(xyz2),xyz[-1]))
    
def principal_components(xyz):
    ''' We use PCA to calculate the 3 principal directions for dataset xyz
    '''

    C=np.cov(xyz.T)    
    va,ve=np.linalg.eig(C)
          
    return va,ve

def midpoint2point(xyz,p):
    ''' Calculate the distance from the midpoint of a curve to an arbitrary point p
    
    Parameters
    ----------
    xyz : array-like shape (N,3)
       array representing x,y,z of N points in a track
    p : array shape (3,)
        array representing an arbitrary point with x,y,z coordinates in space.

    Returns
    -------
    d : float
        a float number representing Euclidean distance         
    '''
    mid=midpoint(xyz) 
    
    return np.sqrt(np.sum((xyz-mid)**2))

def curve_2_vox_space(xyz):
    pass

    
if __name__ == "__main__":
    pass

    
    
