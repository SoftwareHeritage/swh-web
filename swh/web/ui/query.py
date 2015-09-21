# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import re


def parse(args):
    """Parse a formalized get query.

    Arg:
        args, a dictionary of values:
        - nb_hashes is the number of hashes expected to be found in args
        - hash# with # a number between 1 and nb_hashes
    """
    nb_hashes = int(args.get('nb_hashes', '1'))

    hashes = []
    for i in range(1, nb_hashes + 1):
        key = 'hash' + str(i)
        v = args[key]
        if v and len(v) > 0:
            hashes.append(v)
        else:
            nb_hashes -= 1

    return nb_hashes, hashes


# Regexp to filter and check inputs
sha256_regexp='[0-9a-f]{64}'
sha1_regexp='[0-9a-f]{40}'


def group_by_checksums(hashes):
    """Check that the checksums have the right format.
    """
    hashes_m = {}
    for h in hashes:
        if re.search(sha256_regexp, h):
            hashes_m.update({'sha256': h})
        elif re.search(sha1_regexp, h):
            hashes_m.update({'sha1': h})

    return hashes_m
