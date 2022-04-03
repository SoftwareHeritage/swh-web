// Copyright (C) 2021  The Software Heritage developers
// See the AUTHORS file at the top-level directory of this distribution
// License: GNU General Public License version 3, or any later version
// See top-level LICENSE file for more information

// Field tokens
const visitTypeField = 'visit_type';
const sortByField = 'sort_by';
const limitField = 'limit';

// Field categories
const patternFields = ['origin', 'metadata'];
const booleanFields = ['visited'];
const numericFields = ['visits'];
const boundedListFields = [visitTypeField];
const listFields = ['language', 'license', 'keyword'];
const dateFields = [
  'last_visit',
  'last_eventful_visit',
  'last_revision',
  'last_release',
  'created',
  'modified',
  'published'
];

const fields = [].concat(
  patternFields,
  booleanFields,
  numericFields,
  boundedListFields,
  listFields,
  dateFields
);

// Operators
const equalOp = ['='];
const containOp = [':'];
const rangeOp = ['<', '<=', '=', '!=', '>=', '>'];
const choiceOp = ['in', 'not in'];

// Values
const sortByOptions = [
  'visits',
  'last_visit',
  'last_eventful_visit',
  'last_revision',
  'last_release',
  'created',
  'modified',
  'published'
];

const visitTypeOptions = [
  'any',
  'bzr',
  'cran',
  'cvs',
  'deb',
  'deposit',
  'ftp',
  'hg',
  'git',
  'nixguix',
  'npm',
  'opam',
  'pypi',
  'svn',
  'tar'
];

// Extra tokens
const OR = 'or';
const AND = 'and';

const TRUE = 'true';
const FALSE = 'false';

module.exports = {
  // Field tokens
  visitTypeField,
  sortByField,
  limitField,

  // Field categories
  patternFields,
  booleanFields,
  numericFields,
  boundedListFields,
  listFields,
  dateFields,
  fields,

  // Operators
  equalOp,
  containOp,
  rangeOp,
  choiceOp,

  // Values
  sortByOptions,
  visitTypeOptions,

  // Extra tokens
  OR,
  AND,
  TRUE,
  FALSE
};
