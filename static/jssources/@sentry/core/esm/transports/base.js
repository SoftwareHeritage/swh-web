import { forEachEnvelopeItem, envelopeItemTypeToDataCategory, isRateLimited, resolvedSyncPromise, createEnvelope, serializeEnvelope, logger, updateRateLimits, SentryError, makePromiseBuffer } from '@sentry/utils';

const DEFAULT_TRANSPORT_BUFFER_SIZE = 30;

/**
 * Creates an instance of a Sentry `Transport`
 *
 * @param options
 * @param makeRequest
 */
function createTransport(
  options,
  makeRequest,
  buffer = makePromiseBuffer(options.bufferSize || DEFAULT_TRANSPORT_BUFFER_SIZE),
) {
  let rateLimits = {};

  const flush = (timeout) => buffer.drain(timeout);

  function send(envelope) {
    const filteredEnvelopeItems = [];

    // Drop rate limited items from envelope
    forEachEnvelopeItem(envelope, (item, type) => {
      const envelopeItemDataCategory = envelopeItemTypeToDataCategory(type);
      if (isRateLimited(rateLimits, envelopeItemDataCategory)) {
        options.recordDroppedEvent('ratelimit_backoff', envelopeItemDataCategory);
      } else {
        filteredEnvelopeItems.push(item);
      }
    });

    // Skip sending if envelope is empty after filtering out rate limited events
    if (filteredEnvelopeItems.length === 0) {
      return resolvedSyncPromise();
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filteredEnvelope = createEnvelope(envelope[0], filteredEnvelopeItems );

    // Creates client report for each item in an envelope
    const recordEnvelopeLoss = (reason) => {
      forEachEnvelopeItem(filteredEnvelope, (_, type) => {
        options.recordDroppedEvent(reason, envelopeItemTypeToDataCategory(type));
      });
    };

    const requestTask = () =>
      makeRequest({ body: serializeEnvelope(filteredEnvelope, options.textEncoder) }).then(
        response => {
          // We don't want to throw on NOK responses, but we want to at least log them
          if (response.statusCode !== undefined && (response.statusCode < 200 || response.statusCode >= 300)) {
            (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.warn(`Sentry responded with status code ${response.statusCode} to sent event.`);
          }

          rateLimits = updateRateLimits(rateLimits, response);
        },
        error => {
          (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.error('Failed while sending event:', error);
          recordEnvelopeLoss('network_error');
        },
      );

    return buffer.add(requestTask).then(
      result => result,
      error => {
        if (error instanceof SentryError) {
          (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) && logger.error('Skipped sending event because buffer is full.');
          recordEnvelopeLoss('queue_overflow');
          return resolvedSyncPromise();
        } else {
          throw error;
        }
      },
    );
  }

  return {
    send,
    flush,
  };
}

export { DEFAULT_TRANSPORT_BUFFER_SIZE, createTransport };
//# sourceMappingURL=base.js.map