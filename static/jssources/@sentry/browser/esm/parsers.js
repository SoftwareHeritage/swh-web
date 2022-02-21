import { createStackParser, extractExceptionKeysForMessage, isEvent, normalizeToSize } from '@sentry/utils';
import { chrome, gecko, opera10, opera11, winjs } from './stack-parsers';
/**
 * This function creates an exception from an TraceKitStackTrace
 * @param stacktrace TraceKitStackTrace that will be converted to an exception
 * @hidden
 */
export function exceptionFromError(ex) {
    // Get the frames first since Opera can lose the stack if we touch anything else first
    var frames = parseStackFrames(ex);
    var exception = {
        type: ex && ex.name,
        value: extractMessage(ex),
    };
    if (frames && frames.length) {
        exception.stacktrace = { frames: frames };
    }
    if (exception.type === undefined && exception.value === '') {
        exception.value = 'Unrecoverable error caught';
    }
    return exception;
}
/**
 * @hidden
 */
export function eventFromPlainObject(exception, syntheticException, rejection) {
    var event = {
        exception: {
            values: [
                {
                    type: isEvent(exception) ? exception.constructor.name : rejection ? 'UnhandledRejection' : 'Error',
                    value: "Non-Error " + (rejection ? 'promise rejection' : 'exception') + " captured with keys: " + extractExceptionKeysForMessage(exception),
                },
            ],
        },
        extra: {
            __serialized__: normalizeToSize(exception),
        },
    };
    if (syntheticException) {
        event.stacktrace = {
            frames: parseStackFrames(syntheticException),
        };
    }
    return event;
}
/**
 * @hidden
 */
export function eventFromError(ex) {
    return {
        exception: {
            values: [exceptionFromError(ex)],
        },
    };
}
/** Parses stack frames from an error */
export function parseStackFrames(ex) {
    // Access and store the stacktrace property before doing ANYTHING
    // else to it because Opera is not very good at providing it
    // reliably in other circumstances.
    var stacktrace = ex.stacktrace || ex.stack || '';
    var popSize = getPopSize(ex);
    try {
        // The order of the parsers in important
        return createStackParser(opera10, opera11, chrome, winjs, gecko)(stacktrace, popSize);
    }
    catch (e) {
        // no-empty
    }
    return [];
}
// Based on our own mapping pattern - https://github.com/getsentry/sentry/blob/9f08305e09866c8bd6d0c24f5b0aabdd7dd6c59c/src/sentry/lang/javascript/errormapping.py#L83-L108
var reactMinifiedRegexp = /Minified React error #\d+;/i;
function getPopSize(ex) {
    if (ex) {
        if (typeof ex.framesToPop === 'number') {
            return ex.framesToPop;
        }
        if (reactMinifiedRegexp.test(ex.message)) {
            return 1;
        }
    }
    return 0;
}
/**
 * There are cases where stacktrace.message is an Event object
 * https://github.com/getsentry/sentry-javascript/issues/1949
 * In this specific case we try to extract stacktrace.message.error.message
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function extractMessage(ex) {
    var message = ex && ex.message;
    if (!message) {
        return 'No error message';
    }
    if (message.error && typeof message.error.message === 'string') {
        return message.error.message;
    }
    return message;
}
//# sourceMappingURL=parsers.js.map