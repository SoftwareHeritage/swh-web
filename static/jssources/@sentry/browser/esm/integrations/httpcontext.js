import { addGlobalEventProcessor, getCurrentHub } from '@sentry/core';
import { getGlobalObject } from '@sentry/utils';

var global = getGlobalObject();

/** HttpContext integration collects information about HTTP request headers */
class HttpContext  {constructor() { HttpContext.prototype.__init.call(this); }
  /**
   * @inheritDoc
   */
   static __initStatic() {this.id = 'HttpContext';}

  /**
   * @inheritDoc
   */
   __init() {this.name = HttpContext.id;}

  /**
   * @inheritDoc
   */
   setupOnce() {
    addGlobalEventProcessor((event) => {
      if (getCurrentHub().getIntegration(HttpContext)) {
        // if none of the information we want exists, don't bother
        if (!global.navigator && !global.location && !global.document) {
          return event;
        }

        // grab as much info as exists and add it to the event
        var url = (event.request && event.request.url) || (global.location && global.location.href);
        const { referrer } = global.document || {};
        const { userAgent } = global.navigator || {};

        var headers = {
          ...(event.request && event.request.headers),
          ...(referrer && { Referer: referrer }),
          ...(userAgent && { 'User-Agent': userAgent }),
        };
        var request = { ...(url && { url }), headers };

        return { ...event, request };
      }
      return event;
    });
  }
} HttpContext.__initStatic();

export { HttpContext };
//# sourceMappingURL=httpcontext.js.map
