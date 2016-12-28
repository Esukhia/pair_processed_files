from PyTib.common import open_file, get_longest_common_subseq
import os
import re
import difflib
import itertools
import shutil
import logging
from collections import defaultdict
from fuzzywuzzy import fuzz


def clean_string(string,
                 tabs2spaces=False, under2spaces=False,
                 single_spaces=False, single_returns=False, single_unders=False,
                 del_spaces=False, del_returns=False, del_dashes=False,
                 l_strip=False, r_strip=False, strip=False,):
    # Replacements
    if tabs2spaces: string = string.replace('\t', ' ')
    if under2spaces: string = string.replace('_', ' ')

    # Reducing to one element
    if single_spaces: string = re.sub(r' +', r' ', string)
    if single_returns: string = re.sub(r'\n+', r'\n', string)
    if single_unders: string = re.sub(r'_+', r'_', string)

    # Delete the given elements
    if del_spaces: string = string.replace(' ', '')
    if del_returns: string = string.replace('\n', '')
    if del_dashes: string = string.replace('-', '')

    # strips
    if l_strip: string = string.lstrip()
    if r_strip: string = string.rstrip()
    if strip: string = string.strip()

    return string


def find_string(in_path, string):
    """wrapper function """
    found = []
    for f in os.listdir(in_path):
        raw = open_file('{}/{}'.format(in_path, f))
        raw = clean_string(raw, strip=True, del_returns=True)

        # unsegment the files
        raw = clean_string(raw, del_dashes=True, del_spaces=True)

        if string in raw:
            found.append(f)

    if found == []:
        return 'Nothing found.\n'
    else:
        return 'The following files were found:\n{}\n'.format('\n'.join(found))


def search_in_folders(in_folders, string):
    # delete spaces in string
    string = clean_string(string, del_spaces=True)

    for path in in_folders:
        size = len(os.listdir(path))
        print('\tSearching for “{}”\n\tin {} files in {}'.format(string, size, path))
        print(find_string(path, string))


def patterned(names, pattern):
    return [pattern.format(n) for n in names]


to_search = 'སྤྱིར་བཏང་ང་ཚོ་ཡིན་ན་ཡང་གོམས་མ་གོམས་ཀྱི་དབང་གིས'
in_path = patterned(['recordings', 'dialogs', 'children_stories', 'oral_corpus'],
                    '../tibetan-wordbreak-js/make/updateLexicon/{}/files')

#search_in_folders(in_path, clean_string(to_search, del_spaces=True))


##############################################################################################

def is_segmented_version(string_a, string_b, ratio=55):
    """
    Tells if the two files have at least 80% of similarity
    after removing the spaces and dashes added at segmentation time.
    :param string_a: raw content of file a
    :param string_b: raw content of file b
    :param ratio: ratio default set at 80% of similarity
    """
    # clean files
    string_a = clean_string(string_a, strip=True, del_spaces=True, del_dashes=True, del_returns=True)
    string_b = clean_string(string_b, strip=True, del_spaces=True, del_dashes=True, del_returns=True)
    # find ratio
    #d = difflib.SequenceMatcher(a=string_a, b=string_b)

    # return value

    # 1rst 2 syls
    firsta = '་'.join(string_a.split('་')[:8])
    firstb = '་'.join(string_b.split('་')[:8])

    found_ratio = fuzz.ratio(string_a, string_b)
    if found_ratio >= ratio:
        print(found_ratio)
        print(firsta)
        print(firstb)
        return True
    else:
        return False


def first_parts(string, num=10, sep='།'):
    out = ''
    c = 0
    i = 0
    while i <= len(string)-1 and c < num:
        char = string[i]
        out += char
        i += 1
        if char == sep:
            c += 1
    return out


def raw_folder_content(path):
    files_content = {}
    for f in os.listdir(path):
        full_path = '{}/{}'.format(path, f)
        # open file
        raw = open_file(full_path)
        raw = first_parts(raw)
        files_content[full_path] = raw
    return files_content


def pair_files(content1, content2):
    paired = []
    total = defaultdict(int)
    for k1, v1 in content1.items():
        for k2, v2 in content2.items():
            if is_segmented_version(v1, v2):
                name1 = k1.split('/')[-1]
                name2 = k2.split('/')[-1]
                print(name1, name2, '\n')
                total[name1] += 1
                total[name2] += 1
                paired.append((name1, name2))

    # checking the quality of pairing
    c = defaultdict(int)
    for k, v in total.items():
        if v > 1:
            c[v] += 1
            print('{} was found {} times.'.format(k, v))
    for a, b in c.items():
        print('{} files were found {} times'.format(b, a))
    return paired


def find_file_pairs(path1, path2):
    path1_content = raw_folder_content(path1)
    path2_content = raw_folder_content(path2)
    pairs = pair_files(path1_content, path2_content)

    print(pairs)
    print(len(pairs))

#find_file_pairs('/home/swan/Documents/PycharmProjects/tibetan-wordbreak-js/make/updateLexicon/recordings/files', '/home/swan/Documents/modern_tib_corpus/flattened_txt')
#######################################################################################


def create_missing_dir(path):
    """creates the folder designated in path if it does not exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def list_absolute_paths(dir):
    all_files = []
    for root, _dirs, files in itertools.islice(os.walk(dir), 1, None):
        for filename in files:
            if filename != '._.DS_Store':
                all_files.append(os.path.join(root, filename))
    return all_files


def new_prefix(origin, parts=None, sep='_'):
    o_parts = origin.split('/')[:-1]
    if not parts:
        return sep.join(o_parts)
    else:
        return sep.join([o_parts[p] for p in parts if p <= len(o_parts)-1])


def move(origin, destination):
    # list all files
    all_abs_paths = list_absolute_paths(origin)

    for filename in all_abs_paths:
        logging.info(filename)
        name = filename.split('/')[-1]
        prefix = new_prefix(filename, parts=[8])
        #prefix = prefix.replace(''.join(get_longest_common_subseq([name, prefix])), '')
        new_name = '{}__{}'.format(prefix, name)

        # create directory if not yet existing
        create_missing_dir(destination)

        # copy the file and rename it right after
        shutil.copy(filename, destination)
        os.rename('{}/{}'.format(destination, name), '{}/{}'.format(destination, new_name))

#move('/home/swan/Documents/modern_tib_corpus/5 studio recording for Nanhai nunnery/Not Segmented', '/home/swan/Documents/modern_tib_corpus/flattened')
#move('/home/swan/Documents/modern_tib_corpus/4 monastery and nunnery with list/unsegmented/by topics', '/home/swan/Documents/modern_tib_corpus/flattened')
#################################################################################################################


def extract_subset(destination, all_abs_paths):
    # list all files

    for filename in all_abs_paths:
        # create directory if not yet existing
        create_missing_dir(destination)

        # copy the file and rename it right after
        shutil.copy(filename[0], destination)
        os.rename(filename[1], filename[2])
        os.remove(filename[3])

original_path = '/home/swan/Documents/PycharmProjects/tibetan-wordbreak-js/make/updateLexicon/recordings/files/'
delete_path = '/home/swan/Documents/modern_tib_corpus/flattened_txt/'
export_path = '/home/swan/Documents/modern_tib_corpus/segmented_4'

pairs5 = [('20 Chokdup.txt', 'Kunkyab__3ཉལ་ཁང་གཙང་སྦྲ་དང་ལས་གཞི་གོ་སྒྲིག་བྱེད་པ།.txt'),
('1 Chokdup.txt', 'Kunkyab_23བླ་མས་སློབ་མར__བླ་མས་སློབ་མ་རྣམས་ལ་སྡོམ་པ་ལེན་འཇུག་པ༡.txt'),
('khar19.txt', 'Khando Dolma33མགྱོགས་པོ་བྱས་ནས་མང་པོ་འདོན་པ།__REC018_1.txt'),
('Dorji Tsering1.txt', 'Jampa__2ཚེ་རིང་གིས་བཀྲ་ཤིས་གཉིད་དཀྲོགས་པ།.txt'),
('khar21.txt', 'Khando Dolma_4ཕ་མའི་བཀའ་དྲིན་སྐོར།__REC0013_1.txt'),
('4 Chokdup.txt', 'Kunkyab_47།__བརྙན་ལེན་སྟངས་དང་བརྙན་སྒྲིག་སྟངས༢.txt'),
('khar16.txt', 'Khando Dolma_12 ཤེས་ཡོན།__12ཤེས་ཡོད་སྦྱོང་པའི་དགེ་མཚན་དང་་་་.txt'),
('khando38.txt', 'Kunkyab_45པ།__གནམ་གཤིས་འགྱུར་བ་འགྲོ་བ༡.txt'),
('Jampa 26.txt', 'Dawa_8དགེ་རྒན་དང་བླ་མའི་ཡོན་ཏན།__REC005_1.txt'),
('khar2.txt', 'Khando Dolma_24།__24 བླ་མས་སློབ་མ་རྣམས་ལ་ངེས་འབྱུང་སྐྱེ་འཇུག་པ (2).txt'),
('Dorji Tsering7.txt', 'Jampa__74བཀྲིས་མཚོ་མོར་སེམས་གསོ་བྱེད་པ།.txt'),
('Jampa 2.txt', 'Dawa_48__འཛིན་གྲའི་སློབ་མའི་གནས་སྟངས་སྐོར།2.txt'),
('Shawo1.txt', 'Chokdup_36__ཕན་ཚུན་སྐུལ་མ་བྱས་ནས་འདུལ་ཁྲིམས་སྲུང་པ།1.txt'),
('19 Chokdup.txt', 'Kunkyab_17།__བོད་སྐད་སློབ་པ་དང་སྦྱོང་བའི་སྐོར༤.txt'),
('khando10.txt', 'Sangye Khar_32།__བསྐང་གསོལ་སྐོར༡.txt'),
('Dorji Tsering11.txt', 'Jampa_4གནའ་བོའི་དམ་པ་གོང་མ་རྣམས།__REC011_1.txt'),
('khando20.txt', 'Sangye Khar_68།__སྐྱབས་འགྲོ་དང་ལམ་རིམ་བློ་སྦྱོང་སྐོར༣.txt'),
('khando2.txt', 'Sangye Khar_འདྲ་པོ་ཡོཔ།__16skypeབརྒྱུད་སློབ་ཚན་འཁྲིད་སྟངས་་་་.txt'),
('17 Chokdup.txt', 'Kunkyab_17།__བོད་སྐད་སློབ་པ་དང་སྦྱོང་བའི་སྐོར༢.txt'),
('Jampa 9.txt', 'Dawa_13__བླ་མ་བསྟེན་ཚུལ་དང་། འཆི་བ། ལས་དབང་།3.txt'),
('shawo23.txt', 'shawo dolma_4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_4.txt'),
('2 Chokdup.txt', 'Kunkyab_23བླ་མས་སློབ་མར__བླ་མས་སློབ་མ་རསནམས་ལ་སྡོམ་པ་ལེན་འཇུག་པ༢.txt'),
('khar12.txt', 'Khando Dolma_20 བ།__20འཛིན་གྲྭ་མི་གཡོལ་པ.txt'),
('Jampa 10.txt', 'Dawa_13__བླ་མ་བསྟེན་ཚུལ་དང་། འཆི་བ། ལས་དབང་།4.txt'),
('Jampa 7.txt', 'Dawa_13__བླ་མ་བསྟེན་ཚུལ་དང་། འཆི་བ། ལས་དབང་།1.txt'),
('Jampa 29.txt', 'Dawa_81__དགོན་པར་མཇལ་བསྐོར།2.txt'),
('Sherab 3.txt', 'Thenley_Sherab__སྒྲ་འཇུག་ ༢.txt'),
('khando18.txt', 'Sangye Khar_68།__སྐྱབས་འགྲོ་དང་ལམ་རིམ་བློ་སྦྱོང་སྐོར༡.txt'),
('shawo15.txt', 'shawo dolma62དགེ་འདུན་པའི་གྲངས་ཀ__REC015_3.txt'),
('palgun dawa 45.txt', 'Kunkyab_36ཕན་ཚུལ།__ཕན་ཚུན་སྐུལ་མ་བྱས་ནས་འདུལ་ཁྲིམས༢.txt'),
('shawo22.txt', 'shawo dolma_4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_3.txt'),
('Dorji Tsering14.txt', 'Jampa54ཚོགས་ཁང་གཙང་མ་བཟོ་བ།__REC022_2.txt'),
('khando3.txt', 'Sangye Kha__70བཙུན་དགོན་ལ་ཞལ་ལག་དང་ཅ་དངོས་འབུལ་བ།.txt'),
('shawo11.txt', 'shawo dolma8འཛིན་གྲོགས་ག་འདྲ་བསྟེན་དགོས་མིན།__REC001_2.txt'),
('shawo18.txt', 'shawo dolma27 སློབ་སྦྱོང་གི་བརྒྱྱད་རིམ།__00000_1.txt'),
('khar25.txt', 'Khando Dolma51ཆོས་ཀྱི་བྱེད་སྒོ་ཞིག་གི་སྔོན་དུ__REC002_1.txt'),
('khar18.txt', 'Khando Dolma1འཛིན་གྲྭའི་འདུ་འཛོམས།__REC004_2.txt'),
('7 Chokdup.txt', 'Kunkyab_66།__བོད་སྐད་ཡིག་གི་གནས་ཚད་མཐོ་རུ་གཏོང་སྟངས༢.txt'),
('Jampa 21.txt', 'Dawa_55__གསང་སྤྱོད་ཀྱི་སྐོར།2.txt'),
('khando4.txt', 'Sangye Kha__སྐྱོན་བརྗོད་དང་གསལ་བཤད།.txt'),
('khar1.txt', 'Khando Dolma_སློབ་མ་རྣམས་ལ་ངེས་འབྱུང་སྐྱེས་པའི་རོགས་པ་བྱེད་པ__22.txt'),
('21 Chokdup.txt', 'Kunkyab__7གདོང་པ་ཁྲུས.txt'),
('12 Chokdup.txt', 'Kunkyab_༡༣སྡུར་བྱེད་པ།__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བརྡུར་བྱེད་པ༣.txt'),
('khando14.txt', 'Sangye Khar_77སློ།  གློ་རྒྱག་པ།__སློབ་མ་མགོ་ན་བ་དང་་། གློ་རྒྱག་པ༡.txt'),
('shawo19.txt', 'shawo dolma7 སློབ་སྦྱོང་གི་བརྒྱྱད་རིམ།__00000_2.txt'),
('shawo28.txt', 'shawo dolma_དྲ་ལམ་བརྒྱུད་ནས་བསྡུས་གྲྭ་ཁྲིད་པ།__15_3.txt'),
('Jampa 24.txt', 'Dawa_69__བླ་མས་ཆོས་ཀྱི་མཇུག་སྡོམ་གནད་བསྡུས་གསུངས་པ།1.txt'),
('Jampa 15.txt', 'Dawa_35__མི་གཅིག་གིས་དགེ་བའི་ལས་གང་བསྒྲུབས་པ་དེའི་སྐོར།2.txt'),
('khando11.txt', 'Sangye Khar_32།__བསྐང་གསོལ་སྐོར༢.txt'),
('23 Chokdup.txt', 'Kunkyab__58པར་སྐྲུན་འཕྲུལ་ཆས་ཀྱི་སྐོར། 5.txt'),
('22 Chokdup.txt', 'Kunkyab__53ཚེ་རིང་ཉལ་ཁང་དུ་ལོག ༡.txt'),
('khando40.txt', 'Kunkyab_57ཁ་ལག་དང་། ་ཁག__ཁ་ལག་དང་ཉིན་རེའི་དགོས་མཁོ༡.txt'),
('khando19.txt', 'Sangye Khar_68སྐྱབས་འགྲ།__སྐྱབས་འགྱོ་དང་ལམ་རིམ་བློ་སྦྱོང་སྐོར༢.txt'),
('Jampa 20.txt', 'Dawa_55__གསང་སྤྱོད་ཀྱི་སྐོར།1.txt'),
('khar24.txt', 'Khando Dolma_46འཛིན་གྲྭའི་རེའི་མིག__REC009.txt'),
('Jampa 6.txt', 'Dawa_67__ལྷ་ཁང་དང་ཡུལ་ལྗོངས་གཙང་མ་བཟོ་བ།2.txt'),
('14 Chokdup.txt', 'Kunkyab_༡༣།__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བསྡུར་བྱེད་པ༥.txt'),
('11 Chokdup.txt', 'Kunkyab_༡༣།__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བསྡུར་བྱེད་པ༢.txt'),
('Dorji Tsering10.txt', 'Jampa___19 དད་པའི་དགེ་མཚན་དང་བླ་མའི་ཡོན་ཏན.txt'),
('Jampa 16.txt', 'Dawa_43__གུས་ཞབས་བྱས་འི་ཕན་ཡོན1.txt'),
('Dorji Tsering3.txt', 'Jampa__6 ཕྱི་ལོགས་ལ་འགྲོ་དུས་་་་་་.txt'),
('Dorji Tsering15.txt', 'Jampa_3གཞན་ལ་ཞེ་སྡང་དང་ང་རྒྱལ་འགོག་པ།__REC029_1.txt'),
('shawo29.txt', 'shawo dolma_དྲ་ལམ་བརྒྱུད་ནས་བསྡུས་གྲྭ་ཁྲིད་པ།__15_5.txt'),
('Jampa 4.txt', 'Dawa_49__བཙུན་དགོན་དུ་རིན་པོ་ཆེ་ཆོས་གསུང་ཀ་ཕེབས་པ།2.txt'),
('Sherab 2.txt', 'Thenley_Sherab__སྒྲ་འཇུག ༡.txt'),
('Sherab 1.txt', 'Thenley_Sherab__སྒྲ་འཇུག་ ༣.txt'),
('shawo14.txt', 'shawo dolma62དགེ་འདུན་པའི་གྲངས་ཀ__REC015_2.txt'),
('shawo30.txt', 'shawo dolma26བསྡུས་གྲྭ་བསྐྱར་སྦྱོང་།__REC001_1.txt'),
('10 Chokdup.txt', 'Kunkyab_༡༣__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བསྡུར་བྱེད་པ།༡.txt'),
('Dorji Tsering17.txt', 'Jampa9གཞན་ལ་ཞེ་སྡང་དང་ང་རྒྱལ་འགོག་པ།__REC029_3.txt'),
('shawo27.txt', 'shawo dolma_དྲ་ལམ་བརྒྱུད་ནས་བསྡུས་གྲྭ་ཁྲིད་པ།__15_2.txt'),
('Jampa 17.txt', 'Dawa_43__གུས་ཞབས་བྱས་འི་ཕན་ཡོན།2.txt'),
('shawo33.txt', 'shawodolma__71 ཉིན་གཅིག་གི་བྱེད་སྒོ།.txt'),
('khar5.txt', 'Khando Dolma___50རིན་པོ་ཆེ་བཙུན་དགོན་ལ་ཕེབས་བསུ།.txt'),
('5 Chokdup.txt', 'Kunkyab_64__ཆོ་ག་འདོན་སྟངས་སྐོར།.txt'),
('khando7.txt', 'Sangye Khar_25ས་འཚལ་སྟངས།__གྲྭ་ཆས་གོན་སྟངས་དང་ཕྱག་འཚལ་སྟངས༡.txt'),
('shawo17.txt', 'shawo dolma_8སྟོན་པའི་སྐུ་འདྲ་ལ་ཕྱགས་འཚལ་པ།__REC017_2.txt'),
('khando39.txt', 'Kunkyab_45པ།__གནམ་གཤིས་འགྱུར་བ་འགྲོ་བ༢.txt'),
('9 Chokdup.txt', 'Kunkyab_82་__སློབ་མས་སློབ་སྦྱོང་གི་བརྒྱུད་རིམ༢.txt'),
('shawo31.txt', 'shawo dolma6བསྡུས་གྲྭ་བསྐྱར་སྦྱོང་།__REC001_2.txt'),
('khando13.txt', 'Sangye Khar_59།__གཏོར་མ་བཟོ་སྟངས༢.txt'),
('Dorji Tsering6.txt', 'Jampa__73དགེ་རྒན་གྱི་ནོར་འཁྲུལ་བཏོན་པ།.txt'),
('shawo8.txt', 'Chokdup_30__བོད་ཡིག་ཀློག་རྩལ་དང་འབྲི་རྩལ།2.txt'),
('khando6.txt', 'Sangye Khar_40།__ཕ་མའི་བཀའ་དྲིན་སྐོར༢.txt'),
('khar10.txt', 'Khando Dolma61སློབ་སྦྱོང་དང་མཉམ་ལེན་བྱེད་སྟངས།__REC032_2.txt'),
('shawo2.txt', 'Chokdup_36__ཕན་ཚུན་སྐུལ་མ་བྱས་ནས་འདུལ་ཁྲིམས་སྲུང་པ།2.txt'),
('Dorji Tsering8.txt', 'Jampa__75སློབ་མ་ཞིག་གིས་མོ་རང་བཙུན་མ་ཆགས་ཐད་ཀྱི་དོགས་གཞི.txt'),
('Jampa 19.txt', 'Dawa_44__གཞན་ལ་བསམ་བློ་གཏོང་རྒྱུ།2.txt'),
('Dorji Tsering13.txt', 'Jampa54ཚོགས་ཁང་གཙང་མ་བཟོ་བ།__REC022_1.txt'),
('3Chokdup.txt', 'Kunkyab_47།__བརྙན་ལེན་སྟངས་དང་བརྙན་སྒྲིག་སྟངས༡.txt'),
('Dorji Tsering5.txt', 'Dawa__11སྔགས་དང་ཁ་འདོན.txt'),
('Jampa 22.txt', 'Dawa_63__བཙུན་མ་རྣམས་ཀྱིས་རིན་པོ་ཆེར་ཞལ་ལག་འབུལ་བ།1.txt'),
('Jampa 23.txt', 'Dawa_63__བཙུན་མ་རྣམས་ཀྱིས་རིན་པོ་ཆེར་ཞལ་ལག་འབུལ་བ།2.txt'),
('shawo16.txt', 'shawo dolma8སྟོན་པའི་སྐུ་འདྲ་ལ་ཕྱགས་འཚལ་པ།__REC017_1.txt'),
('khar20.txt', 'Khando Dolma33མགྱོགས་པོ་བྱས་ནས་མང་པོ་འདོན་པ།__REC018_2.txt'),
('khar8.txt', 'Khando Dolma65གཞུང་བཀའ་པོད་ལྔའི་སྐོར།__REC017_2.txt'),
('khar11.txt', 'Khando Dolma61སློབ་སྦྱོང་དང་མཉམ་ལེན་བྱེད་སྟངས།__REC032_3.txt'),
('palgun dawa 44.txt', 'Kunkyab_36ཕན་ཚུལ།__ཕན་ཚུན་སྐུལ་མ་བྱས་ནས་འདུལ་ཁྲིམས༡.txt'),
('Jampa 13.txt', 'Dawa_29 __བསྡུས་གྲྭ་དང་བོད་ཡིན་སློབ་པ།2.txt'),
('khando17.txt', 'Sangye Khar_38།__སངས་རྒྱས་དང་བྱང་ཆུབ་སེམས་དཔའ༢.txt'),
('shawo9.txt', 'Chokdup_30__བོད་ཡིག་ཀློག་རྩལ་དང་འབྲི་རྩལ།3.txt'),
('shawo20.txt', 'shawo dolma4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_1.txt'),
('Dorji Tsering9.txt', 'Jampa__76སློབ་མས་སློབ་ཚན་ཏག་ཏག་མགོ་མ་ཚོས་པ།.txt'),
('8 Chokdup.txt', 'Kunkyab_82་__སློབ་མས་སློབ་སྦྱོང་གི་བརྒྱུད་རིམ༡.txt'),
('khando15.txt', 'Sangye Khar_77སློ གློ་རྒྱག་པ།__སློབ་མ་མགོ་ན་བ་དང་། གློ་རྒྱག་པ༢.txt'),
('khar3.txt', 'Khando Dolma_24།__24 བླ་མས་སློབ་མ་རྣམས་ལ་ངེས་འབྱུང་སྐྱེ་འཇུག་པ.txt'),
('13 Chokdup.txt', 'Kunkyab_༡༣།__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བསྡུར་བྱེད་པ༤.txt'),
('khando21.txt', 'Sangye Khar_68།__སྐྱབས་འགྲོ་དང་ལམ་རིམ་བློ་སྦྱོང་སྐོར༤.txt'),
('shawo4.txt', 'Chokdup_53__བཀྲིས་ཉལ་ཁང་དུ་ལོག་ནས་ངལ་གསོ་འདོད་པ།2.txt'),
('Jampa 11.txt', 'Dawa__9བཀྲིས་ཀྱིས་བདེ་སྐྱིད་ལ་སྔོ་ཚལ་གཏུབ་སྟངས།.txt'),
('15 Chokdup.txt', 'Kunkyab_༡༣།__ལམ་རིམ་བློ་སྦྱོང་སྐོར་ལ་གྲོས་བསྡུར་བྱེད་པ༦.txt'),
('shawo13.txt', 'shawo dolma62དགེ་འདུན་པའི་གྲངས་ཀ__REC015_1.txt'),
('khando1.txt', 'SangyeKhar__8 མུ་མཐུད་ནས་གྲྭ་པ་ཡོང་ཕྱིར་་་་.txt'),
('khar23.txt', 'Khando Dolma_46འཛིན་གྲྭའི་རེའི་མིག__REC008.txt'),
('Dorji Tsering16.txt', 'Jampa_3གཞན་ལ་ཞེ་སྡང་དང་ང་རྒྱལ་འགོག་པ།__REC029_2.txt'),
('Jampa 14.txt', 'Dawa_35__མི་གཅིག་གིས་དགེ་བའི་ལས་གང་བསྒྲུབས་པ་དེའི་སྐོར།1.txt'),
('palgun dawa 46.txt', 'Kunkyab_37།__སྟོན་པ་རྗེ་ཙོང་ཁ་པའི་གོ་འཕངས༢.txt'),
('khando9.txt', 'Sangye Khar_25ྱགས་འཚལ་སྟངས།__གྲྭ་ཆས་གོན་སྟངས་དང་ཕྲག་འཚལ་སྟངས༣.txt'),
('palgun dawa 47.txt', 'Kunkyab_37།__སྟོན་པ་རྗེ་ཙོང་ཁ་པའི་གོ་འཕངས༡.txt'),
('Jampa 12.txt', 'Dawa_29 __བསྡུས་གྲྭ་དང་བོད་ཡིན་སློབ་པ།1.txt'),
('khando12.txt', 'Sangye Khar_59།__གཏོར་མ་བཟོ་སྟངས༡.txt'),
('18 Chokdup.txt', 'Kunkyab_17།__བོད་སྐད་སློབ་པ་དང་སྦྱོང་བའི་སྐོར༣.txt'),
('khando16.txt', 'Sangye Khar_38།__སངས་རྒྱས་དང་བྱང་ཆུབ་སེམས་དཔའ༡.txt'),
('shawo3.txt', 'Chokdup_53__བཀྲིས་ཉལ་ཁང་དུ་ལོག་ནས་ངལ་གསོ་འདོད་པ།1.txt'),
('Dorji Tsering2.txt', 'Jampa__5 མཚན་མོ་གཉིད་ཁུག་ཡ་མ་་བྱུང་་་་་་་.txt'),
('khando41.txt', 'Kunkyab_57ཁ་ལག་དང་། ་ཁག__ཁ་ལག་དང་ཉིན་རེའི་དགོས་མཁོ༢.txt'),
('Jampa 25.txt', 'Dawa_69__བླ་མས་ཆོས་ཀྱི་མཇུག་སྡོམ་གནད་བསྡུས་གསུངས་པ།2.txt'),
('khar6.txt', 'Khando Dolma_ཊཱ་མ་རུ་དང་བསྐང་གསོལ་སྐོར།__60.txt'),
('16 Chokdup.txt', 'Kunkyab_17།__བོད་སྐད་སློབ་པ་དང་སྦྱོང་བའི་སྐོར༡.txt'),
('khar9.txt', 'Khando Dolma61སློབ་སྦྱོང་དང་མཉམ་ལེན་བྱེད་སྟངས།__REC032_1.txt'),
('khar26.txt', 'Khando Dolma51ཆོས་ཀྱི་བྱེད་སྒོ་ཞིག་གི་སྔོན་དུ__REC002_2.txt'),
('Jampa 5.txt', 'Dawa_67__ལྷ་ཁང་དང་ཡུལ་ལྗོངས་གཙང་མ་བཟོ་བ།1.txt'),
('shawo10.txt', 'shawo dolma28འཛིན་གྲོགས་ག་འདྲ་བསྟེན་དགོས་མིན།__REC001_1.txt'),
('shawo6.txt', 'Chokdup_31__བགྲོ་གླེང་གི་སྐོར་བཤད་པ།2.txt'),
('Jampa 18.txt', 'Dawa_44__གཞན་ལ་བསམ་བློ་གཏོང་རྒྱུ།1.txt'),
('shawo7.txt', 'Chokdup_30__བོད་ཡིག་ཀློག་རྩལ་དང་འབྲི་རྩལ།1.txt'),
('shawo26.txt', 'shawo dolma_དྲ་ལམ་བརྒྱུད་ནས་བསྡུས་གྲྭ་ཁྲིད་པ།__15 1.txt'),
('shawo24.txt', 'shawo dolma_4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_5.txt'),
('Jampa 1.txt', 'Dawa_48__འཛིན་གྲའི་སློབ་མའི་གནས་སྟངས་སྐོར།1.txt'),
('shawo32.txt', 'shawo lma__4གྲྭ་ཤག་སྐམ་རློམ་སོགས་ཇི་ལྟར་ཡར་རྒྱུས་གཏོང་ཚུལ་སྐོར།.txt'),
('shawo21.txt', 'shawo dolma_4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_2.txt'),
('Jampa 27.txt', 'Dawa_8དགེ་རྒན་དང་བླ་མའི་ཡོན་ཏན།__REC005_2.txt'),
('khar22.txt', 'Khando Dolma_4ཕ་མའི་བཀའ་དྲིན་སྐོར།__REC0013_2.txt'),
('6 Chokdup.txt', 'Kunkyab_66།__བོད་སྐད་ཡིག་གི་གནས་ཚད་མཐོ་རུ་གཏོང་སྟངས༡.txt'),
('shawo25.txt', 'shawo dolma_4སྒྲིག་ཁྲིམས་ཀྱི་ཐོག་ལ་གྲོས་བསྡུར་བྱེད་པའི་སྐོར།__REC010_6.txt'),
('khando8.txt', 'Sangye Khar_25ས་འཚལ་སྟངས།__གྲྭ་ཆས་གོན་སྟངས་དང་ཕྱག་འཚལ་སྟངས༢.txt'),
('Jampa 28.txt', 'Dawa_81__དགོན་པར་མཇལ་བསྐོར།1.txt'),
('khando5.txt', 'Sangye Khar_40།__ཕ་མའི་བཀའ་དྲིན་སྐོར༡.txt'),
('Jampa 3.txt', 'Dawa_49__བཙུན་དགོན་དུ་རིན་པོ་ཆེ་ཆོས་གསུང་ཀ་ཕེབས་པ།1.txt'),
('shawo12.txt', 'shawo dolma28འཛིན་གྲོགས་ག་འདྲ་བསྟེན་དགོས་མིན།__REC001_3.txt'),
('khar4.txt', 'Khando Dolma___50རིན་པོ་ཆེ་བཙུན་དགོན་ལ་ཕེབས་བསུ། (2).txt'),
('Dorji Tsering12.txt', 'Jampa_4གནའ་བོའི་དམ་པ་གོང་མ་རྣམས།__REC011_2.txt'),
('khar7.txt', 'Khando Dolma65གཞུང་བཀའ་པོད་ལྔའི་སྐོར།__REC017_1.txt'),
('Jampa 8.txt', 'Dawa_13__བླ་མ་བསྟེན་ཚུལ་དང་། འཆི་བ། ལས་དབང་།2.txt'),
('shawo5.txt', 'Chokdup_31__བགྲོ་གླེང་གི་སྐོར་བཤད་པ།1.txt')]


pairs4 = [('Jampa 58.txt', 'གནས་ཚུལ།__གུར་དང་མཐུན་རྐྱེན།.txt'),
('khar32.txt', 'གཞན་གྱི་སྐོར།__ཨ་ནེའི་སྐོར།.txt'),
('palgun dawa 28.txt', 'སྐད་ཡིག__ཐ་སྙད་རྒྱུག་ཆེ་ཆུང་གི་སྐོར།.txt'),
('Sherab 14.txt', 'ཆོས་ལུགས།__སྔགས་ཀྱི་སྐོར།.txt'),
('Jampa 55.txt', 'ཟ་མ།__ཁ་ལག་ཟ་སྟངས་ཀྱི་སྐོར།.txt'),
('Jampa 41.txt', 'ལམ་སྟོན།__ཕྱི་ལ་ཐོན་ཁར་མངགས་བྱ་བྱས་པ།.txt'),
('Sherab 28.txt', 'འཕྲུལ་ཆས།__གློག་ཀླད་ཀྱི་སྐོར།.txt'),
('palgun dawa 42.txt', 'བྱེད་སྒོ།__གྲྭ་ཤ་ག་གཙང་མ་བཟོ་བ།.txt'),
('Sherab 30.txt', 'གནས་ཚུལ།__བཙོན་ཁང་གི་སྐོར།.txt'),
('palgun dawa 2.txt', 'གནས་ཚུལ།__ཆུ་བཏང་བའི་སྐོར། .txt'),
('shawo41.txt', 'ཟ་མ།__ཉིན་གུང་བཞེས་ལག་གི་སྦྱིན་བདག་གླེང་བ།.txt'),
('Jampa 32.txt', 'ཆོས་ལུགས།__སྐྱབས་རྟེན་དང་མ་ཎི་རིལ་བུ།.txt'),
('Jampa 36.txt', 'རང་གི་སྐོར།__རླངས་འཁོར་དུ་འགྲོ་བར་ཞེད་པ།.txt'),
('palgun dawa 20.txt', 'གནས་ཚུལ།__གློག་བརྙན་ཞིག་གི་སྐོར་བཤད་པ། .txt'),
('khar34.txt', 'ཟ་མ།__ཐབ་ཚང་དང་ཁ་ལག.txt'),
('palgun dawa 26.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་གི་དགོས་པ་བཤད་པ།.txt'),
('Jampa 62.txt', 'གཞན་གྱི་སྐོར།__བུ་དེ་སླེབས་ཡོད་མེད་སྐད་ཆ་འདྲི་བ།.txt'),
('khar29.txt', 'ཟ་མ།__ཨ་རག་གསར་རྙིང་། .txt'),
('palgun dawa 39.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཁ་པར་བརྒྱབ་མིན་གྱི་སྐོར།.txt'),
('palgun dawa 41.txt', 'ཟ་མ།__འཐེན་ཐུག་མངགས་ཉོང་བྱེད་པ།༡.txt'),
('palgun dawa 15.txt', 'སྐད་ཡིག__བོད་སྐད་ཀྱི་རིན་ཐང་གླེང་བ།.txt'),
('shawo47.txt', 'ལམ་སྟོན།__བརྟན་པོ་བཟོ་རོགས་བྱོས།.txt'),
('palgun dawa 31.txt', 'ཟ་མ།__ཇ་དང་ཟ་མའི་སྐོར། .txt'),
('Sherab 7.txt', 'རང་གི་སྐོར།__ནང་མིའི་སྐོར་གླེང་བ།.txt'),
('Jampa 46.txt', 'ཟ་མ།__ཁ་སང་ཟ་མ་མ་ཟོས་པ་དང་རྙོག་དྲ་གཞན།.txt'),
('Sherab 18.txt', 'བྱེད་སྒོ།__དགོན་པའི་དབྱར་གནས་སྐོར།.txt'),
('palgun dawa 17.txt', 'ཆོས་ལུགས།__བླ་མ་རྒོད་ཚང་པའི་རྣམ་ཐར་འཚོལ་བ།༢.txt'),
('Jampa 45.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཉོ་ཆ་དང་ཤག་རོགས་སྐོར།.txt'),
('Jampa 61.txt', 'གཞན་གྱི་སྐོར།__སྣ་ཐ་གཅོད་པའི་སྐོར།.txt'),
('shawo34.txt', 'གནས་ཚུལ།__དྲ་ལམ་བླུག་ཏུ་འགྲོ་དགོས་རབས་བཤད་པ། .txt'),
('palgun dawa 36.txt', 'གནས་ཚུལ།__ཁང་གླ་གཏོང་ཚུལ་འདི་འདྲ་རེད།.txt'),
('Jampa 57.txt', 'གནས་ཚུལ།__གུར་རྒྱག་སའི་ས་ཆའི་སྐོར།.txt'),
('Sherab 10.txt', 'ལམ་སྟོན།__ཕན་ཚུན་ཚང་མས་མཐུན་སྒྲིལ་བྱེད་དགོས་ཚུལ་བཤད་པ།.txt'),
('Sherab 11.txt', 'རང་གི་སྐོར།__དྲ་ཐོག་ནས་སྒེར་འབྲེལ་བྱས་པའི་སྐོར།.txt'),
('palgun dawa 22.txt', 'སྐད་ཡིག__སྐད་དང་ཡི་གེའི་སྐོར་གླེང་བ།.txt'),
('palgun dawa 40.txt', 'བྱེད་སྒོ།__དབྱར་གནས་དང་འབྲེལ་བའི་གཏམ་གླེང་།.txt'),
('palgun dawa 10.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__གང་བྱུང་མང་བྱུང་བཤད་པ།.txt'),
('Jampa 38.txt', 'གནས་ཚུལ།__ཆུ་ཚོད་བཤད་པ།.txt'),
('palgun dawa 21.txt', 'དངུལ་དང་རྩིས།__རིན་པོ་ཆེར་སྒྲ་འཇུག་གནང་རོགས་ཞུས་པ།.txt'),
('Sherab 13.txt', 'སློབ་སྦྱོང་།__དགེ་བཤེས་ཐོན་པའི་སྐོར།.txt'),
('Sherab 4.txt', 'སློབ་སྦྱོང་།__དཔེ་ཀློག་གི་སྐོར། .txt'),
('palgun dawa 9.txt', 'དངུལ་དང་རྩིས།__ཞབས་བརྟན་གྲངས་དང་ཚེས་གྲངས་སྐོར། .txt'),
('shawo51.txt', 'ལམ་སྟོན།__ཡི་གེའི་འོག་ཏུ་ཐིག་རྒྱག་ཚུལ་བཤད་པ།༡.txt'),
('Sherab 17.txt', 'བྱེད་སྒོ།__ཉིན་གཅིག་གི་བྱེད་སྒོ།.txt'),
('palgun dawa 25.txt', 'སྐད་ཡིག__བསྟན་བཅོས་ཀྱི་སྐད་དང་དམངས་ཀྱི་སྐད།.txt'),
('shawo36.txt', 'ལམ་སྟོན།__ཉར་ཚགས་བྱེད་སྟངས་སྐོར་བཤད་པ།༡.txt'),
('palgun dawa 34.txt', 'ཆོས་ལུགས།__ཡོན་ཆབ་བཤམས་པ།.txt'),
('palgun dawa 5.txt', 'དངུལ་དང་རྩིས།__རྩིས་དེ་འཁྲུག་སོང་ན་རྙོག་དྲ་རེད།.txt'),
('Sherab 29.txt', 'གནས་ཚུལ།__རྙོག་དྲའི་སྐོར།.txt'),
('Sherab 5.txt', 'སློབ་སྦྱོང་།__སློབ་སྦྱོང་གི་སྐོར།.txt'),
('Jampa 43.txt', 'དངུལ་དང་རྩིས།__སང་ཉིན་གྱི་བཞེས་ལག་དང་འགྲོ་སོང་།.txt'),
('Jampa 59.txt', 'འཕྲུལ་ཆས།__གློག་དང་ཁ་པར་ཨང་གྲངས།.txt'),
('palgun dawa 8.txt', 'དངུལ་དང་རྩིས།__ཞབས་རིམ་གྱི་གྲངས་ཀའི་སྐོར།.txt'),
('Sherab 21.txt', 'ལམ་སྟོན།__སྤྱོད་ལམ་སྐོར།.txt'),
('Sherab 9.txt', 'ལམ་སྟོན།__མདུན་ལམ་ལམ་སྟོན།.txt'),
('Sherab 25.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་སྐབས་གཟབ་དགོས་པའི་སྐོར།.txt'),
('Jampa 50.txt', 'རང་གི་སྐོར།__སེམས་ཁྲལ་བྱས་པའི་སྐོར།.txt'),
('Jampa 40.txt', 'གཞན་གྱི་སྐོར།__བུ་མོ་ཞིག་གྲོངས་པའི་སྐོར།.txt'),
('khar31.txt', 'བྱེད་སྒོ།__ཐོ་བཤེར། .txt'),
('Jampa 49.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཐང་ཆད་པ་དང་ཚོང་གི་སྐོར།.txt'),
('Jampa 44.txt', 'ལམ་སྟོན།__ཚལ་གཏུབ་སྟངས་དང་ལས་ཀ་མངགས་པ།.txt'),
('shawo50.txt', 'ལམ་སྟོན།__ཡི་གེ་ཡག་པོ་སྦྱོང་དགོས་སྐོར་གྱི་ལམ་སྟོན།.txt'),
('Jampa 52.txt', 'དངུལ་དང་རྩིས།__དངུལ་དང་གྲངས་ཀ.txt'),
('Jampa 56.txt', 'གནས་ཚུལ།__ཁང་པའི་ནང་དུ་རྒྱུན་རིང་པོར་བསྡད་མཁན་གྱི་སྐོར།.txt'),
('Sherab 15.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་དང་འབྲེལ་ཡོད།.txt'),
('Sherab 23.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་བྱེད་པའི་དགོས་པ།.txt'),
('Sherab 19.txt', 'བྱེད་སྒོ།__ཆོས་ར་ཚོགས་སྟངས།.txt'),
('palgun dawa 4.txt', 'འཕྲོད་བསྟེན།__འཆམ་ནད་ཕོག་པ་དེ་དཀའ་ལས་ཞེ་པོ་ཞིག་འདུག.txt'),
('palgun dawa 27.txt', 'སྐད་ཡིག__དབྱིན་ཇིའི་ཡིག་ཆད་སྐོར་ནས་གླེང་བ།.txt'),
('palgun dawa 11.txt', 'ཆོས་ལུགས།__ཁ་ཆེའི་ལྟ་བ་གླེང་བ།.txt'),
('Jampa 30.txt', 'གནས་ཚུལ།__ཁང་མིག་འཚོལ་བ་དང་སྐད་ཆ་འདྲི་བ།.txt'),
('shawo35.txt', 'ལམ་སྟོན།__ཉར་ཚགས་བྱེད་སྟངས་སྐོར་བཤད་པ།.txt'),
('palgun dawa 30.txt', 'གཞན་གྱི་སྐོར།__དྷ་སར་ཡོང་ཡོད་པའི་སྐོར། .txt'),
('Jampa 48.txt', 'ཟ་མ།__དགོང་མོའི་ཁ་ལག་སྐོར།.txt'),
('palgun dawa 13.txt', 'སྐད་ཡིག__དབྱིན་ཡིག་སྦྱོང་དགོས་རབས་བཤད་པ།.txt'),
('palgun dawa 14.txt', 'སྐད་ཡིག__དབྱིན་ལན་གྱི་གནས་སྟངས་གླེང་བ།.txt'),
('khar30.txt', 'ཟ་མ།__དགེ་རྒན་ལ་ཁ་ལག་སྤྲད་པ། .txt'),
('shawo42.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__དཔར་སློག་གི་སྐོར་ནས་ཆོབ་བསླངས་པའི་སྐོར།.txt'),
('khar33.txt', 'ལམ་སྟོན།__ལས་ཀར་མངགས་པ།.txt'),
('palgun dawa 35.txt', 'དངུལ་དང་རྩིས།__ཤོག་དངུལ་གསེས་མ་བརྗེ་བ།.txt'),
('Jampa 39.txt', 'དངུལ་དང་རྩིས།__དངུལ་གྱི་གྲངས་ཀ་དང་ཆམ་པའི་སྐོར།.txt'),
('palgun dawa 43.txt', 'སློབ་སྦྱོང་།__འཛིན་རིམ་ཐོན་པའི་སྐོར་བཤད་པ། .txt'),
('shawo45.txt', 'འཕྲུལ་ཆས།__གཏགས་པའི་ཡི་གེ་བརླག་ཚུལ་བཤད་པ།.txt'),
('Jampa 47.txt', 'དངུལ་དང་རྩིས།__རྩིས་ཀྱི་སྐོར།.txt'),
('Jampa 60.txt', 'ཆོས་ལུགས།__དུས་འཁོར་དབང་ཆེན་གྱི་སྐོར།.txt'),
('shawo40.txt', 'གནས་ཚུལ།__ཆུ་ཚོད་གཉིས་དང་ཕྱེད་ཀ་ནས་འཛོམས་དགོས་རབས་བཤད་པ།.txt'),
('palgun dawa 3.txt', 'ཆོས་ལུགས།__མཁན་རིན་པོ་ཆེ་ལ་ཕྱག་མོ་གཟིགས་དགོས་ཚུལ།.txt'),
('palgun dawa 1.txt', 'གཞན་གྱི་སྐོར།__མི་ཞིག་གི་འདས་མཆོད་སྐོར། .txt'),
('palgun dawa 33.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཁང་པ་སྐྱིད་པོ་ཡོད་རབས་བཤད་པ།.txt'),
('Jampa 54.txt', 'ཟ་མ།__མོག་མོག་གི་སྐོར།.txt'),
('Sherab 24.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཀུ་ཤུ་དང་སྐུ་ཞབས་ནོར་བ།.txt'),
('palgun dawa 37.txt', 'ཆོས་ལུགས།__ནང་ཆོས་ངོ་སྤྲོད་དེ་ཡག་པོ་ཡོད་ཚུལ།.txt'),
('palgun dawa 24.txt', 'འཕྲུལ་ཆས།__མི་དང་འཕྲུལ་ཆས་ཀྱི་ཁྱད་པར་བཤད་པ།.txt'),
('palgun dawa 12.txt', 'སྐད་ཡིག__དབྱིན་ཡིག་བཀླགས་པའི་སྐོར།.txt'),
('shawo48.txt', 'ལམ་སྟོན།__ཡི་གེའི་འོག་ཏུ་ཐིག་རྒྱག་ཚུལ་བཤད་པ།.txt'),
('palgun dawa 29.txt', 'གནས་ཚུལ།__མདོ་སྨད་ཀྱི་རྗོང་ཆེན་བཞི།.txt'),
('shawo39.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__ཅི་འཕྲོས་མོལ་འཕྲོས།.txt'),
('Jampa 53.txt', 'ཟ་མ།__ཁ་ལག་བཟོ་བར་དུས་ཚོད་ཀྱིས་མ་འདང་བ།.txt'),
('palgun dawa 38.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་དང་འབྲེལ་བའི་སྐད་ཆ།.txt'),
('Sherab 20.txt', 'འཕྲོད་བསྟེན།__མིག་གི་དཀའ་ངལ་སྐོར།.txt'),
('Sherab 6.txt', 'མི་སྣ།__རྒྱལ་བ་རིན་པོ་ཆེའི་སྐོར།.txt'),
('Dorji Tsering57.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__གང་བྱུང་མང་བྱུང་།.txt'),
('shawo38.txt', 'འཕྲུལ་ཆས།__གློག་ཀླད་འཕྲོ་བརླག་ལ་འགྲོ་ཚུལ་བཤད་པ།.txt'),
('Jampa 35.txt', 'ཆོས་ལུགས།__བསྔོ་རྟེན་དང་དངུལ་གྲངས།.txt'),
('Jampa 51.txt', 'ཟ་མ།__ཟ་མ་དང་དངུལ་གྱི་སྐོར།.txt'),
('shawo37.txt', 'རང་གི་སྐོར།__གོང་མ་གསུམ་ཆ་ནས་རང་བསྟོད་བཤད་པ།.txt'),
('shawo43.txt', 'ལམ་སྟོན།__དཔར་སློག་དགོས་རབས་བཤད་པ།.txt'),
('palgun dawa 16.txt', 'འཕྲོད་བསྟེན།__མིག་གི་སྐོར་བཤད་པ།.txt'),
('shawo49.txt', 'སློབ་སྦྱོང་།__ཡིག་གཟུགས་བསླབ་པ།.txt'),
('palgun dawa 18.txt', 'ཆོས་ལུགས།__བླ་མ་རྒོད་ཚང་པའིརྣམ་ཐར་འཚོལ་བ།༡.txt'),
('Sherab 27.txt', 'སྒྲ་འཇུག__སྒྲ་འཇུག་ལ་བསྐྱར་ཉན་བྱེད་པ།.txt'),
('shawo44.txt', 'གནས་ཚུལ།__ཚོགས་འདུའི་སྐོར་བཤད་པ།.txt'),
('palgun dawa 7.txt', 'སྐད་ཡིག__དེབ་ཀྱི་སྐོར།.txt'),
('palgun dawa 19.txt', 'སྐད་ཡིག__རྒྱུན་ལྡན་གྱི་སྐད་དེ་གལ་ཆེན་རབས་བཤད་པ།.txt'),
('palgun dawa 23.txt', 'གཞན་གྱི་སྐོར།__ཚེ་རིང་དཔལ་ལྡན་འཚོལ་བ།.txt'),
('Jampa 31.txt', 'བྱེད་སྒོ།__མཆོད་པ་གཤེག་པའི་སྐོར།.txt'),
('shawo46.txt', 'སློབ་སྦྱོང་།__དབྱིན་ཇིའི་ཡིག་ཚད་གླེང་བ།.txt'),
('shawo52.txt', 'མི་སྣ།__རིན་པོ་ཆེན་ཁ་ཤས་ཤིག་གི་ཡོན་ཏན་གླེང་བ།.txt'),
('Jampa 37.txt', 'ཟ་མ།__ཁ་ལག་བཟོ་བ།.txt'),
('Sherab 16.txt', 'བྱེད་སྒོ།__སློབ་གྲྭའི་འགྲོ་སྟངས། .txt'),
('Jampa 34.txt', 'ཆོས་ལུགས།__སྐྱབས་རྟེན་དང་བསྔོ་རྟེན།.txt'),
('Jampa 42.txt', 'ཟ་མ།__ཇ་དང་ཆུ་ཡི་སྐོར།.txt'),
('Sherab 12.txt', 'བྱེད་སྒོ།__ཉིན་རེའི་བྱེད་སྒོ།.txt'),
('Sherab 32.txt', 'ཅི་འཕྲོས་མོལ་འཕྲོས།__སྒོར་མོ་ལྔ་བརྒྱ་ཅན་གྱི་ཅ་ལག་དེ་ཉོ་འདོད་རབས།.txt'),
('Sherab 8.txt', 'ལམ་སྟོན།__ཕྲུ་གུའི་འདུན་ལམ་ལམ་སྟོན།.txt'),
('palgun dawa 32.txt', 'འཕྲོད་བསྟེན།__ང་ཟི་ལིང་ལ་སྨན་པ་བསྟེན་དུ་སོང་བ་ཡིན། .txt')]


for i in range(len(pairs4)):
    pairs4[i] = (original_path+pairs4[i][0], export_path+'/'+pairs4[i][0], export_path+'/'+pairs4[i][1], delete_path+pairs4[i][1])

extract_subset(export_path, pairs4)