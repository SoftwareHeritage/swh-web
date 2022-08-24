'use strict';

let reportDir = 'cypress/coverage';
let tempDir = '.nyc_output';
const parallelBuildId = process.env.CYPRESS_PARALLEL_BUILD_ID;
if (parallelBuildId !== undefined) {
  reportDir += parallelBuildId;
  tempDir += parallelBuildId;
}

module.exports = {
  exclude: [
    'assets/src/bundles/vendors/index.js',
    'assets/src/thirdparty/**/*.js'
  ],
  'report-dir': reportDir,
  'temp-dir': tempDir
};
