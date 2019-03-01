/**
 * Copyright (C) 2019  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const GenerateWebLabelsPlugin = require('./index');

test('extractLicenseInformation supports missing license/licenses', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    // FIXME: it should probably return an empty list
    expect(plugin.extractLicenseInformation({
    })).toEqual([
        {
            "copy_url": "",
            "name": undefined,
            "url": ""
        },
    ]);
    expect(plugin.logger.warn).toBeCalled();
});


test('extractLicenseInformation parses an empty "licenses"', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    // FIXME: it should probably return an empty list
    expect(plugin.extractLicenseInformation({
        "licenses": [],
    })).toEqual([
        {
            "copy_url": "",
            "name": "",
            "url": ""
        },
    ]);
    expect(plugin.logger.warn).toBeCalled();
});

test('extractLicenseInformation parses "licenses" with one item', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    expect(plugin.extractLicenseInformation({
        "licenses": [
            {
                "type": "MIT",
                "url": "https://www.opensource.org/licenses/mit-license.php"
            },
        ],
    })).toEqual([
        {
            "copy_url": "",
            "name": "Expat License", 
            "url": "http://www.jclark.com/xml/copying.txt"
        },
    ]);
    expect(plugin.logger.warn).not.toBeCalled();
});

test('extractLicenseInformation parses "licenses" with two items', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    expect(plugin.extractLicenseInformation({
        "licenses": [
            {
                "type": "MIT",
                "url": "https://www.opensource.org/licenses/mit-license.php"
            },
            {
                "type": "Apache-2.0",
                "url": "https://opensource.org/licenses/apache2.0.php"
            },
        ],
    })).toEqual([
        {
            "copy_url": "",
            "name": "Expat License", 
            "url": "http://www.jclark.com/xml/copying.txt"
        },
        {
            "copy_url": "",
            "name": "Apache License, Version 2.0", 
            "url": "http://www.apache.org/licenses/LICENSE-2.0"
        },
    ]);
    expect(plugin.logger.warn).not.toBeCalled();
});


test('extractLicenseInformation parses a simple license id', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    expect(plugin.extractLicenseInformation({
        "license": "MIT",
    })).toEqual([
        {
            "copy_url": "",
            "name": "Expat License", 
            "url": "http://www.jclark.com/xml/copying.txt"
        },
    ]);
    expect(plugin.logger.warn).not.toBeCalled();
});

test('extractLicenseInformation parses an SPDX expression with an OR', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    expect(plugin.extractLicenseInformation({
        "license": "MIT OR GPL-3.0",
    })).toEqual([
        {
            "copy_url": "",
            "name": "Expat License", 
            "url": "http://www.jclark.com/xml/copying.txt"
        },
        {
            "copy_url": "",
            "name": "GNU General Public License (GPL) version 3", 
            "url": "http://www.gnu.org/licenses/gpl-3.0.html"
        },
    ]);
    expect(plugin.logger.warn).not.toBeCalled();
});

test('extractLicenseInformation warns on an SPDX with an AND', () => {
    let plugin = new GenerateWebLabelsPlugin({});
    plugin.logger = { warn: jest.fn() };

    // FIXME: it should refuse it outright
    expect(plugin.extractLicenseInformation({
        "license": "MIT AND GPL-3.0",
    })).toEqual([
        {
            "copy_url": "",
            "name": "Expat License", 
            "url": "http://www.jclark.com/xml/copying.txt"
        },
        {
            "copy_url": "",
            "name": "GNU General Public License (GPL) version 3", 
            "url": "http://www.gnu.org/licenses/gpl-3.0.html"
        },
    ]);
    expect(plugin.logger.warn).toBeCalled();
});
