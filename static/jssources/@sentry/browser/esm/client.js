import { BaseClient, SDK_VERSION, getEnvelopeEndpointWithUrlEncodedAuth } from '@sentry/core';
import { logger, createClientReportEnvelope, dsnToString, serializeEnvelope } from '@sentry/utils';
import { eventFromException, eventFromMessage } from './eventbuilder.js';
import { WINDOW } from './helpers.js';
import { BREADCRUMB_INTEGRATION_ID } from './integrations/breadcrumbs.js';

/**
 * Configuration options for the Sentry Browser SDK.
 * @see @sentry/types Options for more information.
 */

/**
 * The Sentry Browser SDK Client.
 *
 * @see BrowserOptions for documentation on configuration options.
 * @see SentryClient for usage documentation.
 */
class BrowserClient extends BaseClient {
  /**
   * Creates a new Browser SDK instance.
   *
   * @param options Configuration options for this SDK.
   */
   constructor(options) {
    options._metadata = options._metadata || {};
    options._metadata.sdk = options._metadata.sdk || {
      name: 'sentry.javascript.browser',
      packages: [
        {
          name: 'npm:@sentry/browser',
          version: SDK_VERSION,
        },
      ],
      version: SDK_VERSION,
    };

    super(options);

    if (options.sendClientReports && WINDOW.document) {
      WINDOW.document.addEventListener('visibilitychange', () => {
        if (WINDOW.document.visibilityState === 'hidden') {
          this._flushOutcomes();
        }
      });
    }
  }

  /**
   * @inheritDoc
   */
   eventFromException(exception, hint) {
    return eventFromException(this._options.stackParser, exception, hint, this._options.attachStacktrace);
  }

  /**
   * @inheritDoc
   */
   eventFromMessage(
    message,
    // eslint-disable-next-line deprecation/deprecation
    level = 'info',
    hint,
  ) {
    return eventFromMessage(this._options.stackParser, message, level, hint, this._options.attachStacktrace);
  }

  /**
   * @inheritDoc
   */
   sendEvent(event, hint) {
    // We only want to add the sentry event breadcrumb when the user has the breadcrumb integration installed and
    // activated its `sentry` option.
    // We also do not want to use the `Breadcrumbs` class here directly, because we do not want it to be included in
    // bundles, if it is not used by the SDK.
    // This all sadly is a bit ugly, but we currently don't have a "pre-send" hook on the integrations so we do it this
    // way for now.
    const breadcrumbIntegration = this.getIntegrationById(BREADCRUMB_INTEGRATION_ID) ;
    // We check for definedness of `addSentryBreadcrumb` in case users provided their own integration with id
    // "Breadcrumbs" that does not have this function.
    if (breadcrumbIntegration && breadcrumbIntegration.addSentryBreadcrumb) {
      breadcrumbIntegration.addSentryBreadcrumb(event);
    }

    super.sendEvent(event, hint);
  }

  /**
   * @inheritDoc
   */
   _prepareEvent(event, hint, scope) {
    event.platform = event.platform || 'javascript';
    return super._prepareEvent(event, hint, scope);
  }

  /**
   * Sends client reports as an envelope.
   */
   _flushOutcomes() {
    const outcomes = this._clearOutcomes();

    if (outcomes.length === 0) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.log('No outcomes to send');
      return;
    }

    if (!this._dsn) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.log('No dsn provided, will not send outcomes');
      return;
    }

    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.log('Sending outcomes:', outcomes);

    const url = getEnvelopeEndpointWithUrlEncodedAuth(this._dsn, this._options);
    const envelope = createClientReportEnvelope(outcomes, this._options.tunnel && dsnToString(this._dsn));

    try {
      const isRealNavigator = Object.prototype.toString.call(WINDOW && WINDOW.navigator) === '[object Navigator]';
      const hasSendBeacon = isRealNavigator && typeof WINDOW.navigator.sendBeacon === 'function';
      // Make sure beacon is not used if user configures custom transport options
      if (hasSendBeacon && !this._options.transportOptions) {
        // Prevent illegal invocations - https://xgwang.me/posts/you-may-not-know-beacon/#it-may-throw-error%2C-be-sure-to-catch
        const sendBeacon = WINDOW.navigator.sendBeacon.bind(WINDOW.navigator);
        sendBeacon(url, serializeEnvelope(envelope));
      } else {
        // If beacon is not supported or if they are using the tunnel option
        // use our regular transport to send client reports to Sentry.
        this._sendEnvelope(envelope);
      }
    } catch (e) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.error(e);
    }
  }
}

export { BrowserClient };
//# sourceMappingURL=client.js.map
