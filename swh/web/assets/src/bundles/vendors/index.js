/**
 * Copyright (C) 2018  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// vendors bundles centralizing assets used in all swh-web applications

// polyfills in order to use advanded js features (like Promise or fetch)
// in older browsers
import 'babel-polyfill';
import 'whatwg-fetch';

// jquery and bootstrap
import 'jquery';
import 'bootstrap-loader/lib/bootstrap.loader?configFilePath=../../../swh/web/assets/config/.bootstraprc!bootstrap-loader/no-op.js';

// jquery datatables
import 'datatables.net';
import 'datatables.net-bs4/css/dataTables.bootstrap4.css';
import './datatables.css';

// web fonts
import 'typeface-alegreya';
import 'typeface-alegreya-sans';
import 'font-awesome/css/font-awesome.css';
import 'octicons/build/font/octicons.css';
