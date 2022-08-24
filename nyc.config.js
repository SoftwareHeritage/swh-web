'use strict';

let reportDir = 'cypress/coverage';
const parallelBuildId = process.env.CYPRESS_PARALLEL_BUILD_ID;
if (parallelBuildId !== undefined) {
  reportDir += parallelBuildId;
}

module.exports = {
  exclude: [
    'assets/src/bundles/vendors/index.js',
    'assets/src/thirdparty/**/*.js'
  ],
  'report-dir': reportDir
};
