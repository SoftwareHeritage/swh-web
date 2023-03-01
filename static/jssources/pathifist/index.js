'use strict';

exports.resolve = function resolve() {
  return Array.prototype.slice
    .apply(arguments)
    .reduce(function(acc, curr) {
      if (curr.charAt(0) === '/') acc = [''];
      return curr.split('/').reduce(function(acc, curr) {
        if (curr === '') return acc;
        if (curr === '.' && acc.length) return acc;
        if (curr === '..' && acc.length) {
          if (acc.length === 1 && !acc[0]) return acc;
          if (acc[acc.length - 1] !== '..') {
            return acc.slice(0, acc.length - 1);
          }
        }
        return acc.concat(curr);
      }, acc);
    }, [])
    .join('/');
};

exports.join = function join() {
  return Array.prototype.join.call(arguments, '/').replace(/\/+/g, '/');
};

exports.dedupeSlashes = function dedupeSlashes(path) {
  return path.replace(/\/+/g, '/');
};

exports.trimSlashes = function trimSlashes(path) {
  return path.replace(/^\/*(.*?)\/*$/, '$1');
};

exports.ensureSlashes = function ensureSlashes(path) {
  return path.replace(/^\/*(.*?)\/*$/, '/$1/');
};

exports.trimLeadingSlash = function trimLeadingSlash(path) {
  return path.replace(/^\/+/, '');
};

exports.trimTrailingSlash = function trimTrailingSlash(path) {
  return path.replace(/\/+$/, '');
};

exports.ensureLeadingSlash = function ensureLeadingSlash(path) {
  return path.replace(/^\/*/, '/');
};

exports.ensureTrailingSlash = function ensureTrailingSlash(path) {
  return path.replace(/\/*$/, '/');
};
