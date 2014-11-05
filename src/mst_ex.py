## MS&T 2014 Fall meeting application
## - plot flow stress along various paths

from os import sep, popen
from glob import glob
from RS import rs_ex
from MP.lib import mpl_lib,axes_label
import matplotlib.pyplot as plt
import numpy as np
from MP.mat.mech import find_err
wf = mpl_lib.wide_fig
fl = mpl_lib.fancy_legend

def main_plot_flow_all(hkl='211',sin2psimx=0.5,
                       psi_nbin=1,pmargin=None,iplot_rs=False,
                       path=''):
    """ 
    Arguments
    =========
    hkl='211'
    sin2psimx
    psi_nbin = 1
    pmargin = None
    iplot_rs=False
    path=''
    """
    fns = read(hkl,prefix=path)
    if len(fns)==0:
        raise IOError, 'Check the path, 0 file was found'
    plt.ioff()
    fig = wf(nw=3,nh=1,left=0.2,uw=3.5,
             w0=0,w1=0.3,right=0,iarange=True)
    ax1,ax2,ax3 = fig.axes
    axes_label.__eqv__(ax1,ft=10)
    errors = []
    for i in range(len(fns)):
        fn = fns[i]
        strain_path = fn.split('_')[0]
        untargz(fn)
        model_rs, fwgt, fdsa \
            = rs_ex.ex_consistency(
                sin2psimx=sin2psimx,
                psi_nbin=psi_nbin,
                hkl=hkl,iplot=iplot_rs,
                pmargin=pmargin,path=path)
        fwgt.get_eqv(); fdsa.get_eqv()

        e = find_err(fwgt,fdsa)
        ax3.plot(fwgt.epsilon_vm,e)
        errors.append([fwgt.epsilon_vm,e])

        ax1.plot(fwgt.epsilon_vm,fwgt.sigma_vm,
                 'bx-',label='Weighted Avg', alpha=1.0)
        ax1.plot(fdsa.epsilon_vm,fdsa.sigma_vm,
                 'kx',label='Diff. Stress Analsysis', alpha=1.0)
        ax2.plot(fwgt.sigma[0,0],fwgt.sigma[1,1],'b+')
        ax2.plot(fdsa.sigma[0,0],fdsa.sigma[1,1],'k+')

        ## connector
        npoints = len(fwgt.sigma[0,0])
        wgtx = fwgt.sigma[0,0]; wgty = fwgt.sigma[1,1]
        dsax = fdsa.sigma[0,0]; dsay = fdsa.sigma[1,1]
        for j in range(npoints):
            ax2.plot([wgtx[j],dsax[j]],[wgty[j],dsay[j]],'k-',alpha=0.5)

    ax1.set_xlim(-0.1,1.1); ax1.set_ylim(-50,700);
    ax2.set_xlim(-10,1000); ax2.set_ylim(-10,1000)
    ax2.set_aspect('equal')
    ax2.set_xlabel(r'$\bar{\Sigma}_{11}$',dict(fontsize=15))
    ax2.set_ylabel(r'$\bar{\Sigma}_{22}$',dict(fontsize=15))
    ax2.locator_params(nbins=3)
    ax2.grid('on'); plt.show()

    plt.ion()
    plt.show();plt.draw()
    fn = 'flow_allpaths_%s.pdf'%(hkl)
    fig.savefig(fn)
    print '%s has been saved.'%fn
    plt.close(fig)

    return np.array(errors)[0]

def error_est_conds(psi_nbin=21,sin2psimx=0.5):
    paths=['BB','URD','UTD','PSRD','PSTD']
    for i in range(len(paths)):
        error_est(
            paths[i],psi_nbin=psi_nbin,
            sin2psimx=sin2psimx,iplot_rs=False)

def error_est(
        path='BB',psi_nbin=21,
        sin2psimx=0.5,
        hkls=['200','220','211','310'],
        iplot_rs=False):
    """
    """
    from MP.lib.axes_label import __deco__ as deco
    fig = wf(nw=1,nh=1,left=0.2,uw=3.5,
             w0=0,w1=0.3,right=0,iarange=True)
    ax=fig.axes[0]
    for i in range(len(hkls)):
        err = main_plot_flow_all(
            hkl=hkls[i],sin2psimx=sin2psimx,
            psi_nbin=psi_nbin,pmargin=None,
            iplot_rs=iplot_rs,path=path)
        eps_vm, e = err
        ax.plot(eps_vm,e,label=hkls[i])
    deco(iopt=8,ft=15,ax=ax)
    ax.legend(loc='best',fontsize=9)
    fig.savefig('error_dsa_%s.pdf'%path)
    return fig

def untargz(fn): std = popen('tar -xzf %s'%fn)

def read(hkl='211',prefix=''):
    fns=glob('%s*_%s_*.tar.gz'%(prefix,hkl))
    print '%i files are found'%len(fns)
    return fns

def plot_rsq():
    from MP.lib import mpl_lib
    import numpy as np
    import matplotlib.pyplot as plt
    from pepshkl import reader2 as reader
    import sfig_class
    from MP.mat.mech import FlowCurve as FC
    StressFactor=sfig_class.SF

    flow = FC(); flow.get_model(fn='STR_STR.OUT');flow.get_eqv()
    tdat,usf  = reader(fn='igstrain_fbulk_ph1.out',iopt=1,isort=True)
    vdat,ngrd = return_vf()
    wf = mpl_lib.wide_fig
    nstp,nij,nphi,npsi = tdat.shape[1:]

    Psi = tdat[8,:,:,:,:]
    Phi = tdat[7,:,:,:,:]
    rsq = tdat[9,:,:,:,:]
    sf  = tdat[3,:,:,:,:]

    ## swap sf axes to comply with sfig_class.SF.sf
    ## [nstp,nphi,npsi,nij]

    sf = sf.swapaxes(1,3).swapaxes(1,2)
    rsq=rsq.swapaxes(1,3).swapaxes(1,2)

    psi = Psi[0,0,0,:]
    phi = Phi[0,0,:,0]
    print psi.shape
    print phi.shape
    print sf.shape

    SF=StressFactor()
    SF.add_data(sf=sf,phi=phi,psi=psi)
    SF.flow = flow ## overwrite flow
    SF.add_vf(vdat)
    SF.add_rsq(rsq)
    SF.plot()

    return sf,vdat,rsq,psi

def return_vf():
    """
    Return volume fraction from 'int_els_ph1.out'
    """
    from pepshkl import reader4
    tdat,_psis_,_vdat_,_ngrd_ = reader4(
        fn='int_els_ph1.out',ndetector=2,iopt=1)

    ## sorting
    import MP.ssort as sort
    shsort = sort.shellSort
    ss     = sort.ind_swap

    ## sort psi and find ind
    psis, ind = shsort(_psis_)
    nstp, nphi, npsis = np.shape(_vdat_)
    vdat = np.zeros((nstp,nphi,npsis))
    ngrd = np.zeros((nstp,nphi,npsis))

    for istp in range(nstp):
        for iphi in range(nphi):
            dum_v = _vdat_[istp,iphi,:][::]
            vdat[istp,iphi,:] = ss(dum_v[::],ind)[::]

            dum_n = _ngrd_[istp,iphi,:][::]
            ngrd[istp,iphi,:] = ss(dum_n[::],ind)[::]
    return vdat, ngrd


def plot_sf(sff_fn='temp.sff',pmargin=0.1):
    """
    Arguments
    =========
    sff_fn = 'temp.sff'
    pmargin = 0.1
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from pepshkl import reader4
    from RS import sff_converter
    from rs_exp import read_IGSF
    from MP.lib import mpl_lib
    wf = mpl_lib.wide_fig

    sff_converter.main(fn=sff_fn,difile=None,itab=True,
                       ieps0=4,  fn_str='STR_STR.OUT')
    SF, IG = read_IGSF(fn=sff_fn,fn_str='STR_STR.OUT')

    tdat,_psis_,_vdat_,_ngrd_ = reader4(
        fn='int_els_ph1.out',ndetector=2,iopt=1)

    ## sorting
    import MP.ssort as sort
    shsort = sort.shellSort
    ss     = sort.ind_swap

    ## sort psi and find ind
    psis, ind = shsort(_psis_)
    nstp, nphi, npsis = np.shape(_vdat_)
    vdat = np.zeros((nstp,nphi,npsis))
    ngrd = np.zeros((nstp,nphi,npsis))

    for istp in range(nstp):
        for iphi in range(nphi):
            dum_v = _vdat_[istp,iphi,:][::]
            vdat[istp,iphi,:] = ss(dum_v[::],ind)[::]

            dum_n = _ngrd_[istp,iphi,:][::]
            ngrd[istp,iphi,:] = ss(dum_n[::],ind)[::]

    SF.mask_vol() ## shake off all zero values
    SF.add_vf(vdat)
    ## Mask data lacking sufficient volume
    SF.mask_vol(pmargin=pmargin)

    fig=wf(nw=1,nh=1)
    ax=fig.axes[0]
    for istp in range(nstp):
        sign_sin2psi = np.sign(SF.psi)*np.sin(SF.psi*np.pi/180.)**2
        ax.plot(sign_sin2psi,SF.vf[istp,0,:],'--')

    SF.plot(nbin_sin2psi=3,iopt=1)
    return SF,tdat,psis,vdat,ngrd

def test_ig(sff_fn='dum.sff'):
    import numpy as np
    import matplotlib.pyplot as plt
    from pepshkl import reader4
    from RS import sff_converter
    from rs_exp import read_IGSF
    from MP.lib import mpl_lib
    wf = mpl_lib.wide_fig

    sff_converter.main(fn=sff_fn,difile=None,itab=True,
                       ieps0=4,  fn_str='STR_STR.OUT')
    SF, IG = read_IGSF(fn=sff_fn,fn_str='STR_STR.OUT')

    IG.plot()


def plot_sf_psis(
        sff_fn='temp.sff',
        psi_ref=[45.0, 42.4, 39.8, 37.1, 34.3, 31.5,
                 28.5, 25.2, 21.7, 17.5, 12.3, 0]):
    import numpy as np
    import matplotlib.pyplot as plt
    from pepshkl import reader4
    from RS import sff_converter
    from rs_exp import read_IGSF
    from MP.lib import mpl_lib, axes_label
    from RS.rs import find_nearest

    deco = axes_label.__deco__
    wf = mpl_lib.wide_fig

    sff_converter.main(fn=sff_fn,difile=None,itab=True,
                       ieps0=4,  fn_str='STR_STR.OUT')
    SF, IG = read_IGSF(fn=sff_fn,fn_str='STR_STR.OUT')

    tdat,_psis_,_vdat_,_ngrd_ = reader4(
        fn='int_els_ph1.out',ndetector=2,iopt=1)

    ## sorting
    import MP.ssort as sort
    shsort = sort.shellSort
    ss     = sort.ind_swap

    ## sort psi and find ind
    psis, ind = shsort(_psis_)
    nstp, nphi, npsis = np.shape(_vdat_)
    vdat = np.zeros((nstp,nphi,npsis))
    ngrd = np.zeros((nstp,nphi,npsis))

    for istp in range(nstp):
        for iphi in range(nphi):
            dum_v = _vdat_[istp,iphi,:][::]
            vdat[istp,iphi,:] = ss(dum_v[::],ind)[::]

            dum_n = _ngrd_[istp,iphi,:][::]
            ngrd[istp,iphi,:] = ss(dum_n[::],ind)[::]

    ## Find only psi_ref values
    ## sin2psi_ref = np.sin(psi_ref*np.pi/180.)**2
    inds = []
    for i in range(len(psi_ref)):
        inds.append(find_nearest(SF.psi, psi_ref[i]))

    #SF.mask_vol() ## shake off all zero values

    fig=wf(nh=nphi,nw=len(psi_ref),iarange=True)
    figv=wf(nh=nphi,nw=len(psi_ref),iarange=True)
    fe0=wf(nh=nphi,nw=len(psi_ref),iarange=True)
    for iphi in range(nphi):
        for ipsi in range(len(psi_ref)):
            #ax = fig.axes[iphi+nphi*ipsi]
            ax = fig.axes[ipsi+len(psi_ref)*iphi]
            axt = figv.axes[ipsi+len(psi_ref)*iphi]
            aig = fe0.axes[ipsi+len(psi_ref)*iphi]
            if iphi==0:
                ax.set_title(
                    r'$\psi= %3.1f^\circ{}$'%\
                    SF.psi[inds[ipsi]]
                )
                axt.set_title(
                    r'$\psi= %3.1f^\circ{}$'%\
                    SF.psi[inds[ipsi]]
                )
                aig.set_title(
                    r'$\psi= %3.1f^\circ{}$'%\
                    SF.psi[inds[ipsi]]
                )
            if ipsi==0:
                ax.text(0,0,r'$\phi=%3.1f^\circ{}$'%\
                        SF.phi[iphi],transform=ax.transAxes)
                axt.text(0,0,r'$\phi=%3.1f^\circ{}$'%\
                         SF.phi[iphi],transform=axt.transAxes)
                aig.text(0,0,r'$\phi=%3.1f^\circ{}$'%\
                         SF.phi[iphi],transform=aig.transAxes)

                deco(ax,iopt=6)
                deco(axt,iopt=7)

            x = SF.flow.epsilon_vm
            y = SF.sf[:,iphi,inds[ipsi],0] # f11
            ig = IG.ig[:,iphi,inds[ipsi]]
            v = vdat[:,iphi,inds[ipsi]]
            ax.plot(x,y*1e12,'b-o')
            aig.plot(x,ig,'b-o')
            axt.plot(x,v,'r-x')

            axt.set_ylim(0.,0.10)
            ax.set_xlim(0.,1.0)
            aig.set_xlim(0.,1.0)
            aig.set_ylim(-0.002,0.002)

def use_intp_sfig(ss=2,iopt=0):
    """
    Use "interpolated" SF/IG strains
    to calculate the influence of 'interpolation'

    Arguments
    =========
    ss=2   or [0,1,3]
       * If ss is an integer, use it as 'step'
       * If ss is a list with intengers in it,
         use these element-wise integers to select.

    interpolation method applied to SF/IG w.r.t. strain
    iopt=0: NN (piece-wise linear interpolation)
        =1: Assign nearest data
        =2: Cubic
        =3: Quadratic
        =4: Linear fit
        =5: Poly2
        =6: poly3
        =7: Place-holder for power law fit
        =8: zero
        =9: slinear
    """
    from rs import ResidualStress as RS
    from copy import copy
    ## 1. Read original SF/IG/FLow
    RS_model = RS(mod_ext=None,
                  fnmod_ig='igstrain_fbulk_ph1.out',
                  fnmod_sf='igstrain_fbulk_ph1.out',
                  i_ip=1)
    _SF_   = RS_model.dat_model.sf[::]
    _IG_   = RS_model.dat_model.ig[::]
    _Flow_ = RS_model.dat_model.flow; _Flow_.get_eqv()
    print _Flow_.epsilon_vm
    Flow   = copy(_Flow_)
    _nstp_ = _Flow_.nstp
    print _nstp_

    ## 2. Create a set of SF/IG/Flow interpolated at
    #   several plastic increments

    ##   2-1. Reduce the SF/IG/FLow nstp
    # Half of the original plastic increments


    if type(ss).__name__=='int':
        SF = _SF_[::ss]; IG = _IG_[::ss]
        Flow.epsilon = Flow.epsilon.swapaxes(0,-1)[::ss].swapaxes(0,-1)
        Flow.sigma   = Flow.sigma.swapaxes(0,-1)[::ss].swapaxes(0,-1)
        Flow.nstp    = Flow.nstp / ss
        Flow.get_eqv()
    elif type(ss).__name__=='list':
        SF = _SF_[ss]; IG = _IG_[ss]
        Flow.epsilon = Flow.epsilon[:,:,ss]
        Flow.sigma   = Flow.sigma[:,:,ss]
        Flow.nstp    = len(ss)
        Flow.get_eqv()

    ##   2-2. Create the SF object
    import sfig_class
    #      2-2-1. Original SF
    SF0 = _SF_.swapaxes(1,-1).swapaxes(1,2)
    StressFactor0 = sfig_class.SF()
    StressFactor0.add_data(
        sf=SF0[::]*1e-6,phi=RS_model.dat_model.phi[::]*180./np.pi,
        psi=RS_model.dat_model.psi[::]*180./np.pi)
    StressFactor0.flow = _Flow_; StressFactor0.flow.get_eqv()
    StressFactor0.mask_vol()

    #      2-2-2. Rearrange SF [stp,nij,nphi,npsi] -> [nstp,nphi,nspi,nij]
    SF = SF.swapaxes(1,-1).swapaxes(1,2)
    StressFactor = sfig_class.SF()
    StressFactor.add_data(
        sf=SF[::]*1e-6,phi=RS_model.dat_model.phi[::]*180./np.pi,
        psi=RS_model.dat_model.psi[::]*180./np.pi)
    StressFactor.flow = Flow
    StressFactor.flow.get_eqv()
    ##     2-2-3. Interpolate them at strains
    StressFactor.interp_strain(epsilon_vm = _Flow_.epsilon_vm,
                               iopt=iopt)
    StressFactor.flow = _Flow_
    StressFactor.flow.get_eqv()
    StressFactor.nstp = StressFactor.flow.nstp

    ##   2-3. Create the IG object
    ## IG0 = _IG_.swapaxes(1,-1).swapaxes(1,2)
    IG0 = _IG_[::]
    IGStrain0 = sfig_class.IG()
    IGStrain0.add_data(
        ig=IG0[::],phi=RS_model.dat_model.phi[::]*180./np.pi,
        psi=RS_model.dat_model.psi[::]*180./np.pi)
    IGStrain0.flow = _Flow_; IGStrain0.flow.get_eqv()
    ## IGStrain0.mask_vol()

    #      2-2-2. Rearrange IG [stp,nij,nphi,npsi] -> [nstp,nphi,nspi,nij]
    ## IG = IG.swapaxes(1,-1).swapaxes(1,2)
    IGStrain = sfig_class.IG()
    IGStrain.add_data(
        ig=IG[::],phi=RS_model.dat_model.phi[::]*180./np.pi,
        psi=RS_model.dat_model.psi[::]*180./np.pi)
    IGStrain.flow = Flow
    IGStrain.flow.get_eqv()
    ##     2-2-3. Interpolate them at strains
    IGStrain.interp_strain(epsilon_vm = _Flow_.epsilon_vm,
                           iopt=iopt)
    IGStrain.flow = _Flow_
    IGStrain.flow.get_eqv()
    IGStrain.nstp = IGStrain.flow.nstp

    StressFactor0.plot()
    StressFactor.plot()
    IGStrain0.plot()
    IGStrain.plot()
    return StressFactor, IGStrain

def influence_of_intp(ss=2,bounds=[0,0.5],
                      psi_nbin=13,iplot=False,
                      hkl=None,
                      iscatter=False,iwgt=False,
                      sigma=5e-5,
                      intp_opt=0):
    """
    Parametric study to demonstrate the influence of
    psi binning

    Arguments
    =========
    ss       = 2 (step size)
    bounds   = sin2psi bounds
    psi_nbin = Number of psi data points in use
    hkl      = None
    iscatter = False
    iwgt     = False
    """
    from MP.mat.mech import find_err
    from rs import filter_psi2
    from rs_ex import ex_consistency as main
    from MP.lib import mpl_lib,axes_label
    import matplotlib.pyplot as plt
    wide_fig     = mpl_lib.wide_fig
    deco         = axes_label.__deco__
    fig = wide_fig(nw=3,nh=1);axs=fig.axes

    ## Use the reduced set over the consistency check
    sf,ig = use_intp_sfig(ss=ss,iopt=intp_opt)
    sf_ext = sf.sf.swapaxes(1,-1).swapaxes(-2,-1)[::]*1e6
    ig_ext = ig.ig[::]

    ##
    # Filtering against sin2psi
    sf_ext = filter_psi2(
        obj=sf_ext,sin2psi=sf.sin2psi,bounds=bounds)
    ig_ext = filter_psi2(
        obj=ig_ext,sin2psi=sf.sin2psi,bounds=bounds)

    # # # Reduce binning
    ## consistency check
    rst = main(sin2psimx=bounds[1],psi_nbin=psi_nbin,
               sf_ext=sf_ext,ig_ext=ig_ext,
               iplot=iplot,hkl=hkl,iscatter=iscatter,
               sigma=sigma,
               iwgt=iwgt)

    fw, fd = rst[1], rst[2]

    axs[0].plot(fw.epsilon_vm,fw.sigma_vm,'b-x',
                label='Weight Avg.')
    axs[0].plot(fd.epsilon_vm,fd.sigma_vm,'k+',
                label='Diff Stress')

    if type(ss).__name__=='int':
        x = fd.epsilon_vm[::ss]; y = fd.sigma_vm[::ss]
    elif type(ss).__name__=='list':
        x = fd.epsilon_vm[ss]; y = fd.sigma_vm[ss]

    label='SF/IG acqusition'
    axs[0].plot(x,y,'o',mec='r',mfc='None',
                alpha=0.8,label=label)
    npoints = len(fw.sigma[0,0])

    axs[1].plot(fw.sigma[0,0],fw.sigma[1,1],'b-x')
    axs[1].plot(fd.sigma[0,0],fd.sigma[1,1],'k+')

    wgtx, wgty = fw.sigma[0,0], fw.sigma[1,1]
    dsax, dsay = fd.sigma[0,0], fd.sigma[1,1]
    for i in range(npoints):
        axs[1].plot([wgtx[i],dsax[i]],
                    [wgty[i],dsay[i]],'k-',alpha=0.2)

    e = find_err(fw,fd)
    axs[2].plot(fw.epsilon_vm, e, 'x')

    if type(ss).__name__=='int':
        axs[2].plot(fw.epsilon_vm[::ss],e[::ss],
                    'o',mec='r',mfc='None',label=label)
    elif type(ss).__name__=='list':
        axs[2].plot(fw.epsilon_vm[ss],e[ss],
                    'o',mec='r',mfc='None',label=label)

    axes_label.__eqv__(axs[0],ft=10)
    axs[1].set_aspect('equal')
    axs[1].set_xlabel(r'$\bar{\Sigma}_{11}$',dict(fontsize=15))
    axs[1].set_ylabel(r'$\bar{\Sigma}_{22}$',dict(fontsize=15))
    axs[1].set_ylim(-100,700); axs[1].set_xlim(-100,700)

    axs[0].legend(loc='best',fontsize=10).get_frame().set_alpha(0.5)
    deco(iopt=8,ft=15,ax=axs[2])

    if type(ss).__name__=='int':    dum=ss
    elif type(ss).__name__=='list': dum =len(ss)
    fig.savefig('flow_dd_bin%i_ss%i.pdf'%(psi_nbin,dum))
    plt.close(fig)

    return fw, e

def influence_of_nbin(
        ss=3,bounds = [0,0.5],
        nbins = [11, 19, 25, 51],
        iscatter=False,
        sigma=1e-5,
        iwgt=False,
        intp_opt=0):
    """
    Influence of psi bin size

    Arguments
    =========
    ss = 3
    bounds = [0.0, 0.5]
    nbins = [11, 19, 25, 51]
    iscatter = False
    iwgt     = False
    intp_opt = 0   (Interpolation option)
    """
    from MP.lib import mpl_lib,axes_label
    import matplotlib.pyplot as plt
    fancy_legend = mpl_lib.fancy_legend
    wide_fig     = mpl_lib.wide_fig
    deco         = axes_label.__deco__
    fig = wide_fig(nw=1,nh=1);ax=fig.axes[0]

    Y = []
    for i in range(len(nbins)):
        nb = nbins[i]
        fw, e = influence_of_intp(
            ss=ss, bounds=bounds,
            psi_nbin = nb,iplot=False,
            iscatter=iscatter,sigma=sigma,
            iwgt=iwgt,
            intp_opt=intp_opt)
        x = fw.epsilon_vm[::]
        y = e[::]
        ax.plot(x,y,label=nb)
        Y.append(y)


    fancy_legend(ax=ax,size=10)
    deco(iopt=8,ft=15,ax=ax)

    if type(ss).__name__=='int':    dum=ss
    elif type(ss).__name__=='list': dum =len(ss)
    fig.savefig('ss%i_err.pdf'%dum)
    plt.close('all')

    ## Y [nbins, nsteps]
    return x, Y

def influence_of_nbin_scatter(
        ss=3,bounds=[0.0, 0.5],
        nbins=[7, 13, 23, 33],
        iscatter=True,nsample=5,iwgt=True,
        sigma=5e-5,intp_opt=0,iplot=False):
    """
    Repeat influence_of_nbin examination
    to verify the error in stress analysis
    pertaining to that in eps(hkl,phi,psi)
    """
    from MP.lib import mpl_lib,axes_label
    import matplotlib.pyplot as plt
    fancy_legend = mpl_lib.fancy_legend
    wide_fig     = mpl_lib.wide_fig
    deco         = axes_label.__deco__
    if iplot:
        fig = wide_fig(nw=2,nh=1);
        ax=fig.axes[0]
        ax1=fig.axes[1]

    Y = []
    for i in range(nsample):
        x, y = influence_of_nbin(
            ss=ss,bounds=bounds,
            nbins=nbins, iscatter=iscatter,
            sigma=sigma,
            iwgt=iwgt,intp_opt=intp_opt)
        Y.append(y)
    ## Y [nsample, nbin, nstp]
    Y = np.array(Y).swapaxes(0,-1).swapaxes(0,1)
    ## Y [nbin, nstp, nsample]
    nbin, nstp, nsamp = Y.shape

    for i in range(nbin):
        e = []; s = []
        for j in range(nstp):
            mean = Y[i,j,:].mean()
            std  = Y[i,j,:].std()
            e.append(mean)
            s.append(std)
        if iplot:
            ax1.plot(x,e,'-o',label=nbins[i])
            ax.errorbar(x,e,yerr=std,fmt='x',label=nbins[i])

    if iplot:
        if type(ss).__name__=='int':
            ax1.plot(x[::ss],np.zeros((len(x[::ss]),)),'r|',ms=12)
            ax.plot(x[::ss],np.zeros((len(x[::ss]),)),'r|',ms=8)
        elif type(ss).__name__=='list':
            ax1.plot(x[ss],np.zeros((len(x[ss]),)),'r|',ms=12)
            ax.plot(x[ss],np.zeros((len(x[ss]),)),'r|',ms=8)

        ax.set_ylim(0.,); ax.set_xlim(0.,ax.get_xlim()[1]*1.05)
        ax1.set_ylim(0.,); ax1.set_xlim(0.,ax1.get_xlim()[1]*1.05)
        fancy_legend(ax=ax, size=7,ncol=2)
        fancy_legend(ax=ax1,size=7,ncol=2)
        deco(iopt=8,ft=15,ax=ax);  deco(iopt=8,ft=15,ax=ax1)

        if type(ss).__name__=='int':    dum=ss
        elif type(ss).__name__=='list': dum =len(ss)
        fig.savefig('ss_%i_err_scatter_nsamp_%i.pdf'%(dum,nsample))
        plt.close('all')
    return x, e

def influence_of_cnts_stats(
        ss=3,bounds=[0.,0.3257],
        nbins=13, sigmas=[1e-5, 2e-5, 5e-5, 1e-4],iwgt=False,
        nsample=5,intp_opt=0,iplot=False):
    from MP.lib import mpl_lib,axes_label
    import matplotlib.pyplot as plt

    if iplot==False:
        plt.ioff()

    fancy_legend = mpl_lib.fancy_legend
    wide_fig     = mpl_lib.wide_fig
    deco         = axes_label.__deco__
    fig = wide_fig(nw=2,nh=1);
    ax1=fig.axes[0]; ax2=fig.axes[1]

    M = []
    for i in range(len(sigmas)):
        Y = []
        for j in range(nsample):
            x, y = influence_of_nbin_scatter(
                ss=ss,bounds=bounds,
                nbins=[nbins],
                iscatter=True,nsample=1,
                iwgt=iwgt,sigma=sigmas[i],
                intp_opt=intp_opt,
                iplot=False)
            Y.append(y)
        Y = np.array(Y).T
        M = []; S=[]
        for k in range(len(x)):
            M.append(Y[k].mean())
            S.append(Y[k].std())
        ax1.plot(x,M,label='%6.0e'%sigmas[i])
        ax2.errorbar(x,M,yerr=S,label='%6.0e'%sigmas[i])

    if type(ss).__name__=='int':
        ax1.plot(x[::ss],np.zeros((len(x[::ss]),)),'o',mec='r',mfc='None',ms=8)
        ax2.plot(x[::ss],np.zeros((len(x[::ss]),)),'o',mec='r',mfc='None',ms=8)
    elif type(ss).__name__=='list':
        ax1.plot(x[ss],np.zeros((len(x[ss]),)),'o',mec='r',mfc='None',ms=8)
        ax2.plot(x[ss],np.zeros((len(x[ss]),)),'o',mec='r',mfc='None',ms=8)

    ax1.set_ylim(0.,); ax1.set_xlim(0.,ax1.get_xlim()[1]*1.05)
    ax1.set_title(r'Error in $\varepsilon^\mathrm{hkl}$')
    deco(iopt=8,ft=15,ax=ax1)
    fancy_legend(ax=ax1, size=7,ncol=2)
    ax2.set_ylim(0.,); ax2.set_xlim(0.,ax2.get_xlim()[1]*1.05)
    ax2.set_title(r'Error in $\varepsilon^\mathrm{hkl}$')
    deco(iopt=8,ft=15,ax=ax2)
    fancy_legend(ax=ax2, size=7,ncol=2)

    fig.savefig('ee.pdf')
    if iplot==False:
        plt.close('all')
        plt.ion()
    return x, M, S

def compare_exp_mod(ntot_psi=21):
    import numpy as np
    import matplotlib.pyplot as plt
    from pepshkl import reader4
    from RS import sff_converter
    from rs_exp import read_IGSF
    from MP.lib import mpl_lib
    from MP.mat.mech import FlowCurve as FC
    wf = mpl_lib.wide_fig
    sff_converter.main(fn='temp.sff',difile=None,itab=True,
                       ieps0=4,  fn_str='STR_STR.OUT')
    SF, dum = read_IGSF(fn='temp.sff',fn_str='STR_STR.OUT')
    SF.reduce_psi(bounds=[0.,0.5],ntot_psi=ntot_psi)
    SF.mask_vol()
    SF.plot(ylim=[-2,2])

    ## biaxial
    flow = FC()
    exx = open('YJ_Bsteel_BB.sff','r').read().split('\n')[4].split()[1:]
    exx = np.array(exx,dtype='float'); eyy = exx[::]; ezz = -(exx+eyy)
    flow.epsilon_vm = abs(ezz)
    flow.nstp = len(ezz)
    SF, dum = read_IGSF(fn='YJ_Bsteel_BB.sff',fc=flow)
    SF.plot(mxnphi=3,ylim=[-2,2])

def influence_of_intp_extp(
        ss=1,
        bounds=[0.,0.5],
        nbins=13,
        sigmas=[1e-11],iwgt=False,
        nsample=5):
    """
    Influence of choice of interpolation/extrapolation
    method on the resulting 'Uncertainity' in stress
    analysis.

    Arguments
    =========
    ss = 1
    bounds = [0., 0.5]
    nbins = 13
    sigmas=[1e-11],
    nsample=5
    """
    from MP.lib import mpl_lib,axes_label
    import matplotlib.pyplot as plt

    iopts = [0,1,2,3,4,7]
    labs  = ['Piece-wise linear',
             'Nearest data',
             'Cubic',
             'Quadratic',
             'Linear fit',
             'Power law fit']

    xs=[];Ms=[];Ss=[]
    for iopt in range(len(iopts)):
        x,M,S = influence_of_cnts_stats(
            ss=ss,bounds=bounds,
            nbins=nbins,
            sigmas=sigmas,
            nsample=nsample,iwgt=False,
            intp_opt=iopt,iplot=False)
        xs.append(x)
        Ms.append(M)
        Ss.append(S)

    fig=mpl_lib.wide_fig(nw=1,nh=1);ax=fig.axes[0]
    for iopt in range(len(iopts)):
        x=xs[iopt]
        M=Ms[iopt]
        s=Ss[iopt]
        ax.errorbar(x,M,yerr=S,label=labs[iopt])
    ax.legend(loc='best').get_frame().set_alpha(0.5)
    fig.savefig('dum.pdf')
