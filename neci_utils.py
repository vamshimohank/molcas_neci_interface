
def calc_Ndet(norb,nele):
    from scipy.special import comb
    Ndet =comb(norb,nele/2)*comb(norb,nele/2)

    return Ndet

def calc_Ncsf(S,norb,nele):

    """
    Given the number of orbitals and electrons in them,
    this function returns the # of CSFs with spin S

    :param S: Total spin
    :param norb: # of orbitals
    :param nele: # of electrons
    :return: # of CSF
    """

    from scipy.special import comb

    fac = (2*S+1)/(norb + 1)
    t1 = comb(norb + 1,(nele/2)-S)
    t2 = comb(norb + 1, (nele/2)+S+1)
    Ncsf = fac * t1 * t2
    # Ncsf = (2*S+1)/(norb + 1) * comb(norb + 1,(nele/2)-S) * comb(norb + 1, (nele/2) + S +1)

    return Ncsf

if __name__ == '__main__':

    S=1
    nele = 4
    norb = 4
    print(calc_Ncsf(S,norb,nele))
    print(calc_Ndet(4,4))
