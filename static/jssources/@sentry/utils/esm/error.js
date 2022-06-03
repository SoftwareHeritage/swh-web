/** An error emitted by Sentry SDKs and related utilities. */
class SentryError extends Error {
  /** Display name of this error instance. */
  

   constructor( message) {
    super(message);this.message = message;;

    this.name = new.target.prototype.constructor.name;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export { SentryError };
//# sourceMappingURL=error.js.map
