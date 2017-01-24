Welcome to Software Heritage project's API documentation.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Version](#version)
- [Schema](#schema)
- [Mimetype override](#mimetype-override)
- [Parameters](#parameters)
    - [Global parameter](#global-parameter)
- [Client errors](#client-errors)
    - [Bad request](#bad-request)
    - [Not found](#not-found)
- [Terminology](#terminology)
    - [Content](#content)
    - [(Cryptographic) hash](#cryptographic-hash)
    - [Directory](#directory)
    - [Origin](#origin)
    - [Project](#project)
    - [Release](#release)
    - [Revision](#revision)
- [Opened endpoints](#opened-endpoints)

<!-- markdown-toc end -->


### Version

Current version is [1](/api/1/).

### Schema

Api access is over https and accessed through [https://archive.softwareheritage.org/api/1/](/api/1/).

Data is sent and received in json by default.

Examples:

- [/api/1/stat/counters/](/api/1/stat/counters/)

- From the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/stat/counters/
```


#### Mimetype override

The response output can be sent as yaml provided the client specifies
it using the header field.

Examples:

- From your favorite REST client API, execute the same request as
  before with the request header 'Accept' set to the
  'application/yaml'.

- From the command line:
``` shell
curl -i -H 'Accept: application/yaml' https://archive.softwareheritage.org/api/1/stat/counters/
```

### Parameters

Some API endpoints can be used with with local parameters. The url
then needs to be adapted accordingly.

For example:

``` text
https://archive.softwareheritage.org/api/1/<endpoint-name>?<field0>=<value0>&<field1>=<value1>
```

where:

- field0 is an appropriate field for the <endpoint-name> and value0
- field1 is an appropriate field for the <endpoint-name> and value1

#### Global parameter

One parameter is defined for all api endpoints `fields`.  It permits
to filter the output fields per key.

For example, to only list the number of contents, revisions,
directories on the statistical endpoints, one uses:

Examples:

- [/api/1/stat/counters/\?fields\=content,directory,revision](/api/1/stat/counters/?fields=content,directory,revision)

- From the command line:
``` shell
curl https://archive.softwareheritage.org/api/1/stat/counters/\?fields\=content,directory,revision
```

Note: If the keys provided to filter on do not exist, they are
ignored.

### Client errors

There are 2 kinds of error.

In that case, the http error code will reflect.  Furthermore, the
response is a dictionary with one key 'error' detailing the problem.

#### Bad request

This means that the input is incorrect.

Example:

- [/api/1/content/1/](/api/1/content/1/)

- From the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/content/1/
```

The api content expects an hash identifier so the error will mention
that an hash identifier is expected.

#### Not found

This means that the request is ok but we do not found the information
the user requests.

Examples:

- [/api/1/content/04740277a81c5be6c16f6c9da488ca073b770d7f/](/api/1/content/04740277a81c5be6c16f6c9da488ca073b770d7f/)

- From the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/content/04740277a81c5be6c16f6c9da488ca073b770d7f/
```

The hash identifier is ok but nothing is found for that identifier.

### Terminology

You will find below the terminology the project SWH uses.
More details can be found
on
[swh's wiki glossary page](https://wiki.softwareheritage.org/index.php?title=Glossary).

#### Content

A (specific version of a) file stored in the archive, identified by
its cryptographic hashes (SHA1, "git-like" SHA1, SHA256) and its size.

Also known as: Blob Note.

#### (Cryptographic) hash

A fixed-size "summary" of a stream of bytes that is easy to compute,
and hard to reverse.

Also known as: Checksum, Digest.

#### Directory

A set of named pointers to contents (file entries), directories
(directory entries) and revisions (revision entries).

#### Origin

A location from which a coherent set of sources has been obtained.

Also known as: Data source.

Examples:

- a Git repository
- a directory containing tarballs
- the history of a Debian package on snapshot.debian.org.

#### Project

An organized effort to develop a software product.

Projects might be nested following organizational structures
(sub-project, sub-sub-project), are associated to a number of
human-meaningful metadata, and release software products via Origins.

#### Release

A revision that has been marked by a project as noteworthy with a
specific, usually mnemonic, name (for instance, a version number).

Also known as: Tag (Git-specific terminology).

Examples:

- a Git tag with its name
- a tarball with its name
- a Debian source package with its version number.

#### Revision

A "point in time" snapshot in the development history of a project.

Also known as: Commit

Examples:

- a Git commit

### Opened endpoints

Accessible through [https://archive.softwareheritage.org/api/1/](/api/1/).
