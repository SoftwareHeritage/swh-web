import { isString } from './is.js';
import { logger } from './logger.js';

var BAGGAGE_HEADER_NAME = 'baggage';

var SENTRY_BAGGAGE_KEY_PREFIX = 'sentry-';

var SENTRY_BAGGAGE_KEY_PREFIX_REGEX = /^sentry-/;

/**
 * Max length of a serialized baggage string
 *
 * https://www.w3.org/TR/baggage/#limits
 */
var MAX_BAGGAGE_STRING_LENGTH = 8192;

/** Create an instance of Baggage */
function createBaggage(initItems, baggageString = '', mutable = true) {
  return [{ ...initItems }, baggageString, mutable];
}

/** Get a value from baggage */
function getBaggageValue(baggage, key) {
  return baggage[0][key];
}

/** Add a value to baggage */
function setBaggageValue(baggage, key, value) {
  if (isBaggageMutable(baggage)) {
    baggage[0][key] = value;
  }
}

/** Check if the Sentry part of the passed baggage (i.e. the first element in the tuple) is empty */
function isSentryBaggageEmpty(baggage) {
  return Object.keys(baggage[0]).length === 0;
}

/** Returns Sentry specific baggage values */
function getSentryBaggageItems(baggage) {
  return baggage[0];
}

/**
 * Returns 3rd party baggage string of @param baggage
 * @param baggage
 */
function getThirdPartyBaggage(baggage) {
  return baggage[1];
}

/**
 * Checks if baggage is mutable
 * @param baggage
 * @returns true if baggage is mutable, else false
 */
function isBaggageMutable(baggage) {
  return baggage[2];
}

/**
 * Sets the passed baggage immutable
 * @param baggage
 */
function setBaggageImmutable(baggage) {
  baggage[2] = false;
}

/** Serialize a baggage object */
function serializeBaggage(baggage) {
  return Object.keys(baggage[0]).reduce((prev, key) => {
    var val = baggage[0][key] ;
    var baggageEntry = `${SENTRY_BAGGAGE_KEY_PREFIX}${encodeURIComponent(key)}=${encodeURIComponent(val)}`;
    var newVal = prev === '' ? baggageEntry : `${prev},${baggageEntry}`;
    if (newVal.length > MAX_BAGGAGE_STRING_LENGTH) {
      (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
        logger.warn(`Not adding key: ${key} with val: ${val} to baggage due to exceeding baggage size limits.`);
      return prev;
    } else {
      return newVal;
    }
  }, baggage[1]);
}

/**
 * Parse a baggage header from a string or a string array and return a Baggage object
 *
 * If @param includeThirdPartyEntries is set to true, third party baggage entries are added to the Baggage object
 * (This is necessary for merging potentially pre-existing baggage headers in outgoing requests with
 * our `sentry-` values)
 */
function parseBaggageHeader(
  inputBaggageValue,
  includeThirdPartyEntries = false,
) {
  // Adding this check here because we got reports of this function failing due to the input value
  // not being a string. This debug log might help us determine what's going on here.
  if ((!Array.isArray(inputBaggageValue) && !isString(inputBaggageValue)) || typeof inputBaggageValue === 'number') {
    (typeof __SENTRY_DEBUG__ === 'undefined' || __SENTRY_DEBUG__) &&
      logger.warn(
        '[parseBaggageHeader] Received input value of incompatible type: ',
        typeof inputBaggageValue,
        inputBaggageValue,
      );

    // Gonna early-return an empty baggage object so that we don't fail later on
    return createBaggage({}, '');
  }

  var baggageEntries = (isString(inputBaggageValue) ? inputBaggageValue : inputBaggageValue.join(','))
    .split(',')
    .map(entry => entry.trim())
    .filter(entry => entry !== '' && (includeThirdPartyEntries || SENTRY_BAGGAGE_KEY_PREFIX_REGEX.test(entry)));

  return baggageEntries.reduce(
    ([baggageObj, baggageString], curr) => {
      const [key, val] = curr.split('=');
      if (SENTRY_BAGGAGE_KEY_PREFIX_REGEX.test(key)) {
        var baggageKey = decodeURIComponent(key.split('-')[1]);
        return [
          {
            ...baggageObj,
            [baggageKey]: decodeURIComponent(val),
          },
          baggageString,
          true,
        ];
      } else {
        return [baggageObj, baggageString === '' ? curr : `${baggageString},${curr}`, true];
      }
    },
    [{}, '', true],
  );
}

/**
 * Merges the baggage header we saved from the incoming request (or meta tag) with
 * a possibly created or modified baggage header by a third party that's been added
 * to the outgoing request header.
 *
 * In case @param headerBaggageString exists, we can safely add the the 3rd party part of @param headerBaggage
 * with our @param incomingBaggage. This is possible because if we modified anything beforehand,
 * it would only affect parts of the sentry baggage (@see Baggage interface).
 *
 * @param incomingBaggage the baggage header of the incoming request that might contain sentry entries
 * @param thirdPartyBaggageHeader possibly existing baggage header string or string[] added from a third
 *        party to the request headers
 *
 * @return a merged and serialized baggage string to be propagated with the outgoing request
 */
function mergeAndSerializeBaggage(incomingBaggage, thirdPartyBaggageHeader) {
  if (!incomingBaggage && !thirdPartyBaggageHeader) {
    return '';
  }

  var headerBaggage = (thirdPartyBaggageHeader && parseBaggageHeader(thirdPartyBaggageHeader, true)) || undefined;
  var thirdPartyHeaderBaggage = headerBaggage && getThirdPartyBaggage(headerBaggage);

  var finalBaggage = createBaggage((incomingBaggage && incomingBaggage[0]) || {}, thirdPartyHeaderBaggage || '');
  return serializeBaggage(finalBaggage);
}

/**
 * Helper function that takes a raw baggage string (if available) and the processed sentry-trace header
 * data (if available), parses the baggage string and creates a Baggage object
 * If there is no baggage string, it will create an empty Baggage object.
 * In a second step, this functions determines if the created Baggage object should be set immutable
 * to prevent mutation of the Sentry data.
 *
 * Extracted this logic to a function because it's duplicated in a lot of places.
 *
 * @param rawBaggageValue
 * @param sentryTraceHeader
 */
function parseBaggageSetMutability(
  rawBaggageValue,
  sentryTraceHeader,
) {
  var baggage = parseBaggageHeader(rawBaggageValue || '');

  // Because we are always creating a Baggage object by calling `parseBaggageHeader` above
  // (either a filled one or an empty one, even if we didn't get a `baggage` header),
  // we only need to check if we have a sentry-trace header or not. As soon as we have it,
  // we set baggage immutable. In case we don't get a sentry-trace header, we can assume that
  // this SDK is the head of the trace and thus we still permit mutation at this time.
  // There is one exception though, which is that we get a baggage-header with `sentry-`
  // items but NO sentry-trace header. In this case we also set the baggage immutable for now
  // but if smoething like this would ever happen, we should revisit this and determine
  // what this would actually mean for the trace (i.e. is this SDK the head?, what happened
  // before that we don't have a sentry-trace header?, etc)
  (sentryTraceHeader || !isSentryBaggageEmpty(baggage)) && setBaggageImmutable(baggage);

  return baggage;
}

export { BAGGAGE_HEADER_NAME, MAX_BAGGAGE_STRING_LENGTH, SENTRY_BAGGAGE_KEY_PREFIX, SENTRY_BAGGAGE_KEY_PREFIX_REGEX, createBaggage, getBaggageValue, getSentryBaggageItems, getThirdPartyBaggage, isBaggageMutable, isSentryBaggageEmpty, mergeAndSerializeBaggage, parseBaggageHeader, parseBaggageSetMutability, serializeBaggage, setBaggageImmutable, setBaggageValue };
//# sourceMappingURL=baggage.js.map
