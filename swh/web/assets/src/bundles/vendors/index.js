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
import 'datatables.net-bs/css/dataTables.bootstrap.css';
import './datatables.css';

// web fonts
import 'typeface-alegreya';
import 'typeface-alegreya-sans';
import 'font-awesome/css/font-awesome.css';
import 'octicons/build/font/octicons.css';
