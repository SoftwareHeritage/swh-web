const {defineConfig} = require('cypress');

module.exports = defineConfig({
  projectId: 'swh-web',
  video: false,
  viewportWidth: 1920,
  viewportHeight: 1080,
  defaultCommandTimeout: 20000,
  requestTimeout: 20000,
  numTestsKeptInMemory: 500,
  reporter: 'cypress-multi-reporters',
  reporterOptions: {
    reporterEnabled: 'mochawesome, mocha-junit-reporter',
    mochawesomeReporterOptions: {
      reportDir: 'cypress/mochawesome/results',
      quiet: true,
      overwrite: false,
      html: false,
      json: true
    },
    mochaJunitReporterReporterOptions: {
      mochaFile: 'cypress/junit/results/results-[hash].xml'
    }
  },
  env: {
    SKIP_SLOW_TESTS: 1
  },
  retries: {
    runMode: 4
  },
  hmrUrl: 'ws://127.0.0.1:3000/ws',
  hmrRestartDelay: 5000,
  e2e: {
    // We've imported your old cypress plugins here.
    // You may want to clean this up later by importing these.
    setupNodeEvents(on, config) {
      return require('./cypress/plugins/index.js')(on, config);
    },
    baseUrl: 'http://127.0.0.1:5004',
    supportFile: 'cypress/support/e2e.js'
  }
});
