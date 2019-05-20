
def plot(molcas_Workdir,what='walkers'):

    from molcas_neci_interface.plotting.statsplot import plotter

    import tarfile

    # tar = tarfile.open('/home/katukuri/Codes/Python/molcas_neci_interface/Example/tmp/Iter_0.tar.gz','r')
    tar = tarfile.open(molcas_Workdir+'Iter_0.tar.gz','r')

    f=tar.extractfile(tar.getmember('Iter_0/FCIMCStats'))
    fout=tar.extractfile(tar.getmember('Iter_0/neci.out'))

    plot=plotter()
    plot.init_axes()
    plot.plot_data(f,fout=fout,what=what)

    plot.fig.show()

#plot.fig.canvas.mpl_connect('key_release_event', keypress_callback)

if __name__ == "__main__" :

    molcas_Workdir='/home/katukuri/Codes/Python/molcas_neci_interface/Example/tmp/'
    plot(molcas_Workdir)


