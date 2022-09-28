import { addGlobalEventProcessor, getCurrentHub } from '@sentry/hub';
import { arrayify, logger } from '@sentry/utils';

var installedIntegrations = [];

/** Map of integrations assigned to a client */

/**
 * Remove duplicates from the given array, preferring the last instance of any duplicate. Not guaranteed to
 * preseve the order of integrations in the array.
 *
 * @private
 */
function filterDuplicates(integrations) {
  var integrationsByName = {};

  integrations.forEach(currentInstance => {
    const { name } = currentInstance;

    var existingInstance = integrationsByName[name];

    // We want integrations later in the array to overwrite earlier ones of the same type, except that we never want a
    // default instance to overwrite an existing user instance
    if (existingInstance && !existingInstance.isDefaultInstance && currentInstance.isDefaultInstance) {
      return;
    }

    integrationsByName[name] = currentInstance;
  });

  return Object.values(integrationsByName);
}

/** Gets integrations to install */
function getIntegrationsToSetup(options) {
  var defaultIntegrations = options.defaultIntegrations || [];
  var userIntegrations = options.integrations;

  // We flag default instances, so that later we can tell them apart from any user-created instances of the same class
  defaultIntegrations.forEach(integration => {
    integration.isDefaultInstance = true;
  });

  let integrations;

  if (Array.isArray(userIntegrations)) {
    integrations = [...defaultIntegrations, ...userIntegrations];
  } else if (typeof userIntegrations === 'function') {
    integrations = arrayify(userIntegrations(defaultIntegrations));
  } else {
    integrations = defaultIntegrations;
  }

  var finalIntegrations = filterDuplicates(integrations);

  // The `Debug` integration prints copies of the `event` and `hint` which will be passed to `beforeSend`. It therefore
  // has to run after all other integrations, so that the changes of all event processors will be reflected in the
  // printed values. For lack of a more elegant way to guarantee that, we therefore locate it and, assuming it exists,
  // pop it out of its current spot and shove it onto the end of the array.
  var debugIndex = finalIntegrations.findIndex(integration => integration.name === 'Debug');
  if (debugIndex !== -1) {
    const [debugInstance] = finalIntegrations.splice(debugIndex, 1);
    finalIntegrations.push(debugInstance);
  }

  return finalIntegrations;
}

/**
 * Given a list of integration instances this installs them all. When `withDefaults` is set to `true` then all default
 * integrations are added unless they were already provided before.
 * @param integrations array of integration instances
 * @param withDefault should enable default integrations
 */
function setupIntegrations(integrations) {
  var integrationIndex = {};

  integrations.forEach(integration => {
    integrationIndex[integration.name] = integration;

    if (installedIntegrations.indexOf(integration.name) === -1) {
      integration.setupOnce(addGlobalEventProcessor, getCurrentHub);
      installedIntegrations.push(integration.name);
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.log(`Integration installed: ${integration.name}`);
    }
  });

  return integrationIndex;
}

export { getIntegrationsToSetup, installedIntegrations, setupIntegrations };
//# sourceMappingURL=integration.js.map
