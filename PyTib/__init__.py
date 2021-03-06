import os
import json
from .SylComponents import SylComponents
this_dir, this_filename = os.path.split(__file__)

# lexicon used by Segment
with open(os.path.join(this_dir, "data", "uncompound_lexicon.txt"), 'r', -1, 'utf-8-sig') as f:
    lexicon = [line.strip() for line in f.readlines()]
# extensions to the lexicon : exceptions (sskrt + others), particles
with open(os.path.join(this_dir, "data", "particles.json"), 'r', -1, 'utf-8-sig') as f:
    lexicon.extend(json.loads(f.read())['particles'])
with open(os.path.join(this_dir, "data", "monlam1_verbs.txt"), 'r', -1, 'utf-8-sig') as f:
    lexicon.extend([line.strip().split(' | ')[0] for line in f.readlines()])
with open(os.path.join(this_dir, "data", "exceptions.txt"), 'r', -1, 'utf-8-sig') as f:
    exceptions = [line.strip() for line in f.readlines() if not line.startswith('#')]
lexicon.extend(exceptions)
# calculate the sizes of words in the lexicon, for segment()
len_word_syls = []
for word in lexicon:
    l = len(word.split('་'))
    if l not in len_word_syls:
        len_word_syls.append(l)
len_word_syls = sorted(len_word_syls, reverse=True)

# compound words to join by default
with open(os.path.join(this_dir, "data", "compound_lexicon.csv"), 'r', -1, 'utf-8-sig') as f:
    raw = [line.strip() for line in f.readlines()]
    # parse the data in the compound lexicon
    compound = ([], [])
    for line in raw[1:]:
        if line.strip().strip(',') != '' and not line.startswith('#'):
            # Todo : change to \t when putting in production
            parts = line.split(',')
            # list of words as created by the base segmentation
            compound[0].append(parts[2].replace('-', '').replace('+', '').split(' '))
            # list of words with the markers to split('+') and merge ('-')
            compound[1].append((parts[1].split(' '), parts[2].split(' '), parts[3].split(' ')))


# ancient spelling
with open(os.path.join(this_dir, "data", "ancient.txt"), 'r', -1, 'utf-8-sig') as f:
    ancient = [line.strip() for line in f.readlines()]

# data for SylComponents
with open(os.path.join(this_dir, "data", "SylComponents.json"), 'r', -1, 'utf-8-sig') as f:
    data = json.loads(f.read())
dadrag = data['dadrag']
roots = data['roots']
suffixes = data['suffixes']
Csuffixes = data['Csuffixes']
special = data['special']
wazurs = data['wazurs']
ambiguous = data['ambiguous']
m_roots = data['m_roots']
m_exceptions = data['m_exceptions']
m_wazurs = data['m_wazurs']
# hack to turn lists to tuples as required for SylComponents
for am in ambiguous:
    ambiguous[am] = (ambiguous[am][0], ambiguous[am][1])

# data for Agreement
with open(os.path.join(this_dir, "data", "Agreement.json"), 'r', -1, 'utf-8-sig') as f:
    a_data = json.loads(f.read())
particles = a_data['particles']
corrections = a_data['corrections']

# data for AntTib
with open(os.path.join(this_dir, "data", "AntTib.json"), 'r', -1, 'utf-8-sig') as f:
    t_data = json.loads(f.read())
t_roots = t_data['roots']
t_rareC = t_data['rareC']
t_wazurC = t_data['wazurC']
t_NB = t_data['NB']
t_special = t_data['special']
t_wazur = t_data['wazur']


def getSylComponents():
    if not getSylComponents.instance:
        getSylComponents.instance = SylComponents(dadrag, roots, suffixes, Csuffixes, special, wazurs, ambiguous, m_roots, m_exceptions, m_wazurs)
    return getSylComponents.instance
getSylComponents.instance = None


def Segment():
    from .Segmentation import Segment, strip_list, search
    SC = getSylComponents()
    return Segment(lexicon, compound, ancient, exceptions, len_word_syls, SC)


def Agreement():
    from .Agreement import Agreement
    SC = getSylComponents()
    return Agreement(particles, corrections, SC)


def AntTib():
    from .AntTib import AntTib, strip_list
    SC = getSylComponents()
    return AntTib(t_roots, t_rareC, t_wazurC, t_NB, t_special, t_wazur, SC)


def getAntTib():
    if not getAntTib.instance:
        getAntTib.instance = AntTib()
    return getAntTib.instance
getAntTib.instance = None


def AntPut():
    from .AntPut import AntPut
    AT = getAntTib()
    return AntPut(AT)

__all__ = ['Segment', 'getSylComponents', 'Agreement', 'AntTib', 'AntPut']
