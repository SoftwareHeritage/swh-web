import { __assign } from "tslib";
import { Severity } from '@sentry/types';
import { addExceptionMechanism, addExceptionTypeValue, isDOMError, isDOMException, isError, isErrorEvent, isEvent, isPlainObject, resolvedSyncPromise, } from '@sentry/utils';
import { eventFromError, eventFromPlainObject, parseStackFrames } from './parsers';
/**
 * Creates an {@link Event} from all inputs to `captureException` and non-primitive inputs to `captureMessage`.
 * @hidden
 */
export function eventFromException(options, exception, hint) {
    var syntheticException = (hint && hint.syntheticException) || undefined;
    var event = eventFromUnknownInput(exception, syntheticException, {
        attachStacktrace: options.attachStacktrace,
    });
    addExceptionMechanism(event); // defaults to { type: 'generic', handled: true }
    event.level = Severity.Error;
    if (hint && hint.event_id) {
        event.event_id = hint.event_id;
    }
    return resolvedSyncPromise(event);
}
/**
 * Builds and Event from a Message
 * @hidden
 */
export function eventFromMessage(options, message, level, hint) {
    if (level === void 0) { level = Severity.Info; }
    var syntheticException = (hint && hint.syntheticException) || undefined;
    var event = eventFromString(message, syntheticException, {
        attachStacktrace: options.attachStacktrace,
    });
    event.level = level;
    if (hint && hint.event_id) {
        event.event_id = hint.event_id;
    }
    return resolvedSyncPromise(event);
}
/**
 * @hidden
 */
export function eventFromUnknownInput(exception, syntheticException, options) {
    if (options === void 0) { options = {}; }
    var event;
    if (isErrorEvent(exception) && exception.error) {
        // If it is an ErrorEvent with `error` property, extract it to get actual Error
        var errorEvent = exception;
        return eventFromError(errorEvent.error);
    }
    // If it is a `DOMError` (which is a legacy API, but still supported in some browsers) then we just extract the name
    // and message, as it doesn't provide anything else. According to the spec, all `DOMExceptions` should also be
    // `Error`s, but that's not the case in IE11, so in that case we treat it the same as we do a `DOMError`.
    //
    // https://developer.mozilla.org/en-US/docs/Web/API/DOMError
    // https://developer.mozilla.org/en-US/docs/Web/API/DOMException
    // https://webidl.spec.whatwg.org/#es-DOMException-specialness
    if (isDOMError(exception) || isDOMException(exception)) {
        var domException = exception;
        if ('stack' in exception) {
            event = eventFromError(exception);
        }
        else {
            var name_1 = domException.name || (isDOMError(domException) ? 'DOMError' : 'DOMException');
            var message = domException.message ? name_1 + ": " + domException.message : name_1;
            event = eventFromString(message, syntheticException, options);
            addExceptionTypeValue(event, message);
        }
        if ('code' in domException) {
            event.tags = __assign(__assign({}, event.tags), { 'DOMException.code': "" + domException.code });
        }
        return event;
    }
    if (isError(exception)) {
        // we have a real Error object, do nothing
        return eventFromError(exception);
    }
    if (isPlainObject(exception) || isEvent(exception)) {
        // If it's a plain object or an instance of `Event` (the built-in JS kind, not this SDK's `Event` type), serialize
        // it manually. This will allow us to group events based on top-level keys which is much better than creating a new
        // group on any key/value change.
        var objectException = exception;
        event = eventFromPlainObject(objectException, syntheticException, options.isRejection);
        addExceptionMechanism(event, {
            synthetic: true,
        });
        return event;
    }
    // If none of previous checks were valid, then it means that it's not:
    // - an instance of DOMError
    // - an instance of DOMException
    // - an instance of Event
    // - an instance of Error
    // - a valid ErrorEvent (one with an error property)
    // - a plain Object
    //
    // So bail out and capture it as a simple message:
    event = eventFromString(exception, syntheticException, options);
    addExceptionTypeValue(event, "" + exception, undefined);
    addExceptionMechanism(event, {
        synthetic: true,
    });
    return event;
}
/**
 * @hidden
 */
export function eventFromString(input, syntheticException, options) {
    if (options === void 0) { options = {}; }
    var event = {
        message: input,
    };
    if (options.attachStacktrace && syntheticException) {
        event.stacktrace = {
            frames: parseStackFrames(syntheticException),
        };
    }
    return event;
}
//# sourceMappingURL=eventbuilder.js.map