# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


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
