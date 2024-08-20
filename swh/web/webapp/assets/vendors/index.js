/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// vendors bundles centralizing assets used in all swh-web applications

// polyfills in order to use advanced js features (like Promise or fetch)
// in browsers that do not support them
import 'core-js/stable';
import 'regenerator-runtime/runtime';
import 'whatwg-fetch/dist/fetch.umd';
import './elementsfrompoint-polyfill';

// jquery and bootstrap
import 'jquery';
import 'bootstrap-loader/lib/bootstrap.loader?configFilePath=../../../assets/config/.bootstraprc!bootstrap-loader/no-op.js';

// admin-lte scripts
import 'admin-lte';

// js-cookie
import 'js-cookie';

// datatables and extensions
import dataTable from 'datatables.net';
import 'datatables.net-bs4';
import 'datatables.net-fixedheader-bs4';
import 'datatables.net-bs4/css/dataTables.bootstrap4.css';
import 'datatables.net-fixedheader-bs4/css/fixedHeader.bootstrap4.css';
import './datatables.css';

// chosen-js
import 'chosen-js';
import 'chosen-js/chosen.min.css';

// web fonts
import 'typeface-alegreya';
import 'typeface-alegreya-sans';
import '@mdi/font/css/materialdesignicons.css';

// monitoring
import '@sentry/browser';

// fix js error on homepage due to admin-lte 3.2
localStorage.setItem('AdminLTE:IFrame:Options', JSON.stringify({}));

// ensure datatables jquery plugin is properly initialized
$.fn.dataTable = dataTable;
