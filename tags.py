gold_pos = {
    'S': 'Nn',
    'V': 'Vb',
    # 'INFN': 'If',  # V + inf
    # 'PRTF': 'Pt',  # V + partcp + plen
    # 'PRTS': 'Vp',  # V + partcp + brev
    # 'GRND': 'Dp',  # V + ger
    'A': 'Aj',
    'A-PRO': 'Aj',
    'A-NUM': 'Aj',
    # 'ADJS': 'Ap',  # A + brev
    'ADV': 'Ad',
    'ADV-PRO': 'Ad',
    'S-PRO': 'Pn',
    'PRAEDIC-PRO': 'Pd',
    'NUM': 'Nu',
    'CONJ': 'Cj',
    'PR': 'Pp',
    'PART': 'Pc',
    'PRAEDIC': 'Pd',
    'PARENTH': 'Ad',
    'A/ADV': 'Cm',
    'INTJ': 'Ij',

    'INIT': 'Zr',
    'NONLEX': 'Zr',
}

gold_animacy = {
    'anim': 'An',
    'inan': 'In',
    '|animation': 'Zz',
}

gold_case = {
    'nom': 'Nm',
    'gen': 'Gn',
    'dat': 'Dt',
    'acc': 'Ac',
    'ins': 'Ab',
    'loc': 'Lc',
    'voc': 'Nm',
    'gen2': 'Gn',
    'loc2': 'Lc',
    'acc2': 'Ac',
    '|case': 'Zz',
}

gold_number = {
    'sg': 'Sg',
    'pl': 'Pl',
    '|number': 'Zz',
}

gold_gender = {
    'm': 'Ms',
    'f': 'Fm',
    'n': 'Nr',
    '|gender': 'Zz',
}

gold_person = {
    '1p': 'Fs',
    '2p': 'Sc',
    '3p': 'Th',
    '|person': 'Zz',
}

gold_aspect = {
    'pf': 'Pf',
    'ipf': 'Im',
    '|aspect': 'Zz',
}

pymorphy_all = {
    'NOUN': 'Nn',
    'VERB': 'Vb',
    'INFN': 'If',
    'PRTF': 'Pt',
    'PRTS': 'Vp',
    'GRND': 'Dp',
    'ADJF': 'Aj',
    'ADJS': 'Ap',
    'ADVB': 'Ad',
    'NPRO': 'Pn',
    'NUMR': 'Nu',
    'CONJ': 'Cj',
    'PREP': 'Pp',
    'PRCL': 'Pc',
    'PRED': 'Pd',
    'COMP': 'Cm',
    'INTJ': 'Ij',

    'anim': 'An',
    'inan': 'In',

    'nomn': 'Nm',
    'gent': 'Gn',
    'datv': 'Dt',
    'accs': 'Ac',
    'ablt': 'Ab',
    'loct': 'Lc',
    'voct': 'Nm',
    'gen2': 'Gn',
    'loc2': 'Lc',
    'acc2': 'Ac',

    'sing': 'Sg',
    'plur': 'Pl',

    'masc': 'Ms',
    'femn': 'Fm',
    'neut': 'Nr',

    '1per': 'Fs',
    '2per': 'Sc',
    '3per': 'Th',

    'perf': 'Pf',
    'impf': 'Im',

    'PNCT': 'PM',
    'NUMB': 'NM',
    'LATN': 'Zr',
    'ROMN': 'Zr',
    'UNKN': 'Zr',
}
