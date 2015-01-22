"""
A collection of scripts that make use of residual stress module
"""

import numpy as np
from numpy import pi, sin, cos
from lib import write_args

def ex(ifig=50,
       exp_ref=['exp_dat/Bsteel/EXP_BULGE_JINKIM.txt',
                'exp_dat/Bsteel/uni/avgstr_000.txt'],
       exp_lab=['Exp bulge','Exp uniaxial'],
       mod_ref='STR_STR.OUT'):
    """
    Arguments
    =========
    exp_ref = ['exp_dat'/Bsteel/EXP_BULGE_JINKIM.txt']
    exp_lab = ['Exp bulge', 'Exp uniaxial')
    mod_ref = 'STR_STR.OUT'
    """
    fig=plt.figure(ifig);ax=fig.add_subplot(111)
    myrs = ResidualStress()
    strains = myrs.straine #(20,6)
    # strains = myrs.strainm #(4,6)
    strain_eff = strains.T[0]+strains.T[1]
    strain_eff = strain_eff.T
    stress = []
    for i in range(len(strain_eff)):
        dum = myrs.analysis(iopt=0,istp=i)
        stress.append((dum[0] + dum[1])/2.)
    ax.plot(strain_eff,stress,'-x',label='Model SF/IG/ehkl')

    stress = []
    for i in range(len(strain_eff)):
        dum = myrs.analysis(iopt=1,istp=i)
        stress.append((dum[0] + dum[1])/2.)
    ax.plot(strain_eff,stress,'-x',label='Exp SF/IG/ehkl')

    stress = []
    for i in range(len(strain_eff)):
        dum = myrs.analysis(iopt=2,istp=i)
        stress.append((dum[0] + dum[1])/2.)
    ax.plot(strain_eff,stress,'-x',label='Model SF/IG + Exp ehkl')


    for i in range(len(exp_ref)):
        exp_ref = exp_ref[i]
        x,y=np.loadtxt(exp_ref).T
        ax.plot(x,y,'--',label=exp_lab[i])

    dum=np.loadtxt(mod_ref,skiprows=1).T;
    x=dum[2]+dum[3];y=(dum[8]+dum[9])/2.;

    ax.plot(x,y,'--',label='EVPSC biaxial')
    __deco__(ax,iopt=3)

    ax.legend(loc='best',fancybox=True).get_frame().set_alpha(0.5)
    fig.tight_layout()
    plt.show()
    return stress

def ex_consistency(
        ifig=50,nxphi=3,exp_ref=[],exp_lab=[],mod_ext=None,
        mod_ref='STR_STR.OUT',sin2psimx=None,iscatter=False,
        sigma=5e-5,psimx=None,psi_nbin=1,ig_sub=True,istep=None,
        hkl=None,iplot=True,iwind=False,wdeg=2,ipsi_opt=1,
        fn_sff=None,pmargin=None,path='',sf_ext=None,ig_ext=None,
        vf_ext=None,iwgt=False,verbose=False,ilog=False):
    """
    Consistency check between 'weighted average' stress and
    the stress obtained following the stress analysis method
    (SF, IG strain)

    ----------------------------------------
    ## Data visualization options
    ifig = 50
    nxphi     : display only first nxphi of results
                along phi axis
    hkl       : hkl of plane, for the sake of labels.
    path      : place holder for strain path




    ----------------------------------------
    ## Data process parameters
    #1. Main options
    sf_ext    : Overwrite stress factor
    ig_ext    : Overwrite IG strain
    vf_ext    : Overwrite grain volume fraction (nstp,nphi,npsi)
    iscatter (False) : introducing a random scattering of 'ehkl'

    #1. tilting angle restriction/treatments
    sin2psimx : limiting the maximum sin2psi values, with which
                stress-fitting is carried out
    psimx     : limiting the maximum psi value
    psi_nbin  : If other than 1, limit the number of data

    #2. IG strain-specific
    ig_sub    : flag whether or not subtract the IG strain

    #3. Weight treatments
    iwgt      : Whether or not accounting for 'weight'
    pmargin   : portional margin of volume that should exceed to
                contribute to the ehkl/SF/IG in model_rs
    #4. Misc.
    exp_ref   : experimental reference
    mod_ref   : model's weighted average flow curves are given

    ----------------------------------------
    ## misc. options
    iplot (True) : flag whether or not MPL plot is performed
    ipsi_opt 0: sin2psi
             1: sing(psi) * sin2psi
             2: psi
    istep     : If other than None, analysis is carried out
                only for the given istep

    ----------------------------------------
    ## debugging options
    verbose   : False
    ilog      : False
    """
    if ilog:
        fn = 'ex_consistency.log'
        f = open(fn,'w')
        write_args(
            f=f,ihead=True,ifig=ifig,nxphi=nxphi,exp_ref=exp_ref,
            exp_lab=exp_lab,mod_ext=mod_ext,mod_ref=mod_ref,
            sin2psimx=sin2psimx,iscatter=iscatter,sigma=sigma,
            psimx=psimx,psi_nbin=psi_nbin,ig_sub=ig_sub,
            istep=istep,hkl=hkl,iplot=iplot,iwind=iwind,
            wdeg=wdeg,ipsi_opt=ipsi_opt,fn_sff=fn_sff,
            pmargin=pmargin,path=path,sf_ext=sf_ext,
            ig_ext=ig_ext,vf_ext=vf_ext,iwgt=iwgt,
            verbose=verbose,ilog=ilog)
        f.close()
        print 'log has been saved to ',fn

    from rs import ResidualStress,u_epshkl,filter_psi,\
        filter_psi3,psi_reso, psi_reso2, psi_reso3,psi_reso4

    from MP.mat import mech # mech is a module
    FlowCurve = mech.FlowCurve

    if iplot:
        from matplotlib import pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        from MP.lib import mpl_lib,axes_label
        wide_fig     = mpl_lib.wide_fig
        fancy_legend = mpl_lib.fancy_legend
        ## Collection of figures at various plastic strains
        fe   = PdfPages('all_ehkl_fits_%s_%s.pdf'%(hkl,path))
        fs   = PdfPages('all_stress_factors_%s_%s.pdf'%(hkl,path))
        f_er = PdfPages('all_Ei-ehkl-e0_%s_%s.pdf'%(hkl,path))
        fig1 = wide_fig(ifig,nw=2,nh=1,left=0.2,uw=3.5,
                        w0=0,w1=0.3,right=0,iarange=True)

        ## ax1: Equivalent Stress/Strain
        ## ax2: Stress path in the plane stress space (RD/TD)
        ax1 = fig1.axes[0]; ax2 = fig1.axes[1]
        pass

    #------------------------------------------------------------#
    ## i_ip = 1: ioption for the model data
    model_rs = ResidualStress(
        mod_ext=mod_ext,fnmod_ig='igstrain_fbulk_ph1.out',
        fnmod_sf='igstrain_fbulk_ph1.out',i_ip=1)

    ## Process the sf/eps0/ehkl/wgt and so forth
    ## according to the parameters given
    ivf_ext=True; isf_ext=True; iig_ext=True
    if type(sf_ext)==type(None):isf_ext=False
    if type(ig_ext)==type(None):iig_ext=False
    if type(vf_ext)==type(None):ivf_ext=False

    """
    if given, do not process
    if yes, do process.

    ## final data should be saved to
    'model_sfs'
    'model_igs'
    'model_ehkl'
    And eventually to 'model_tdats' inside the loop
    """

    ## SF/IG/ehkl
    model_ehkls = model_rs.dat_model.ehkl[::]
    if isf_ext and iig_ext:
        model_sfs = sf_ext[::]
        model_igs = ig_ext[::]
    elif isf_ext!=iig_ext:
        raise IOError, 'isf_ext should equal to iig_ext'
    ## if isf_ext False and isf_ext False
    else:
        model_sfs = model_rs.dat_model.sf[::]
        model_igs = model_rs.dat_model.ig[::]

    ## VF
    if not(ivf_ext):
        model_vfs = model_rs.dat_model.vf[::]
    else: model_vfs = vf_ext[::]

    ## whether or not vf would be used as weights in
    ## the least-sq estimator
    if not(iwgt): wgt = None # overwrite wgt

    # Apply process
    # 1. Confine the range of sin2psi (or psi)
    # 2. Finite number of tiltings
    # 3. Assign tdat
    # 4. Perturb ehkl (common)
    # 5. Filter based on vf?

    ## Unstaged but the 'raw' arrays
    raw_psis = model_rs.dat_model.psi[::]
    raw_vfs  = model_vfs[::]
    raw_ehkl = model_rs.dat_model.ehkl[::]
    raw_sfs  = model_sfs

    ## staged arrays for stress estimation
    model_rs.psis = model_rs.dat_model.psi[::]
    model_rs.phis = model_rs.dat_model.phi[::]
    model_rs.npsi = len(model_rs.psis)
    model_rs.nphi = len(model_rs.phis)
    sin2psis_init = np.sin(model_rs.psis)**2
    # 1. Limit the range of sin2psi (or psi)
    if type(sin2psimx)!=type(None) or \
       type(psimx)!=type(None):
        if type(sin2psimx)!=type(None):
            bounds=[0., sin2psimx]
        elif type(psimx)!=type(None):
            bounds=[0., np.sin(psimx*np.pi/180.)**2]

        raw_sfs,model_sfs,model_igs,model_vfs,model_ehkls,raw_psis \
            = filter_psi3(
                sin2psis_init,bounds,raw_sfs,model_sfs,model_igs,
                model_vfs,model_ehkls,raw_psis)

        ## reduce the psis in model_rs
        model_rs.psis, = filter_psi3(
            sin2psis_init,bounds,
            model_rs.psis[::])
        model_rs.npsi = len(model_rs.psis)

    # 2. Finite number of tiltings
    if psi_nbin!=1:
        model_sfs, model_igs, model_vfs, model_ehkls \
            = psi_reso4(model_rs.psis, psi_nbin,
                        model_sfs,model_igs,model_vfs,
                        model_ehkls)
        model_rs.psis, = psi_reso4(
            model_rs.psis[::],psi_nbin,model_rs.psis[::])
        model_rs.npsi = len(model_rs.psis)

    # 3. Assign tdat
    if ig_sub: model_tdats = model_ehkls - model_igs
    else: model_tdats = model_ehkls[::]

    # 4. Perturb ehkl (common)
    if iscatter:
        nstp,nphi,npsi = model_ehkls.shape
        tdats = np.zeros((nstp,nphi,npsi))
        for istp in range(nstp):
            for iphi in range(nphi):
                tdats[istp,iphi,:] = u_epshkl(
                    model_tdats[istp,iphi],
                    sigma=sigma)
    else: tdats=model_tdats[::]

    # 5. Filter based on vf
    # if not(ivf_ext): model_rs.dat_model.mask_vol()
    # elif ivf_ext:
    #     shape1 = model_rs.dat_model.vf.shape
    #     shape2 = vf_ext.shape
    #     if shape1==shape2: model_rs.dat_model.vf[::] =\
    #        vf_ext[::]
    #     else:raise IOError, 'shape mismatch'
    #     model_rs.dat_model.mask_vol()

    # if pmargin!=None: model_rs.dat_model.\
    #    mask_vol_margin(pmargin)


    ## end of data process
    #------------------------------------------------------------#

    if mod_ext==None: mod_ref='STR_STR.OUT'
    else: mod_ref='%s.%s'%(mod_ref.split('.')[0],mod_ext)

    flow_weight = FlowCurve(name='Model weighted')
    flow_weight.get_model(fn=mod_ref)
    flow_weight.get_eqv() ## calc Von Mises stress/strain

    if len(flow_weight.epsilon_vm)<5: lc='k.'
    else:                             lc='k-'

    if iplot:
        ax1.plot(flow_weight.epsilon_vm,flow_weight.sigma_vm,
                 lc,label=r'$\langle \sigma^c \rangle$',
                 alpha=1.0)
        axes_label.__eqv__(ax1,ft=10)

    ## plot all stress factors at individual deformation levels
    stress = []
    if verbose: print '%8s%8s%8s%8s%8s%8s'%(
        'S11','S22','S33','S23','S13','S12')

    ############################################################
    ## *Serial* Loop over the deformation steps
    # nstp = model_rs.dat_model.nstp
    nstp = 3 ## debugging
    for istp in range(nstp):
        """
        Dimensions of data arrays for:
        ==============================
        sf     (nstp, k, nphi, npsi)
        ig     (nstp, nphi, npsi)
        ehkl   (nstp, nphi, npsi)
        strain (nstp, 6)
        vf     (nstp, nphi, npsi)
        """
        model_rs.sf = model_sfs[istp][::]
        model_rs.eps0 = model_igs[istp][::]
        model_rs.ehkl = model_ehkls[istp][::]
        model_rs.tdat = tdats[istp][::]

        #-----------------------------------#
        ## find the sigma ...
        s11 = model_rs.dat_model.flow.sigma[0,0][istp]
        s22 = model_rs.dat_model.flow.sigma[1,1][istp]

        ## find the stress by fitting the elastic strains
        dsa_sigma = model_rs.find_sigma(
            ivo=[0,1],
            init_guess=[0,0,0,0,0,0],#init_guess=[s11,s22,0,0,0,0],
            weight = wgt) # None

        if verbose:
            for i in range(6): print '%+7.1f'%(dsa_sigma[i]),
            print ''
        stress.append(dsa_sigma)

        full_Ei = np.zeros((model_rs.nphi,len(raw_psis)))
        for iphi in range(model_rs.nphi):
            for ipsi in range(len(raw_psis)):
                for k in range(6):
                    full_Ei[iphi,ipsi] \
                        = full_Ei[iphi,ipsi]+\
                        raw_sfs[istp,k,iphi,ipsi]*dsa_sigma[k]

        #-----------------------------------#
        if istp==0: ileg=True
        else:       ileg=False

        if (istep!=None and istp==istep) or\
           (istep==None and istp==nstp-1)\
           and iplot:
            fig2,fig3,fig4=__model_fit_plot__(
                model_rs,ifig=ifig+istp*2+10,
                istp=istp, nxphi=nxphi,stress_wgt=None,
                ivo=None,hkl=hkl,ileg=ileg,iwind=iwind,
                wdeg=wdeg)
        elif iplot:
            plt.ioff()
            f1,f2,f3=__model_fit_plot__(
                model_rs,ifig=ifig+istp*2+10,
                ## stress_wgt: the mechanical stress.
                ## will be used as a reference line
                istp=istp,nxphi=nxphi,stress_wgt=[s11,s22,0,0,0,0],
                wgt=raw_vfs[istp][::],wgt_psi=raw_psis,
                full_Ei=full_Ei,
                ivo=[0,1],hkl=hkl,ileg=ileg,iwind=False,
                ipsi_opt=ipsi_opt)
            fs.savefig(f2);fe.savefig(f1);f_er.savefig(f3)
            f1.clf();plt.draw();f2.clf();plt.draw();f3.clf();plt.draw()
            plt.close(f1);plt.close(f2);plt.close(f3);plt.ion()
    # end of the serial loop over deformation steps
    ############################################################

    if iplot: fe.close(); fs.close(); f_er.close()

    stress   = np.array(stress).T # diffraction stress
    flow_dsa = FlowCurve(name='Diffraction Stress')
    flow_dsa.get_6stress(stress)
    flow_dsa.get_33strain(model_rs.dat_model.flow.epsilon)
    flow_dsa.get_eqv()


    ## Various plots
    if iplot:
        ax1.plot(flow_dsa.epsilon_vm,flow_dsa.sigma_vm,'k+',
                 label=r'$\hat{\sigma}^{RS}$')
        for i in range(len(exp_ref)):
            f = exp_ref[i]; lab = exp_lab[i]
            edat = np.loadtxt(f).T
            ax1.plot(edat[0],edat[1],'-',lw=2,label=lab)
            ## ax1.set_ylim(0.,800)
        fancy_legend(ax1,size=10,nscat=2)

    sigma_wgt = flow_weight.sigma

    if iplot:
        ax2.plot(sigma_wgt[0,0],sigma_wgt[1,1],'k-')
        ax2.plot(flow_dsa.sigma[0,0],flow_dsa.sigma[1,1],'k+')

        ## connector
        npoints = len(sigma_wgt[0,0])
        wgtx = sigma_wgt[0,0];      wgty = sigma_wgt[1,1]
        dsax = flow_dsa.sigma[0,0]; dsay = flow_dsa.sigma[1,1]
        for i in range(npoints):
            ax2.plot([wgtx[i],dsax[i]],[wgty[i],dsay[i]],'k-',alpha=0.2)

        ax2.set_ylim(-100,700); ax2.set_xlim(-100,700)
        ax2.set_aspect('equal')
        ax2.set_xlabel(r'$\bar{\Sigma}_{11}$',dict(fontsize=15))
        ax2.set_ylabel(r'$\bar{\Sigma}_{22}$',dict(fontsize=15))
        ax2.locator_params(nbins=3)
        ax2.set_xticks(np.linspace(300,700,3),dict(fontsize=4))
        ax2.set_yticks(np.linspace(300,700,3),dict(fontsize=4))
        ax2.grid('on'); plt.show()

        ## save figures
        fig1.savefig('flow_%s_%s.pdf'%(hkl,path))
        ## fig2.savefig('ehkl_%s_fit_%s.pdf'%(hkl,path))
        ## fig3.savefig('sf_%s_%s.pdf'%(hkl,path))
        ## fig4.savefig('ehkl_fit_err_%s_%s.pdf'%(hkl,path))
        # close figures
        plt.close(fig1); plt.close(fig2); plt.close(fig3); plt.close(fig4)

    return model_rs, flow_weight, flow_dsa


def minimal_parallel_ex_consistency_(
    ifig=50,nxphi=3,
    exp_ref=[],exp_lab=[],mod_ext=None,
    mod_ref='STR_STR.OUT',sin2psimx=None,
    iscatter=False,sigma=5e-5,psimx=None,psi_nbin=1,
    ig_sub=True,istep=None,hkl=None,iplot=True,
    iwind=False,wdeg=2,ipsi_opt=1,fn_sff=None,
    pmargin=None,path='',
    sf_ext=None,ig_ext=None,iwgt=False):
    """
    minimal parallel version of ex_consistency
    parallel in the sense that stress analysis is done
    for individual step in parallel

    Remove all plots.
    """
    from rs import ResidualStress,u_epshkl,filter_psi,\
        filter_psi2,psi_reso, psi_reso2, psi_reso3
    from MP.mat import mech # mech is a module
    FlowCurve = mech.FlowCurve

    model_rs = ResidualStress(
        mod_ext=mod_ext,
        fnmod_ig='igstrain_fbulk_ph1.out',
        fnmod_sf='igstrain_fbulk_ph1.out',
        i_ip=1)

    ## masking array element based on diffraction volume
    model_rs.dat_model.mask_vol()
    if pmargin!=None: model_rs.dat_model.\
            mask_vol_margin(pmargin)
    if mod_ext==None: mod_ref='STR_STR.OUT'
    else:             mod_ref='%s.%s'%(
        mod_ref.split('.')[0],mod_ext)

    flow_weight = FlowCurve(name='Model weighted')
    flow_weight.get_model(fn=mod_ref)
    flow_weight.get_eqv() ## calc Von Mises stress/strain

    if len(flow_weight.epsilon_vm)<5: lc='k.'
    else:                             lc='k-'

    stress = []
    print '%8s%8s%8s%8s%8s%8s'%(
        'S11','S22','S33','S23','S13','S12')

    ## 'Stage' model diffraction orientations to model_rs
    model_rs.phis = model_rs.dat_model.phi
    model_rs.psis = model_rs.dat_model.psi
    model_rs.nphi = len(model_rs.phis)
    model_rs.npsi = len(model_rs.psis)

    ############################################################
    ## *Serial* Loop over the deformation steps
    for istp in range(model_rs.dat_model.nstp):
        """
        Dimensions of data arrays for:
        ==============================
        sf     (nstp, k, nphi, npsi)
        ig     (nstp, nphi, npsi)
        ehkl   (nstp, nphi, npsi)
        strain (nstp, 6)
        vf     (nstp, nphi, npsi)
        """
        ## 'Stage' relevant properties to be used for analysis
        model_rs.sf   = model_rs.dat_model.sf[istp][::]
        model_rs.eps0 = model_rs.dat_model.ig[istp][::]
        model_rs.ehkl = model_rs.dat_model.ehkl[istp][::]
        wgt           = model_rs.dat_model.vf[istp][::]

        ## whether or not intergranular strain is subtracted.
        if ig_sub: model_rs.tdat = model_rs.ehkl - model_rs.eps0
        else:      model_rs.tdat = model_rs.ehkl[::]
        tdat_ref = model_rs.tdat[::]

        ## Inducing counting stats noise in e(hkl)
        if iscatter:
            tdat_scatter = []
            for iphi in range(len(tdat_ref)):
                dum = u_epshkl(tdat_ref[iphi],sigma=sigma)
                tdat_scatter.append(dum)
            tdat_scatter = np.array(tdat_scatter)
            model_rs.tdat = tdat_scatter

        ## Use only finite range of psi tilts
        if type(sin2psimx)!=type(None) or \
           type(psimx)!=type(None):
            filter_psi(model_rs,sin2psimx=sin2psimx,psimx=psimx)
            wgt = filter_psi2(
                wgt,sin2psi=np.sin(model_rs.psis)**2,
                bounds =[0., sin2psimx])
            if type(sf_ext)!=type(None):
                model_rs.sf = sf_ext[istp]
            elif type(ig_ext)!=type(None):
                model_rs.ig = ig_ext[istp]

        ## Use a finite frequence of psi tilts
        if psi_nbin!=1:

            ## psi_reso3: Reduce elements along the psi axis
            wgt = psi_reso3(wgt[::],psi=model_rs.psis,ntot=psi_nbin)
            # ## psi_reso2: Make data nearly-equal spaced along psi
            # ## or along sin2psi given the number of desired data points
            # psi_reso2(model_rs,ntot=psi_nbin)

            ## psi_reso4 : using psi_reso3
            model_rs.sf, model_rs.eps0, model_rs.ehkl \
                = psi_reso4(psi,psi_nbin, model_rs.sf[::],
                            model_rs.eps0[::], model_rs.ehkl[::])
            if ig_sub: model_rs.tdat = model_rs.ehkl - model_rs.eps0
            else:      model_rs.tdat = model_rs.ehkl[::]
            tdat_ref = model_rs.tdat[::]



        #-----------------------------------#
        ## find the sigma ...
        s11 = model_rs.dat_model.flow.sigma[0,0][istp]
        s22 = model_rs.dat_model.flow.sigma[1,1][istp]

        if iwgt: pass
        else: wgt = None # overwrite wgt

        dsa_sigma = model_rs.find_sigma(
            ivo=[0,1],
            init_guess=[0,0,0,0,0,0],
            #init_guess=[s11,s22,0,0,0,0],
            weight = wgt # None
            )

        for i in range(6): print '%+7.1f'%(dsa_sigma[i]),
        print ''
        stress.append(dsa_sigma)
        #-----------------------------------#

    # end of the serial loop over deformation steps
    ############################################################

    stress   = np.array(stress).T # diffraction stress
    flow_dsa = FlowCurve(name='Diffraction Stress')
    flow_dsa.get_6stress(stress)
    flow_dsa.get_33strain(model_rs.dat_model.flow.epsilon)
    flow_dsa.get_eqv()

    sigma_wgt = flow_weight.sigma
    return model_rs, flow_weight, flow_dsa


def __model_fit_plot__(
        container,ifig,istp,nxphi=None,hkl=None,
        wgt=None,wgt_psi=None,full_Ei=None,
        stress_wgt=None,ivo=None,fig=None,figs=None,fige=None,
        c1='r',c2='b',m1='--',m2='-',isf=[True,True],
        ileg=True,iwind=False,wdeg=2,
        ipsi_opt=0):

    """
    Plot container's analyzed data
    """
    from MP.lib import mpl_lib, axes_label
    import lib; sin2psi_wind = lib.sin2psi_bounds
    sin2psi_opt = lib.sin2psi_opt
    wide_fig     = mpl_lib.wide_fig
    fancy_legend = mpl_lib.fancy_legend
    rm_lab       = mpl_lib.rm_lab
    tune_x_lim   = mpl_lib.tune_x_lim
    tune_xy_lim  = mpl_lib.tune_xy_lim
    deco         = axes_label.__deco__

    nphi = container.nphi; npsi = container.npsi
    phis = container.phis; psis = container.psis
    if nxphi!=None and nphi>nxphi:
        print 'Probed phis are redundant:', nphi
        print 'Only %i of phis axis are shown'%(nxphi)
        nphi = nxphi

    ivf=True
    #vf   = container.dat_model.vf[istp]
    #ngr  = container.dat_model.ngr[istp]
    if type(wgt)!=type(None): vf   = wgt[::]
    else: vf =[np.nan]

    if np.all(np.isnan(vf)):
        print 'All volume fractions are nan'
        ivf=False

    iEi = False
    if type(full_Ei)!=type(None): iEi = True

    sf   = container.sf #dat_model.sf[istp]
    tdat = container.tdat; ehkl = container.ehkl
    eps0 = container.eps0; Ei   = container.Ei

    if fig==None: fig = wide_fig(
            ifig,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
            left=0.15,right=0.25,nh=1,h0=0.2,h1=0,
            down=0.08,up=0.10,iarange=True)
    if figs==None: figs= wide_fig(
            ifig+1,nw=nphi,w0=0.00,ws=0.5,w1=0.0,
            uw=3.0,left=0.12,right=0.10)
    if fige==None: fige= wide_fig(
            ifig+2,nw=nphi,w0=0.00,ws=0.5,w1=0.0,
            uw=3.0,left=0.12,right=0.10)

    axes  = fig.axes[:nphi]#nphi:nphi*2]
    ax_er = fige.axes[:nphi]; axesf = figs.axes;
    if ivf: axesv = []

    for iphi in range(nphi):
        ax = fig.axes[iphi]; axs = figs.axes[iphi]
        if ivf: axesv.append(axes[iphi].twinx())
        ax.set_title( r'$\phi=%3.1f^\circ$'%(phis[iphi]*180/pi))
        axs.set_title(r'$\phi=%3.1f^\circ$'%(phis[iphi]*180/pi))
        ax.locator_params(nbins=4); axs.locator_params(nbins=4)
        if ivf: axesv[iphi].locator_params(nbins=4)

    for iphi in range(nphi):
        ax = axes[iphi]; ae = ax_er[iphi]
        if ivf: av = axesv[iphi];
        ## convert psi to user's convenience.
        if iphi==0:
            if iEi: xEi = sin2psi_opt(wgt_psi[::],ipsi_opt)
            x  = sin2psi_opt(psis[::],ipsi_opt)
            if ivf: xv = sin2psi_opt(wgt_psi[::],ipsi_opt)
            if iwind:
                x = sin2psi_opt(psis[::],2)
                if ivf: xv = sin2psi_opt(wgt_psi[::],2)


        ## E_{i}
        if ileg: label=r'Fit'
        else:    label=None
        ax.plot(x,Ei[iphi]*1e6,'+',mec='k',ms=7,
                mfc='None',label=label)
        ## e-e_0
        if hkl==None and ileg:
            label=r'$\tilde{ \langle\varepsilon^e \rangle}^G$'
        elif hkl!=None and ileg:
            label=r'$\tilde{ \langle\varepsilon^e \rangle}^G$'
            #label=r'$\varepsilon^{\{%s\}}-\varepsilon^{\{%s\}}_0$'%(hkl,hkl)
        elif ileg!=True: label=None

        y = tdat[iphi]*1e6
        ax.plot(x,y,'k.',label=label)
        if iwind:
            raise IOError, 'iwind is not stable'
            xerr = []
            for i in range(len(psis)):
                X = psis[i]*180./np.pi; Y = y[i]
                pl, lu, s2l, s2u = sin2psi_wind(
                    w_rad=wdeg,psi0=X)
                ax.plot([s2l,s2u],[Y,Y],'g-')
                ax.plot([s2l,s2u],[Y,Y],'g|')

        if hkl==None and ileg: label=r'$E_{i} - \varepsilon^{\{hkl\}}-\varepsilon^{\{hkl\}}_0$'
        elif hkl!=None and ileg: label='$E_{i} - \varepsilon^{\{%s\}}-\varepsilon^{\{%s\}}_0$'%(hkl,hkl)
        elif ileg!=True: label = None

        # if np.all(np.isnan(vf[iphi])):
        #     print 'All volume fractions are nan'
        # else:
        if ivf: av.plot(xv,vf[iphi],'r-')

        ae.plot(x,Ei[iphi]*1e6-y,c2+m2,label=label)
        deco(ax=ax,iopt=0,hkl=hkl,ipsi_opt=ipsi_opt)
        deco(ax=ae,iopt=0,hkl=hkl,ipsi_opt=ipsi_opt)
        if iphi==0 and ileg:
            pass
            # ax.legend(loc='upper right',fontsize=9,fancybox=True).\
            #     get_frame().set_alpha(0.5)
            # av.legend(loc='lower right',fontsize=9,fancybox=True).\
            #     get_frame().set_alpha(0.5)

        ## all_stress_factor_hkl.pdf
        ax=axesf[iphi]
        if hkl==None and ileg:
            lab1=r'$\mathbb{F}_{11}$'; lab2=r'$\mathbb{F}_{22}$'
        elif hkl!=None and ileg:
            lab1=r'$\mathbb{F}^{\{%s\}}_{11}$'%hkl; lab2=r'$\mathbb{F}^{\{%s\}}_{22}$'%hkl
        elif ileg!=True:
            lab1=None; lab2=None

        for i in range(len(isf)):
            if i==0:# and ileg:
                lab=lab1
                #st = c1+m1
                # c=c1
                c='k'
                st='r-'
                marker = '.'
            elif i==1:# and ileg:
                lab=lab2
                #st = c2+m2
                # c=c2
                c = 'gray'
                st='b-'
                marker = '+'

            if isf[i]:
                # l, = ax.plot(
                #     xv,sf[i][iphi]*1e6,st,label=lab)
                for j in range(len(sf[i][iphi][:])):
                    if sf[i][iphi][j]!=0:
                        if j==0:
                            ax.plot(x[j],sf[i][iphi][j]*1e6,ls='None',
                                    color=c,marker=marker,
                                    label=lab)
                        else:
                            ax.plot(x[j],sf[i][iphi][j]*1e6,color=c,marker=marker)

        if ivf:
            av.set_ylabel(r'Vol. $f(\phi,\psi)$',dict(fontsize=13))
            av.tick_params(axis='y',colors='red')
            av.yaxis.label.set_color('red')

        deco(ax=ax,iopt=1,hkl=hkl,ipsi_opt=ipsi_opt)
        # if iphi==0:fancy_legend(ax,nscat=1)

    if stress_wgt!=None:
        container.sigma = np.array(stress_wgt)
        container.calc_Ei(ivo=ivo)

        if ileg:
            label = r'$\mathbb{F}^{\ \ G, I}_{ij} \langle\sigma^c\rangle_{ij}$'
            lab1 = r'$\mathbb{F}_{ij}\ \hat{\sigma}^{RS}_{ij}$'
        else:
            label=None
            lab1 =None

        for iphi in range(nphi):
            ax=axes[iphi]

            ## Calculate the elastic strain
            ## based on the obtained stress and DEC
            ax.plot(x,container.Ei[iphi]*1e6,'o',
                    mfc='None',mec='black',label=label)
            if iEi: ax.plot(xEi, full_Ei[iphi]*1e6,'k-',label=lab1)
            if iphi==nphi-1: fancy_legend(
                    ax,size=11,nscat=1,ncol=1,
                    bbox_to_anchor=(1.4,1))


    tune_x_lim(fig.axes,axis='x')
    tune_x_lim(axes,    axis='y')
    tune_xy_lim(ax_er           )
    if ivf: tune_x_lim(axesv,   axis='y')
    tune_x_lim(axesf,   axis='y')

    ## remove redundant axis labels
    for i in range(len(axes)-1):
        rm_lab(axes[i+1], axis='y')
        rm_lab(axes[i+1], axis='x')
        rm_lab(axesf[i+1],axis='y')
        rm_lab(axesf[i+1],axis='x')
        rm_lab(ax_er[i+1],axis='y')
        rm_lab(ax_er[i+1],axis='x')
        if ivf: rm_lab(axesv[i],  axis='y')

    return fig, figs, fige

def __model_fit_plot_3d__(container,istp,nxphi=None):
    import phikhi.psikhi2cart as pk
    conv = pk.conv
    convs = pk.convs

    nphi=container.nphi
    if nxphi!=None and nphi>nxphi:
        print 'Probed phis are redundant:', nphi
        print 'Only %i of phis axis are shown'%(nxphi)
        nphi = nxphi

    npsi=container.npsi
    phis=container.phis
    psis=container.psis

    vf = container.dat_model.vf[istp]
    ngr = container.dat_model.ngr[istp]

    sf = container.sf
    tdat = container.tdat
    ehkl = container.ehkl
    eps0 = container.eps0
    Ei   = container.Ei

    from mpl_lib import mpl_lib
    ax3d = mpl_lib.axes3()

    for iphi in range(nphi):
        #x = sin(psis)**2
        x = psis
        y = np.ones(len(x))*phis[iphi]
        x, y = convs(k=x,p=y)
        z = Ei[iphi]
        ax3d.plot(x,y,z,'rx')

    for iphi in range(nphi):
        x = psis
        y = np.ones(len(x)) * phis[iphi]
        x, y = convs(k=x,p=y)
        z = tdat[iphi]
        ax3d.plot(x,y,z,'b+')

    #ax3d.set_xlabel(r'$\sin^2{\psi}$')
    ax3d.set_xlabel(r'$\psi$')
    ax3d.set_ylabel(r'$\phi$')
    ax3d.set_xlim(-1,1)
    ax3d.set_ylim(-1,1)



def sf_scan(fn='sf_ph1.out',npair=1):
    import MP.read_blocks as rb
    from MP.mat import voigt
    from MP.lib import mpl_lib

    wide_fig = mpl_lib.wide_fig
    figs=wide_fig(nw=2)
    ijv = voigt.ijv
    read=rb.read_sf_scan
    sig,eps=read(fn=fn)
    print len(sig),len(eps)
    nstp = len(sig)
    if np.mod(nstp,npair)!=0:
        raise IOError, 'Cannot be paired with given npair...'

    for i in range(nstp/npair):
        for j in range(npair):
            s = sig[i*npair+j]
            e = eps[i*npair+j]
            for k in range(2):
                figs.axes[k].plot(s[k], e[10])
                figs.axes[k].plot(s[k], e[1])
                figs.axes[k].plot(s[k], e[100])
                figs.axes[k].plot(s[k], e[200])

def stress_plot(ext=['311','211','220','200'],ifig=1,nphi=3,istp=2,sin2psimx=None):
    """
    Plot results on various hkl
    """
    from MP.lib import mpl_lib
    from MP.lib import axes_label
    wide_fig = mpl_lib.wide_fig
    fig  = wide_fig(ifig,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                    left=0.15,right=0.10,
                    nh=1,h0=0.2,h1=0,down=0.08,up=0.10,
                    iarange=True)
    figs = wide_fig(ifig+1,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                    left=0.12,right=0.10)
    fige = wide_fig(ifig+2,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                    left=0.12,right=0.10)
    hkl=ext


    c1=['r','g','b','k']
    c2=['m','y','b','r']

    m1=['x','+','-','--']
    m2=['+','+','+','+']

    diffs=[]
    f_w=[]
    f_d=[]

    for i in range(len(ext)):
        # weighted flow, flow based on diffraction analysis
        diff, flow_w, flow_d = ex_consistency(iplot=False,mod_ext=ext[i],
                                              sin2psimx=sin2psimx)
        diffs.append(diffs)
        f_w.append(flow_w)
        f_d.append(flow_d)

        print ext[i]
        f1,f2,f3=__model_fit_plot__(
            container=diff,ifig=ifig,istp=istp,nxphi=3,hkl=ext[i],
            stress_wgt=None,ivo=None,fig=fig,figs=figs,fige=fige,
            c1=c1[i],c2=c2[i],
            m1=m1[i],m2=m2[i],
            isf=[True,False]
            )

    return diffs, f_w, f_d
