"""
A collection of scripts that make use of residual stress module
"""

import numpy as np
pi = np.pi
sin = np.sin
cos = np.cos

def ex(ifig=50,
       exp_ref=['exp_dat/Bsteel/EXP_BULGE_JINKIM.txt',
                'exp_dat/Bsteel/uni/avgstr_000.txt'],
       exp_lab=['Exp bulge','Exp uniaxiai'],
       mod_ref='STR_STR.OUT'):
    """
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
        ifig=50,
        nxphi=3,
        #exp_ref=['exp_dat/Bsteel/bulge/EXP_BULGE_JINKIM.txt',
        #'exp_dat/Bsteel/uni/avgstr_000.txt'],
        #exp_lab=['Exp bulge','Exp uniaxiai'],
        #exp_ref=['exp_dat/Bsteel/uni/avgstr_000.txt'],
        #exp_lab=['Exp uniaxiai'],
        exp_ref=[], exp_lab=[],
        mod_ext=None,
        mod_ref='STR_STR.OUT',
        sin2psimx=None,
        iscatter=False,
        psimx=None,
        psi_nbin=1,
        ig_sub=True,
        istep=None,
        hkl=None,
        iplot=True):
    """
    Consistency check between 'weighted average' stress and
    the stress obtained following the stress analysis method
    (SF, IG strain)

    ifig = 50
    nxphi   : display only first nxphi of results along phi axis
    exp_ref : experimental reference
    mode_ref: model's weighted average flow curves are given
    """
    from rs import ResidualStress
    from rs import u_epshkl
    from rs import filter_psi
    from rs import psi_reso, psi_reso2
    from MP.mat import mech # mech is a module
    FlowCurve = mech.FlowCurve

    if iplot:
        from matplotlib import pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        from MP.lib import mpl_lib # mpl_lib is a module
        from MP.lib import axes_label

        wide_fig = mpl_lib.wide_fig
        fancy_legend = mpl_lib.fancy_legend

        fe   = PdfPages('all_ehkl_fits_%s.pdf'%hkl)
        fs   = PdfPages('all_stress_factors_%s.pdf'%hkl)
        f_er = PdfPages('all_Ei-ehkl-e0_%s.pdf'%hkl)

        fig1 = wide_fig(ifig,nw=2,nh=1,left=0.2,uw=3.5,
                        w0=0,w1=0.3,right=0,iarange=True)

        ax1 = fig1.axes[0]
        ax2 = fig1.axes[1]

        ax2.set_axis_bgcolor('0.95')
        pass

    model_rs = ResidualStress(
        mod_ext=mod_ext,
        i_ip=1)

    ## masking array element based on diffraction volume
    model_rs.dat_model.mask_vol()

    if mod_ext==None:mod_ref='STR_STR.OUT'
    else: mod_ref='%s.%s'%(mod_ref.split('.')[0],mod_ext)

    flow_weight = FlowCurve(name='Model weighted')
    flow_weight.get_model(fn=mod_ref)
    #flow_weight = model_rs.dat_model.flow
    flow_weight.get_eqv()

    if len(flow_weight.epsilon_vm)<50: lc='bx'
    else: lc='b-'

    if iplot:
        ax1.plot(flow_weight.epsilon_vm,flow_weight.sigma_vm,
                 lc,label='Average',alpha=1.0)
        axes_label.__eqv__(ax1,ft=10)

    ## plot all stress factors at individual deformation levels

    stress = []
    print '%10s%11s%11s%11s%11s%11s'%(
        'S11','S22','S33','S23','S13','S12')
    for istp in range(model_rs.dat_model.nstp):
        """
        sf (nstp, k, nphi,npsi)
        ig (nstp, nphi, npsi)
        ehkl (nstp, nphi,npsi)
        strain (nstp,6)
        vf (nstp,nphi,npsi)
        """
        model_rs.sf   = model_rs.dat_model.sf[istp]
        model_rs.eps0 = model_rs.dat_model.ig[istp]
        model_rs.ehkl = model_rs.dat_model.ehkl[istp]

        ## whether or not intergranular strain is subtracted.
        if ig_sub: model_rs.tdat = model_rs.ehkl - model_rs.eps0
        else: model_rs.tdat = model_rs.ehkl

        tdat_ref = model_rs.tdat[::]
        if iscatter:
            tdat_scatter = []
            for iphi in range(len(tdat_ref)):
                dum = u_epshkl(tdat_ref[iphi],sigma=5e-5)
                tdat_scatter.append(dum)
            tdat_scatter = np.array(tdat_scatter)
            model_rs.tdat = tdat_scatter

        model_rs.phis = model_rs.dat_model.phi
        model_rs.psis = model_rs.dat_model.psi
        model_rs.nphi = len(model_rs.phis)
        model_rs.npsi = len(model_rs.psis)

        if sin2psimx!=None or psimx!=None:
            filter_psi(model_rs,sin2psimx=sin2psimx,psimx=psimx)

        if psi_nbin!=1:
            #psi_reso(model_rs,nbin=psi_nbin)
            psi_reso2(model_rs,ntot=psi_nbin)

        #-----------------------------------#
        ## find the sigma ...

        s11 = model_rs.dat_model.flow.sigma[0,0][istp]
        s22 = model_rs.dat_model.flow.sigma[1,1][istp]
        dsa_sigma = model_rs.find_sigma(
            ivo=[0,1],
            init_guess=[s11,s22,0,0,0,0])

        for i in range(6): print '%+10.1f'%(dsa_sigma[i]),
        print ''
        stress.append(dsa_sigma)
        #-----------------------------------#

        if (istep!=None and istp==istep) or\
                (istep==None and istp==model_rs.dat_model.nstp-1)\
                and iplot:
            fig2,fig3,fig4=__model_fit_plot__(
                model_rs,ifig=ifig+istp*2+10,
                istp=istp, nxphi=nxphi, stress_wgt=None,ivo=None)

        if iplot:
            plt.ioff()
            f1,f2,f3=__model_fit_plot__(
                model_rs,ifig=ifig+istp*2+10,
                istp=istp, nxphi=nxphi, stress_wgt=[s11,s22,0,0,0,0],ivo=[0,1])
            fs.savefig(f2);fe.savefig(f1); f_er.savefig(f3)
            plt.close(f1);plt.close(f2); plt.close(f3)
            plt.ion()
            pass

    if iplot: fe.close(); fs.close(); f_er.close()

    stress=np.array(stress).T # diffraction stress
    flow_dsa = FlowCurve(name='Diffraction Stress')
    flow_dsa.get_6stress(stress)
    flow_dsa.get_33strain(model_rs.dat_model.flow.epsilon)
    flow_dsa.get_eqv()

    if iplot:
        ax1.plot(flow_dsa.epsilon_vm,flow_dsa.sigma_vm,'k+',
                 label='Stress Analysis')
        for i in range(len(exp_ref)):
            f = exp_ref[i]
            lab = exp_lab[i]
            edat=np.loadtxt(f).T
            ax1.plot(edat[0],edat[1],'-',lw=2,label=lab)
            ax1.set_ylim(0.,800)

        fancy_legend(ax1,size=10)

    #sigma_wgt = model_rs.dat_model.flow.sigma
    sigma_wgt = flow_weight.sigma

    if iplot:
        ax2.plot(sigma_wgt[0,0],sigma_wgt[1,1],'b--',label='weight')
        ax2.plot(flow_dsa.sigma[0,0],flow_dsa.sigma[1,1],'k+',label='DSA')

        ax2.set_ylim(-100,700); ax2.set_xlim(-100,700)
        ax2.set_aspect('equal')
        ax2.set_xlabel(r'$\bar{\Sigma}_{11}$',dict(fontsize=15))
        ax2.set_ylabel(r'$\bar{\Sigma}_{22}$',dict(fontsize=15))
        ax2.locator_params(nbins=3)
        ax2.set_xticks(np.linspace(300,700,3),dict(fontsize=4))
        ax2.set_yticks(np.linspace(300,700,3),dict(fontsize=4))
        ax2.grid('on')
        plt.show()

        ## save figures
        fig1.savefig('flow_%s.pdf'%hkl)
        fig2.savefig('ehkl_fit_%s.pdf'%hkl)
        fig3.savefig('sf_%s.pdf'%hkl)
        fig4.savefig('ehkl_fit_err_%s.pdf'%hkl)

        # close figures
        plt.close(fig1)
        plt.close(fig2)
        plt.close(fig3)
        plt.close(fig4)

    return model_rs, flow_weight, flow_dsa

def __model_fit_plot__(container,ifig,istp,nxphi=None,hkl=None,
                       stress_wgt=None,ivo=None,fig=None,figs=None,fige=None,
                       c1='r',c2='b',m1='--',m2='-',isf=[True,True]):

    """
    Plot container's
    """
    from MP.lib import mpl_lib
    from MP.lib import axes_label
    wide_fig     = mpl_lib.wide_fig
    fancy_legend = mpl_lib.fancy_legend
    rm_lab       = mpl_lib.rm_lab
    tune_x_lim   = mpl_lib.tune_x_lim
    deco = axes_label.__deco__

    nphi=container.nphi; npsi=container.npsi;
    phis=container.phis; psis=container.psis
    if nxphi!=None and nphi>nxphi:
        print 'Probed phis are redundant:', nphi
        print 'Only %i of phis axis are shown'%(nxphi)
        nphi = nxphi

    vf = container.dat_model.vf[istp]
    ngr = container.dat_model.ngr[istp]

    sf = container.dat_model.sf[istp]
    tdat = container.tdat
    ehkl = container.ehkl
    eps0 = container.eps0
    Ei   = container.Ei

    if fig==None: fig = wide_fig(ifig,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                                 left=0.15,right=0.10,
                                 nh=1,h0=0.2,h1=0,down=0.08,up=0.10,
                                 iarange=True)
    if figs==None: figs= wide_fig(ifig+1,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                                  left=0.12,right=0.10)
    if fige==None: fige= wide_fig(ifig+2,nw=nphi,w0=0.00,ws=0.5,w1=0.0,uw=3.0,
                                  left=0.12,right=0.10)

    axes= fig.axes[:nphi]#nphi:nphi*2]
    ax_er= fige.axes[:nphi]
    axesf = figs.axes; axesv = []

    for iphi in range(nphi):
        ax=fig.axes[iphi]
        axesv.append(axes[iphi].twinx())
        axs=figs.axes[iphi]

        ax.set_title(r'$\phi=%3.1f^\circ$'%(phis[iphi]*180/pi))
        axs.set_title(r'$\phi=%3.1f^\circ$'%(phis[iphi]*180/pi))
        ax.locator_params(nbins=4)
        axs.locator_params(nbins=4)
        axesv[iphi].locator_params(nbins=4)

    for iphi in range(nphi):
        ax=axes[iphi]; av=axesv[iphi]; ae=ax_er[iphi]

        x=sin(psis)**2
        xv = sin(container.dat_model.psi)**2
        ax.plot(x,Ei[iphi]*1e6,'r--',
                label=r'$E_{i}$ (fitting)')
        y = tdat[iphi]*1e6

        if hkl==None:
            label=r'$\varepsilon^{hkl}-\varepsilon^{hkl}_0$'
        else:
            label=r'$\varepsilon^{%s}-\varepsilon^{%s}_0$'%(hkl,hkl)
        ax.plot(x,y,'bx',label=label)


        if hkl==None: label=r'$E_{i} - \varepsilon^{hkl}-\varepsilon^{hkl}_0$'
        else:
            label=r'$E_{i} - \varepsilon^{%s}-\varepsilon^{%s}_0$'%(hkl,hkl)
        av.plot(xv,vf[iphi],c1+m1,label='VF')
        ae.plot(x,Ei[iphi]*1e6-y,c2+m2,label=label)

        deco(ax=ax,iopt=0); deco(ax=ae,iopt=0)
        if iphi==0:
            ax.legend(loc='upper right',fontsize=9,fancybox=True).\
                get_frame().set_alpha(0.5)
            av.legend(loc='lower right',fontsize=9,fancybox=True).\
                get_frame().set_alpha(0.5)
        ax=axesf[iphi]

        if hkl==None:
            lab1=r'$F_{11}$'
            lab2=r'$F_{22}$'
        else:
            lab1=r'$F^{%s}_{11}$'%hkl
            lab2=r'$F^{%s}_{22}$'%hkl

        for i in range(len(isf)):
            if isf[i]:
                l, = ax.plot(xv,sf[i][iphi]*1e6,c1+m1,
                             label=lab1)
        av.set_ylabel(r'$f(\phi,\psi)$',dict(fontsize=15))
        deco(ax=ax,iopt=1)
        if iphi==0:fancy_legend(ax)

    if stress_wgt!=None:
        container.sigma = np.array(stress_wgt)
        container.calc_Ei(ivo=ivo)

        # label = 'E_{i} \mathrm{(fitting) with}'
        # for i in range(len(ivo)):
        #     label = '%s \sigma_{%1i}: %3.1f'%(label,i+1,stress_wgt[i])
        # label=r'$%s$'%label
        label = r'$E_{i}$ with given stress'

        for iphi in range(nphi):
            ax=axes[iphi]
            x=sin(psis)**2
            ax.plot(x,container.Ei[iphi]*1e6,'k--',label=label)
            if iphi==0: fancy_legend(ax,size=10)

    tune_x_lim(fig.axes,axis='x')
    tune_x_lim(axes,    axis='y')
    tune_x_lim(axesv,   axis='y')
    tune_x_lim(axesf,   axis='y')

    ## remove redundant axis labels
    for i in range(len(axes)-1):
        rm_lab(axes[i+1], axis='y')
        rm_lab(axes[i+1], axis='x')
        rm_lab(axesf[i+1],axis='y')
        rm_lab(axesf[i+1],axis='x')
        rm_lab(axesv[i],  axis='y')

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
