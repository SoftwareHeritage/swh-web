Content
-------

.. http:get:: /api/1/content/[(hash_type):](hash)/

    Get information about a content (aka a "blob") object. 
    In the SWH archive, a content object is identified based on checksum
    values computed using various hashing algorithms.

    :param string hash_type: optional parameter specifying which hashing algorithm has been used
        to compute the content checksum. It can be either *sha1*, *sha1_git*, *sha256*
        or *blake2s256*. If that parameter is not provided, it is assumed that the 
        hashing algorithm used is *sha1*.
    :param string hash: hexadecimal representation of the checksum value computed with
        the specified hashing algorithm.

    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :>json object checksums: object holding the computed checksum values for the requested content
    :>json string data_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/raw/` 
        for downloading the content raw bytes
    :>json string filetype_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/filetype/`
        for getting information about the content MIME type
    :>json string language_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/language/`
        for getting information about the programming language used in the content
    :>json number length: length of the content in bytes
    :>json string license_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/license/` 
        for getting information about the license of the content

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested content can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "checksums": {
                "blake2s256": "791e07fcea240ade6dccd0a9309141673c31242cae9c237cf3855e151abc78e9",
                "sha1": "dc2830a9e72f23c1dfebef4413003221baa5fb62",
                "sha1_git": "fe95a46679d128ff167b7c55df5d02356c5a1ae1",
                "sha256": "b5c7fe0536f44ef60c8780b6065d30bca74a5cd06d78a4a71ba1ad064770f0c9"
            },
            "data_url": "/api/1/content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/raw/",
            "filetype_url": "/api/1/content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/filetype/",
            "language_url": "/api/1/content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/language/",
            "length": 151810,
            "license_url": "/api/1/content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/license/",
            "status": "visible"
        }
    
.. http:get:: /api/1/content/[(hash_type):](hash)/raw/

    Get the raw content of a content object (aka a "blob"), as a byte sequence.

    :param string hash_type: optional parameter specifying which hashing algorithm has been used
        to compute the content checksum. It can be either *sha1*, *sha1_git*, *sha256*
        or *blake2s256*. If that parameter is not provided, it is assumed that the 
        hashing algorithm used is *sha1*.
    :param string hash: hexadecimal representation of the checksum value computed with
        the specified hashing algorithm.
    :query string filename: if provided, the downloaded content will get that filename

    :resheader Content-Type: application/octet-stream

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested content can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/raw/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-disposition: attachment; filename=content_sha1_dc2830a9e72f23c1dfebef4413003221baa5fb62_raw
        Content-Type: application/octet-stream

        /* 'dir', 'vdir' and 'ls' directory listing programs for GNU.                                                                                                                                                                                                                  
        Copyright (C) 1985-2015 Free Software Foundation, Inc.                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                    
        This program is free software: you can redistribute it and/or modify                                                                                                                                                                                                        
        it under the terms of the GNU General Public License as published by                                                                                                                                                                                                        
        the Free Software Foundation, either version 3 of the License, or                                                                                                                                                                                                           
        (at your option) any later version.                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                    
        This program is distributed in the hope that it will be useful,                                                                                                                                                                                                             
        but WITHOUT ANY WARRANTY; without even the implied warranty of                                                                                                                                                                                                              
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                                                                                                                                                                                               
        GNU General Public License for more details.                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                    
        You should have received a copy of the GNU General Public License                                                                                                                                                                                                           
        along with this program.  If not, see <http://www.gnu.org/licenses/>.  */

        ...

.. http:get:: /api/1/content/[(hash_type):](hash)/filetype/

    Get information about the detected MIME type of a content object.

    :param string hash_type: optional parameter specifying which hashing algorithm has been used
        to compute the content checksum. It can be either *sha1*, *sha1_git*, *sha256*
        or *blake2s256*. If that parameter is not provided, it is assumed that the 
        hashing algorithm used is *sha1*.
    :param string hash: hexadecimal representation of the checksum value computed with
        the specified hashing algorithm.

    :>json object content_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/` for
        getting information about the content
    :>json string encoding: the detected content encoding
    :>json string id: the *sha1* identifier of the content
    :>json string mimetype: the detected MIME type of the content
    :>json object tool: information about the tool used to detect the content filetype

    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested content can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/filetype/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "content_url": "/api/1/content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/",
            "encoding": "us-ascii",
            "id": "dc2830a9e72f23c1dfebef4413003221baa5fb62",
            "mimetype": "text/x-c",
            "tool": {
                "configuration": {
                    "command_line": "file --mime "
                },
                "id": 7,
                "name": "file",
                "version": "5.22"
            }
        }

.. http:get:: /api/1/content/[(hash_type):](hash)/language/

    Get information about the programming language used in a content object.

    :param string hash_type: optional parameter specifying which hashing algorithm has been used
        to compute the content checksum. It can be either *sha1*, *sha1_git*, *sha256*
        or *blake2s256*. If that parameter is not provided, it is assumed that the 
        hashing algorithm used is *sha1*.
    :param string hash: hexadecimal representation of the checksum value computed with
        the specified hashing algorithm.

    :>json object content_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/` for
        getting information about the content
    :>json string id: the *sha1* identifier of the content
    :>json string lang: the detected programming language if any
    :>json object tool: information about the tool used to detect the programming language

    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested content can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/language/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "content_url": "/api/1/content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/",
            "id": "dc2830a9e72f23c1dfebef4413003221baa5fb62",
            "lang": "c",
            "tool": {
                "configuration": {
                    "debian-package": "python3-pygments",
                    "max_content_size": 10240,
                    "type": "library"
                },
                "id": 8,
                "name": "pygments",
                "version": "2.0.1+dfsg-1.1+deb8u1"
            }
        }


.. http:get:: /api/1/content/[(hash_type):](hash)/license/

    Get information about the license of a content object.

    :param string hash_type: optional parameter specifying which hashing algorithm has been used
        to compute the content checksum. It can be either *sha1*, *sha1_git*, *sha256*
        or *blake2s256*. If that parameter is not provided, it is assumed that the 
        hashing algorithm used is *sha1*.
    :param string hash: hexadecimal representation of the checksum value computed with
        the specified hashing algorithm.

    :>json object content_url: link to :http:get:`/api/1/content/[(hash_type):](hash)/` for
        getting information about the content
    :>json string id: the *sha1* identifier of the content
    :>json array licenses: array of strings containing the detected license names if any
    :>json object tool: information about the tool used to detect the license

    :reqheader Accept: the requested response content type, 
        either *application/json* (default) or *application/yaml*
    :resheader Content-Type: this depends on :http:header:`Accept` header of request

    :statuscode 200: no error
    :statuscode 400: an invalid *hash_type* or *hash* has been provided
    :statuscode 404: requested content can not be found in the SWH archive

    **Request**:

    .. parsed-literal::

        $ curl -i :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/license/`

    **Response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "content_url": "/api/1/content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/",
            "id": "dc2830a9e72f23c1dfebef4413003221baa5fb62",
            "licenses": [
                "GPL-3.0+"
            ],
            "tool": {
                "configuration": {
                    "command_line": "nomossa "
                },
                "id": 1,
                "name": "nomos",
                "version": "3.1.0rc2-31-ga2cbb8c"
            }
        }
