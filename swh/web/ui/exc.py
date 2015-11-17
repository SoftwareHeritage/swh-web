# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


class BadInputExc(ValueError):
    def __init__(self, errorMsg):
        super().__init__(errorMsg)


class NotFoundExc(Exception):
    def __init__(self, errorMsg):
        super().__init__(errorMsg)
