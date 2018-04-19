// webapp entrypoint bundle centralizing global custom stylesheets
// and utility js modules used in all swh-web applications

// explicitely import the vendors bundle
import '../vendors';

// global swh-web custom stylesheets
import './webapp.css';
import './breadcrumbs.css';

// utility js modules
export * from './code-highlighting';
export * from './markdown-rendering';
