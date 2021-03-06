from __future__ import division
import numpy as np
from scipy import linalg, ndimage
from pyeconomics.interpolation import pwl_interp

# Defining the transition matrix.

DurationUnempG = 1.5
DurationUnempB = 2.5
corr = .25

UnempG = .04
UnempB = .1
Unemp = np.array([[UnempG], [UnempB]])

DurationZG = 8
DurationZB = 8

pZG = 1 - 1 / DurationZG
pZB = 1 - 1 / DurationZB

PZ = np.array([[pZG, 1 - pZG], [1 - pZB, pZB]])

p22 = 1 - 1 / DurationUnempG
p21 = 1 - p22
p11 = ((1 - UnempG) - UnempG * p21) / (1 - UnempG)

P11 = np.array([[p11, 1 - p11], [p21, p22]])

p22 = 1 - 1 / DurationUnempB
p21 = 1 - p22
p11 = ((1 - UnempB) - UnempB * p21) / (1 - UnempB)

P00 = np.array([[p11, 1 - p11], [p21, p22]])

p22 = (1 + corr) * p22
p21 = 1 - p22
p11 = ((1 - UnempB) - UnempG * p21) / (1 - UnempG)

P10 = np.array([[p11, 1 - p11], [p21, p22]])

p22 = (1 - corr) * (1 - 1 / DurationUnempG)
p21 = 1 - p22
p11 = ((1 - UnempG) - UnempB * p21) / (1 - UnempB)

P01 = np.array([[p11,1 - p11], [p21, p22]])

P = np.vstack((np.hstack((PZ[0, 0] * P11, PZ[0, 1] * P10)), 
               np.hstack((PZ[1, 0] * P01, PZ[1, 1] * P00))))

# Model Parameters

alpha  = 0.36             
beta   = 0.99
delta  = .025
sigma  = 1
phi    = 0
Nk     = 250
NK     = 12
UI     = 0.15
h      = 1 / (1 - UnempB)
tau    = np.array([[UI * UnempG / (h * (1 - UnempG)), UI * UnempB / (h * (1 - UnempB))]])
BiasCorrection = 1

if BiasCorrection == 1:
    de = 0.01257504725554
    du = 0.03680683961167
else:
    de=0
    du=0

deltaZ = 0.01

# Grid
kmin   = phi
kmax   = 200

zg = 1 + deltaZ
zb = 1 - deltaZ
Z  = np.array([[zg], [zb]])
ZZ = Z

Kumin = 33
Kemin = 35
Kumax = 42.5
Kemax = 43.5

kptemp = np.linspace(0, np.log(kmax + 1 - kmin), Nk).reshape((Nk, 1))
kp = np.exp(kptemp) - 1 + kmin

Ke = np.linspace(Kemin, Kemax, NK).reshape((NK, 1))
Ku = np.linspace(Kumin, Kumax, NK).reshape((NK, 1))

# Individual policy function
kpp1 = np.empty((2, 2, NK, Nk, NK))
kpp2 = np.empty((2, 2, NK, Nk, NK))

# multi-dimensional array indexing differs between NumPy and Matlab

for ii in range(2):
    for i in range(2):
        for j in range(NK):
            for l in range(NK):
                kpp1[ii, i, l, :, j] = (1 - delta) * kp.flatten()
                kpp2[ii, i, l, :, j] = .3 * (1 - delta) * kp.flatten()

# Initial aggregate policy function (guess: unit root.)
A = np.empty((2, 2, 2))
A[0] = linalg.inv(np.array([[P11[0, 0], P11[1,0] * UnempG / (1 - UnempG)], 
                            [P11[0, 1] * (1 - UnempG) / UnempG, P11[1, 1]]]))
A[1] = linalg.inv(np.array([[P00[0,0], P00[1,0] * UnempB / (1 - UnempB)], 
                            [P00[0, 1] * (1 - UnempB)/UnempB, P00[1, 1]]]))

Kpeu = np.empty((2,1))
Kpe  = np.empty((2, NK, NK))
Kpu  = np.empty((2, NK, NK))
for ii in range(2):
    for i in range(NK):
        for j in range(NK):
            Kpeu = A[ii, :, :].dot(np.array([Ke[i], Ku[j]]))
            Kpe[ii, i, j] = Kpeu[0]
            Kpu[ii, i, j] = Kpeu[1]

KpeN = np.empty((2, 2, NK, NK))
KpeN[0, 0, :, :] = ((P11[0, 0] * (1 - UnempG) * Kpe[0, :, :] + 
                     P11[1, 0] * UnempG * Kpu[0, :, :]) / (1 - UnempG))
KpeN[1, 0, :, :] = ((P01[0, 0] * (1 - UnempB) * Kpe[1, :, :] + 
                     P01[1, 0] * UnempB * Kpu[1, :, :]) / (1 - UnempG))
KpeN[0, 1, :, :] = ((P10[0, 0] * (1 - UnempG) * Kpe[0, :, :] + 
                     P10[1, 0] * UnempG * Kpu[0, :, :]) / (1 - UnempB))
KpeN[1, 1, :, :] = ((P00[0, 0] * (1 - UnempB) * Kpe[1, :, :] + 
                     P00[1, 0] * UnempB * Kpu[1, :, :]) / (1 - UnempB))

KpuN = np.empty((2, 2, NK, NK))
KpuN[0, 0, :, :] = ((P11[0, 1] * (1 - UnempG) * Kpe[0, :, :] + 
                     P11[1, 1] * UnempG * Kpu[0, :, :]) / (UnempG))
KpuN[1, 0, :, :] = ((P01[0, 1] * (1 - UnempB) * Kpe[1, :, :] + 
                     P01[1, 1] * UnempB * Kpu[1, :, :]) / (UnempG))
KpuN[0, 1, :, :] = ((P10[0, 1] * (1 - UnempG) * Kpe[0, :, :] + 
                     P10[1, 1] * UnempG * Kpu[0, :, :]) / (UnempB))
KpuN[1, 1, :, :] = ((P00[0, 1] * (1 - UnempB) * Kpe[1, :, :] + 
                     P00[1, 1] * UnempB * Kpu[1, :, :]) / (UnempB))

KpeN = np.minimum(KpeN, np.max(Ke))
KpeN = np.maximum(KpeN, np.min(Ke))
KpuN = np.minimum(KpuN, np.max(Ku))
KpuN = np.maximum(KpuN, np.min(Ku))

# Solving the individual's Euler equation with endogenous gridpoints.

ConvCrit = 1
s = 0
tol = 1e-6

print 'Solving the individual and aggregate problem until ConvCrit < %g' %tol

while ConvCrit > tol:
    s = s + 1
    k = np.empty((2, 2, NK, Nk, NK))
    
    for i in range(2): # pages
        for j in range(NK): # rows
            for l in range(NK): # cols
                Kp = (1 - Unemp[i, 0]) * Kpe[i, j, l] + Unemp[i, 0] * Kpu[i, j, l]
                
                Rp = np.array([(1 + alpha * zg * (Kp / (h * (1 - UnempG)))**(alpha - 1) - delta), 
                               (1 + alpha * zg * (Kp / (h * (1 - UnempG)))**(alpha - 1) - delta),
                               (1 + alpha * zb * (Kp / (h * (1 - UnempB)))**(alpha - 1) - delta),
                               (1 + alpha * zb * (Kp / (h * (1 - UnempB)))**(alpha - 1) - delta)])
                
                Wp = np.array([h * (1 - alpha) * zg * (Kp / (h * (1 - UnempG)))**alpha * (1 - tau[0, 0]),
                              (1 - alpha) * zg * (Kp / (h * (1 - UnempG)))**alpha,
                              h * (1 - alpha) * zb * (Kp / (h * (1 - UnempB)))**alpha * (1 - tau[0, 1]),
                              (1 - alpha) * zb * (Kp / (h * (1 - UnempB)))**alpha])
                
                # correct dimensions are (Nk, 4)
                RHS = np.hstack((beta * Rp[0] * (Rp[0] * kp + Wp[0] - kpp1[i, 0, l, :, j].reshape((Nk, 1)))**(-sigma),
                                 beta * Rp[1] * (Rp[1] * kp + UI * Wp[1] - kpp2[i, 0, l, :, j].reshape((Nk, 1)))**(-sigma),
                                 beta * Rp[2] * (Rp[2] * kp + Wp[2] - kpp1[i, 1, l, :, j].reshape((Nk, 1)))**(-sigma),
                                 beta * Rp[3] * (Rp[3] * kp + UI * Wp[3] - kpp2[i, 1, l, :, j].reshape((Nk, 1)))**(-sigma)))
                
                C1 = (RHS.dot(P[2 * i, :].reshape((P.shape[0], 1))))**(-1 / sigma)
                C2 = (RHS.dot(P[2 * i + 1, :].reshape((P.shape[0], 1))))**(-1/sigma)
                
                K = (1 - Unemp[i, 0]) * Ke[j, 0] + Unemp[i, 0] * Ku[l, 0]
            
                k[i, 0, l, :, j] = ((C1 - h * (1 - alpha) * Z[i, 0] * (K / (h * (1 - Unemp[i, 0])))**alpha * (1 - tau[0, i]) + kp).flatten() / 
                                    ((1 + alpha * Z[i, 0] * (K / (h * (1 - Unemp[i, 0])))**(alpha - 1) - delta)))
                k[i, 1, l, :, j] = ((C2 - UI * (1 - alpha) * Z[i, 0] * (K / (h * (1 - Unemp[i, 0])))**alpha + kp).flatten() /
                                    ((1 + alpha * Z[i, 0] * (K / (h * (1 - Unemp[i, 0])))**(alpha - 1) - delta)))
    
    
    ConvCrit = 0

    kpmat = np.empty((2, 2, NK, Nk, NK))
    for i in range(2):
        for j in range(NK):
            for l in range(NK):
                x  = k[i, 0, l, :, j]
                Y  = kp
                xi = kp
                if np.min(k[i, 0, l, :,j]) > 0:
                    x = np.append(0, x)
                    Y = np.append(0, Y)
                    kpmat[i, 0, l, :, j] = pwl_interp.pwl_interp_1d(x, Y, xi)
                else:
                    kpmat[i, 0, l, :, j] = pwl_interp.pwl_interp_1d(x, Y, xi)
                
                x  = k[i, 1, l, :, j]
                Y  = kp
                xi = kp
                if np.min(k[i, 1, l, :, j]) > 0:
                    x = np.append(0, x)
                    Y = np.append(0, Y)
                    kpmat[i, 1, l, :,j] = pwl_interp.pwl_interp_1d(x, Y, xi)
                else:
                    kpmat[i, 1, l, :, j] = pwl_interp.pwl_interp_1d(x, Y, xi)
    
    # Update the individual policy functions for t+1
    kpp2New = np.empty((2, 2, NK, Nk, NK))
    for ii in range(2):
        for i in range(2):
            for j in range(NK):
                for l in range(NK):
                    kpp1[ii, i, l, :, j] = pwl_interp.pwl_interp_3d(Ke, kp, Ku, kpmat[i, 0, :, :, :], 
                                                                    np.repeat(KpeN[ii, i, j, l], Nk), kp, np.repeat(KpuN[ii, i, j, l], Nk))
                    kpp2New[ii, i, l, :, j] = pwl_interp.pwl_interp_3d(Ke, kp, Ku, kpmat[i, 1, :, :, :], 
                                                                       np.repeat(KpeN[ii, i, j, l], Nk), kp, np.repeat(KpuN[ii, i, j, l], Nk))
    
    # Update the convergence measure:
    ConvCrit = np.max(np.abs(kpp2New[0, 0, 0, :, 0] - kpp2[0, 0, 0, :, 0]) / (1 + np.abs(kpp2[0, 0, 0, :, 0])))
    
    if s % 10 == 0:
        print 'After %i iterations, the current value of ConvCrit is %g.' %(s, ConvCrit)
     
    kpp2 = kpp2New
     
    # Update the aggregate policy function using explicit aggregation:
    KpeNew = np.empty((2, NK, NK))
    KpuNew = np.empty((2, NK, NK))
    for i in range(NK):
        for j in range(NK):
            for l in range(2):
                x = kp
                Y = kpmat[l, 0, j, :, i]
                KpeNew[l, i, j] = pwl_interp.pwl_interp_1d(x, Y, Ke[i, 0]) + de
                Y = kpmat[l, 1, j, :, i]
                KpuNew[l, i, j] = pwl_interp.pwl_interp_1d(x, Y, Ku[j, 0]) + du

    """
    # no idea what this conditional is doing!
    if s > 200:
        rho = 0;
        Kpe = rho * Kpe + (1 - rho) * KpeNew
        Kpu = rho * Kpu + (1 - rho) * KpuNew
    
        KpeN[0, 0, :, :] = ((P11[0, 0] * (1 - UnempG) * Kpe[0, :, :] + 
                             P11[1, 0] * UnempG * Kpu[0, :, :]) / (1 - UnempG))
        KpeN[1, 0, :, :] = ((P01[0, 0] * (1 - UnempB) * Kpe[1, :, :] + 
                             P01[1, 0] * UnempB * Kpu[1, :, :]) / (1 - UnempG))
        KpeN[0, 1, :, :] = ((P10[0, 0] * (1 - UnempG) * Kpe[0, :, :] + 
                             P10[1, 0] * UnempG * Kpu[0, :, :]) / (1 - UnempB))
        KpeN[1, 1, :, :] = ((P00[0, 0] * (1 - UnempB) * Kpe[1, :, :] + 
                             P00[1, 0] * UnempB * Kpu[1, :, :]) / (1 - UnempB))

        KpuN[0, 0, :, :] = ((P11[0, 1] * (1 - UnempG) * Kpe[0, :, :] + 
                             P11[1, 1] * UnempG * Kpu[0, :, :]) / (UnempG))
        KpuN[1, 0, :, :] = ((P01[0, 1] * (1 - UnempB) * Kpe[1, :, :] + 
                             P01[1, 1] * UnempB * Kpu[1, :, :]) / (UnempG))
        KpuN[0, 1, :, :] = ((P10[0, 1] * (1 - UnempG) * Kpe[0, :, :] + 
                             P10[1, 1] * UnempG * Kpu[0, :, :]) / (UnempB))
        KpuN[1, 1, :, :] = ((P00[0, 1] * (1 - UnempB) * Kpe[1, :, :] + 
                             P00[1, 1] * UnempB * Kpu[1, :, :]) / (UnempB))
        
        KpeN = np.minimum(KpeN, np.max(Ke))
        KpeN = np.maximum(KpeN, np.min(Ke))
        KpuN = np.minimum(KpuN, np.max(Ku))
        KpuN = np.maximum(KpuN, np.min(Ku))
    """

print ('The individual and aggregate problem has converged. Simulation will ' + 
       'proceed until s=10000')

# Initial Distribution

pdistyoung = np.loadtxt('pdistyoung.txt')
InDist = pdistyoung[:, 1:]

NDist = len(InDist)

kk = np.linspace(0, kmax, NDist)

Pe = InDist[:, 1]
Pu = InDist[:, 0]

# Exogenous shocks

Z    = np.loadtxt('Z.txt', dtype='int')
ZSim = -Z + 2 # Python indexing starts at 0!

KeSim = np.zeros(Z.shape)
KuSim = np.zeros(Z.shape)

KeSim[0] = kk.dot(Pe)
KuSim[0] = kk.dot(Pu)

# make sure to use copy?
KeImp = KeSim.copy()
KuImp = KuSim.copy()

KeFit = KeSim.copy()
KuFit = KuSim.copy()

ind_switch = np.loadtxt('ind_switch.txt')
ind_switch = -ind_switch + 2 # careful about indexing!
Kind = np.zeros(Z.shape)
Cind = np.zeros(len(Z) - 1)
Kind[0] = 43
percentile = np.zeros((len(Z), 6))
moments    = np.zeros((len(Z), 5))
momentse   = np.zeros((len(Z), 5))
momentsu   = np.zeros((len(Z), 5))
Rvec       = np.zeros((len(Z), 1))
Wvec       = np.zeros((len(Z), 1))

# Let's rock'n'roll

s = 0
SimLength = len(Z) - 1
for i in range(SimLength):
    
    # remember to transpose 2D array before passing as arg...inputs needs to be Fortran contiguous!
    KpeSim = pwl_interp.pwl_interp_2d(Ku, Ke, Kpe[ZSim[i], :, :].T, KuSim[i], KeSim[i])
    KpuSim = pwl_interp.pwl_interp_2d(Ku, Ke, Kpu[ZSim[i], :, :].T, KuSim[i], KeSim[i])

    KpeFit = pwl_interp.pwl_interp_2d(Ku, Ke, Kpe[ZSim[i], :, :].T, KuImp[i], KeImp[i])
    KpuFit = pwl_interp.pwl_interp_2d(Ku, Ke, Kpu[ZSim[i], :, :].T, KuImp[i], KeImp[i])

    # why do I not need to bother making 3D array Fortran contiguous?
    kprimeE = pwl_interp.pwl_interp_3d(Ke, kp, Ku, kpmat[ZSim[i], 0, :,:,:], 
                                       np.repeat(kk.dot(Pe), NDist), kk, np.repeat(kk.dot(Pu), NDist))    
    kprimeU = pwl_interp.pwl_interp_3d(Ke, kp, Ku, kpmat[ZSim[i], 1, :,:,:], 
                                       np.repeat(kk.dot(Pe), NDist), kk, np.repeat(kk.dot(Pu), NDist))
   
    Kind[i + 1] = pwl_interp.pwl_interp_3d(Ke, kp, Ku, kpmat[ZSim[i], ind_switch[i], :, :, :], kk.dot(Pe), Kind[i], kk.dot(Pu))
    
    K = (1 - Unemp[ZSim[i], 0]) * KeImp[i] + Unemp[ZSim[i], 0] * KuImp[i]
    r = 1 + alpha * ZZ[ZSim[i], 0] * (K / (h * (1 - Unemp[ZSim[i], 0])))**(alpha - 1) - delta
    w = (1 - alpha) * ZZ[ZSim[i], 0] * (K / (h * (1 - Unemp[ZSim[i], 0])))**alpha

    # not sure what is going on with ind_switch
    Cind[i] = r * Kind[i] + (1 - ind_switch[i]) * h * w * (1 - tau[0, ZSim[i]]) + ind_switch[i] * w * UI - Kind[i + 1]
    Rvec[i] = r
    Wvec[i] = w
    
    kprimeE = np.minimum(kprimeE, np.max(kk))
    kprimeE = np.maximum(kprimeE, np.min(kk))

    kprimeU = np.minimum(kprimeU, np.max(kk))
    kprimeU = np.maximum(kprimeU, np.min(kk))

    P = (1 - Unemp[ZSim[i], 0]) * Pe + Unemp[ZSim[i], 0] * Pu

    # This section computes percentiles of something...not sure what!    
    
    CP = np.cumsum(P)
    IP5 = np.nonzero(CP < 0.05)[0][-1] # occasionally this is empty!
    percentile[i, 0] = (0.05 - CP[IP5 + 1]) / (CP[IP5] - CP[IP5 + 1]) * kk[IP5] + (1 - (0.05 - CP[IP5 + 1]) / (CP[IP5] - CP[IP5 + 1])) * kk[IP5 + 1] 
    IP10 = np.nonzero(CP < 0.1)[0][-1]
    percentile[i, 1] = (0.1 - CP[IP10 + 1]) / (CP[IP10] - CP[IP10 + 1]) * kk[IP10] + (1 - (0.1 - CP[IP10 + 1]) / (CP[IP10] - CP[IP10 + 1])) * kk[IP10 + 1]
    
    CPe = np.cumsum(Pe)
    IPe5 = np.nonzero(CPe < 0.05)[0][-1] # occasionally this is empty!
    percentile[i, 2] = (0.05 - CPe[IPe5 + 1]) / (CPe[IPe5] - CPe[IPe5 + 1]) * kk[IPe5] + (1 - (0.05 - CPe[IPe5 + 1]) / (CPe[IPe5] - CPe[IPe5 + 1])) * kk[IPe5 + 1]
    IPe10 = np.nonzero(CPe < 0.1)[0][-1]
    percentile[i, 3] = (0.1 - CPe[IPe10 + 1]) / (CPe[IPe10] - CPe[IPe10 + 1]) * kk[IPe10] + (1 - (0.1 - CPe[IPe10 + 1]) / (CPe[IPe10] - CPe[IPe10 + 1])) * kk[IPe10 + 1]

    CPu = np.cumsum(Pu);
    IPu5 = np.nonzero(CPu < 0.05)[0][-1] # occasionally this is empty!
    percentile[i, 4] = (0.05 - CPu[IPu5 + 1]) / (CPu[IPu5] - CPu[IPu5 + 1]) * kk[IPu5] + (1 - (0.05 - CPu[IPu5 + 1]) / (CPu[IPu5] - CPu[IPu5 + 1])) * kk[IPu5 + 1]
    IPu10 = np.nonzero(CPu < 0.1)[0][-1]
    percentile[i, 5] = (0.1 - CPu[IPu10 + 1]) / (CPu[IPu10] - CPu[IPu10 + 1]) * kk[IPu10] + (1 - (0.1 - CPu[IPu10 + 1]) / (CPu[IPu10] - CPu[IPu10 + 1])) * kk[IPu10 + 1]
    
    moments[i, 0]  = kk.dot(P)
    momentse[i, 0] = kk.dot(Pe)
    momentsu[i, 0] = kk.dot(Pu)
    
    for j in range(2, 5):
        moments[i, j] = (((kk**j).T).dot(P))**(1 / j) / moments[i, 0]
        momentse[i, j] = (((kk**j).T).dot(Pe))**(1 / j) / momentse[i, 0]
        momentsu[i, j] = (((kk**j).T).dot(Pu))**(1 / j) / momentsu[i, 0]

    Ie = np.empty(NDist, dtype='int')
    Iu = np.empty(NDist, dtype='int')
    
    for j in range(NDist):
        Ie[j] = np.nonzero(kprimeE[j] >= kk)[0][-1]
        Iu[j] = np.nonzero(kprimeU[j] >= kk)[0][-1]

    # careful with indexing!
    Ie = np.minimum(Ie, NDist - 2)
    Iu = np.minimum(Iu, NDist - 2)

    rhoE = (kprimeE - kk[Ie + 1]) / (kk[Ie] - kk[Ie + 1])
    rhoU = (kprimeU - kk[Iu + 1]) / (kk[Iu] - kk[Iu + 1])

    Le1 = np.zeros((NDist, 1))
    Le2 = np.zeros((NDist, 1))
    Lu1 = np.zeros((NDist, 1))
    Lu2 = np.zeros((NDist, 1))

    for jj in range(NDist):
        Le1[Ie[jj]]     = rhoE[jj] * Pe[jj] + Le1[Ie[jj]]
        Le2[Ie[jj] + 1] = (1 - rhoE[jj]) * Pe[jj] + Le2[Ie[jj] + 1]
        Lu1[Iu[jj]]     = rhoU[jj] * Pu[jj] + Lu1[Iu[jj]]
        Lu2[Iu[jj] + 1] = (1 - rhoU[jj]) * Pu[jj] + Lu2[Iu[jj] + 1]
 
    PPe = Le1 + Le2
    PPu = Lu1 + Lu2

    if ZSim[i] == 0:
        if ZSim[i + 1] == 0:
            KeSim[i + 1] = (P11[0, 0] * (1-UnempG) * KpeSim + P11[1, 0] * UnempG * KpuSim) / (1 - UnempG)
            KuSim[i + 1] = (P11[0, 1] * (1-UnempG) * KpeSim + P11[1, 1] * UnempG * KpuSim) / UnempG
            KeFit[i + 1] = (P11[0, 0] * (1-UnempG) * KpeFit + P11[1, 0] * UnempG * KpuFit) / (1 - UnempG)
            KuFit[i + 1] = (P11[0, 1] * (1-UnempG) * KpeFit + P11[1, 1] * UnempG * KpuFit) / UnempG
            Pe           = (P11[0, 0] * (1-UnempG) * PPe + P11[1, 0] * UnempG * PPu) / (1 - UnempG)
            Pu           = (P11[0, 1] * (1-UnempG) * PPe + P11[1, 1] * UnempG * PPu) / UnempG
            KeImp[i + 1] = kk.dot(Pe)
            KuImp[i + 1] = kk.dot(Pu)
        
        if ZSim[i + 1] == 1:
            KeSim[i + 1] = (P10[0, 0] * (1 - UnempG) * KpeSim + P10[1, 0] * UnempG * KpuSim) / (1 - UnempB)
            KuSim[i + 1] = (P10[0, 1] * (1 - UnempG) * KpeSim + P10[1, 1] * UnempG * KpuSim) / UnempB
            KeFit[i + 1] = (P10[0, 0] * (1 - UnempG) * KpeFit + P10[1, 0] * UnempG * KpuFit) / (1 - UnempB)
            KuFit[i + 1] = (P10[0, 1] * (1 - UnempG) * KpeFit + P10[1, 1] * UnempG * KpuFit) / UnempB
            Pe           = (P10[0, 0] * (1 - UnempG) * PPe + P10[1, 0] * UnempG * PPu) / (1 - UnempB)
            Pu           = (P10[0, 1] * (1 - UnempG) * PPe + P10[1, 1] * UnempG * PPu) / UnempB
            KeImp[i + 1] = kk.dot(Pe)
            KuImp[i + 1] = kk.dot(Pu)

    if ZSim[i] == 1:
        if ZSim[i + 1] == 0:
            KeSim[i + 1] = (P01[0, 0] * (1 - UnempB) * KpeSim + P01[1, 0] * UnempB * KpuSim) / (1 - UnempG)
            KuSim[i + 1] = (P01[0, 1] * (1 - UnempB) * KpeSim + P01[1, 1] * UnempB * KpuSim) / UnempG
            KeFit[i + 1] = (P01[0, 0] * (1 - UnempB) * KpeFit + P01[1, 0] * UnempB * KpuFit) / (1 - UnempG)
            KuFit[i + 1] = (P01[0, 1] * (1 - UnempB) * KpeFit + P01[1, 1] * UnempB * KpuFit) / UnempG 
            Pe           = (P01[0, 0] * (1 - UnempB) * PPe + P01[1, 0] * UnempB * PPu) / (1 - UnempG)
            Pu           = (P01[0, 1] * (1 - UnempB) * PPe + P01[1, 1] * UnempB * PPu) / UnempG
            KeImp[i + 1] = kk.dot(Pe)
            KuImp[i + 1] = kk.dot(Pu)
        
        if ZSim[i + 1] == 1:
            KeSim[i + 1] = (P00[0, 0] * (1 - UnempB) * KpeSim + P00[1, 0] * UnempB * KpuSim) / (1 - UnempB)
            KuSim[i + 1] = (P00[0, 1] * (1 - UnempB) * KpeSim + P00[1, 1] * UnempB * KpuSim) / UnempB
            KeFit[i + 1] = (P00[0, 0] * (1 - UnempB) * KpeFit + P00[1, 0] * UnempB * KpuFit) / (1 - UnempB)
            KuFit[i + 1] = (P00[0, 1] * (1 - UnempB) * KpeFit + P00[1, 1] * UnempB * KpuFit) / UnempB
            Pe           = (P00[0, 0] * (1 - UnempB) * PPe + P00[1, 0] * UnempB * PPu) / (1 - UnempB)
            Pu           = (P00[0, 1] * (1 - UnempB) * PPe + P00[1, 1] * UnempB * PPu) / UnempB
            KeImp[i + 1] = kk.dot(Pe)
            KuImp[i + 1] = kk.dot(Pu)
            
    # increment the counter
    s = s + 1
    if s % 100 == 0:
        print "Number of iterations:", s
    
# finish up!
KSim = (1 - Unemp[ZSim, 0]) * KeSim + Unemp[ZSim, 0] * KuSim
KImp = (1 - Unemp[ZSim, 0]) * KeImp + Unemp[ZSim, 0] * KuImp
KFit = (1 - Unemp[ZSim, 0]) * KeFit + Unemp[ZSim, 0] * KuFit

ZZ = np.array([[zg], [zb]])
Y  = ZZ[ZSim, 0] * KImp**alpha * ((1 - Unemp[ZSim, 0]) * h)**(1 - alpha)
C  = Y[:-1] - KImp[1:] + (1 - delta) * KImp[:-1]

# aggregate output
Yind = Cind + Kind[1:] - (1 - delta) * Kind[:-1]

print 'Correlation of individual and aggregate consumption:' 
print np.corrcoef([Cind, C])
print 'Correlation of individual consumption and aggregate income:' 
print np.corrcoef([Cind, Y[:-1]])
print 'Correlation of individual consumption and aggregate capital:' 
print np.corrcoef([Cind, KImp[:-1]])
print 'Correlation of individual consumption and individual income:'
print np.corrcoef([Cind, Yind])
print 'Correlation of individual consumption and individual capital:' 
print np.corrcoef([Cind, Kind[:-1]])
print ''
print 'Standard deviation of individual consumption:', np.std(Cind)
print 'Standard deviation of individual capital:', np.std(Kind)
print ''
print 'Autocorrelation of individual consumption:'
print np.corrcoef([Cind[:-3], Cind[1:-2],Cind[2:-1],Cind[3:]])
print 'Autocorrelation of individual capital:'
print np.corrcoef([Kind[:-3], Kind[1:-2], Kind[2:-1], Kind[3:]])
print 'Autocorrelation of individual consumption growth:'
cgrowth = np.log(Cind[1:]) - np.log(Cind[:-1])
print np.corrcoef([cgrowth[:-3], cgrowth[1:-2], cgrowth[2:-1], cgrowth[3:]])
print ''
print 'Max error Ke (%)', 100 * np.max(np.abs(np.log(KeSim) - np.log(KeImp)))
print 'Max error Ku (%)', 100 * np.max(np.abs(np.log(KuSim) - np.log(KuImp)))
print 'Mean error Ke (%)', 100 * np.mean(np.abs(np.log(KeSim) - np.log(KeImp)))
print 'Mean error Ku (%)', 100 * np.mean(np.abs(np.log(KuSim) - np.log(KuImp)))
print ''
print 'R-Square K', 1 - (np.var(KImp - KFit) / np.var(KImp))
print 'R-Square Ke', 1 - (np.var(KeImp - KeFit) / np.var(KeImp))
print 'R-Square Ku', 1 - (np.var(KuImp - KuFit) / np.var(KuImp))
