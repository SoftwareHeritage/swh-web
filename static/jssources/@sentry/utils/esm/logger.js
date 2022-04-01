import { __read, __spread } from "tslib";
import { isDebugBuild } from './env';
import { getGlobalObject } from './global';
// TODO: Implement different loggers for different environments
var global = getGlobalObject();
/** Prefix for logging strings */
var PREFIX = 'Sentry Logger ';
export var CONSOLE_LEVELS = ['debug', 'info', 'warn', 'error', 'log', 'assert'];
/**
 * Temporarily unwrap `console.log` and friends in order to perform the given callback using the original methods.
 * Restores wrapping after the callback completes.
 *
 * @param callback The function to run against the original `console` messages
 * @returns The results of the callback
 */
export function consoleSandbox(callback) {
    var global = getGlobalObject();
    if (!('console' in global)) {
        return callback();
    }
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    var originalConsole = global.console;
    var wrappedLevels = {};
    // Restore all wrapped console methods
    CONSOLE_LEVELS.forEach(function (level) {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
        if (level in global.console && originalConsole[level].__sentry_original__) {
            wrappedLevels[level] = originalConsole[level];
            originalConsole[level] = originalConsole[level].__sentry_original__;
        }
    });
    // Perform callback manipulations
    var result = callback();
    // Revert restoration to wrapped state
    Object.keys(wrappedLevels).forEach(function (level) {
        originalConsole[level] = wrappedLevels[level];
    });
    return result;
}
/** JSDoc */
var Logger = /** @class */ (function () {
    /** JSDoc */
    function Logger() {
        this._enabled = false;
    }
    /** JSDoc */
    Logger.prototype.disable = function () {
        this._enabled = false;
    };
    /** JSDoc */
    Logger.prototype.enable = function () {
        this._enabled = true;
    };
    /** JSDoc */
    Logger.prototype.log = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            var _a;
            (_a = global.console).log.apply(_a, __spread([PREFIX + "[Log]:"], args));
        });
    };
    /** JSDoc */
    Logger.prototype.warn = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            var _a;
            (_a = global.console).warn.apply(_a, __spread([PREFIX + "[Warn]:"], args));
        });
    };
    /** JSDoc */
    Logger.prototype.error = function () {
        var args = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            args[_i] = arguments[_i];
        }
        if (!this._enabled) {
            return;
        }
        consoleSandbox(function () {
            var _a;
            (_a = global.console).error.apply(_a, __spread([PREFIX + "[Error]:"], args));
        });
    };
    return Logger;
}());
var sentryGlobal = global.__SENTRY__ || {};
var logger = sentryGlobal.logger || new Logger();
if (isDebugBuild()) {
    // Ensure we only have a single logger instance, even if multiple versions of @sentry/utils are being used
    sentryGlobal.logger = logger;
    global.__SENTRY__ = sentryGlobal;
}
export { logger };
//# sourceMappingURL=logger.js.map