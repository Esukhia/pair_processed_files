from PyTib.common import open_file, get_longest_common_subseq
import os
import itertools
import shutil
import logging


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
        prefix = new_prefix(filename, parts=[7, 9])
        prefix = prefix.replace(''.join(get_longest_common_subseq([name, prefix])), '')
        new_name = '{}__{}'.format(prefix, name)

        # create directory if not yet existing
        create_missing_dir(destination)

        # copy the file and rename it right after
        shutil.copy(filename, destination)
        os.rename('{}/{}'.format(destination, name), '{}/{}'.format(destination, new_name))

#move('/home/swan/Documents/modern_tib_corpus/5 studio recording for Nanhai nunnery/Not Segmented', '/home/swan/Documents/modern_tib_corpus/flattened')
move('/home/swan/Documents/modern_tib_corpus/4 monastery and nunnery with list/unsegmented', '/home/swan/Documents/modern_tib_corpus/flattened4')