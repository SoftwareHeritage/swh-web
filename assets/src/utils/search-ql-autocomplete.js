import '../../../node_modules/web-tree-sitter/tree-sitter.wasm';
import Parser from 'web-tree-sitter';
import {Autocomplete} from 'utils/autocomplete.js';
import {
  fields, limitField, sortByField, // fields
  sortByOptions, visitTypeOptions, // options
  equalOp, rangeOp, choiceOp, // operators
  AND, OR, TRUE, FALSE // special tokens
} from './tokens.js';

const filterNames = fields.concat(sortByField, limitField);

const languageSyntax = [
  {
    category: 'patternFilter',
    field: 'patternField',
    operator: 'equalOp',
    value: 'patternVal',
    suggestion: ['string', '"string"']
  },
  {
    category: 'booleanFilter',
    field: 'booleanField',
    operator: 'equalOp',
    value: 'booleanVal',
    suggestion: [TRUE, FALSE]
  },
  {
    category: 'numericFilter',
    field: 'numericField',
    operator: 'rangeOp',
    value: 'numberVal',
    suggestion: ['15']
  },
  {
    category: 'boundedListFilter',
    field: 'visitTypeField',
    operator: 'equalOp',
    value: 'visitTypeVal',
    options: visitTypeOptions,
    suggestion: ['[']
  },
  {
    category: 'unboundedListFilter',
    field: 'listField',
    operator: 'choiceOp',
    value: 'listVal',
    options: ['string', '"string"'],
    suggestion: ['[']
  },
  {
    category: 'dateFilter',
    field: 'dateField',
    operator: 'rangeOp',
    value: 'dateVal',
    suggestion: ['2000-01-01', '2000-01-01T00:00Z']
  },
  {
    category: 'sortBy',
    field: 'sortByField',
    operator: 'equalOp',
    value: 'sortByVal',
    options: sortByOptions,
    suggestion: ['[']
  },
  {
    category: 'limit',
    field: 'limit',
    operator: 'equalOp',
    value: 'number',
    suggestion: ['50']
  }
];

const filterOperators = {equalOp, choiceOp, rangeOp};

const findMissingNode = (node) => {
  if (node.isMissing()) {
    return node;
  }
  if (node.children.length > 0) {
    for (let i = 0; i < node.children.length; i++) {
      const missingNode = findMissingNode(node.children[i]);
      if (missingNode !== null) { return missingNode; }
    }
  }

  return null;
};

const isWrapperNode = (child, parent) => {
  if (!child || !parent) return false;
  if (parent.namedChildren.length === 1 && parent.type !== 'ERROR') return true;
  return (
    (child.startPosition.column === parent.startPosition.column) &&
    (child.endPosition.column === parent.endPosition.column)
  );
};

const isCategoryNode = (node) => {
  if (!node || node === null) return false;
  if (node.type === 'ERROR' || languageSyntax.filter(f => f.category === node.type).length > 0) { return true; }

  return false;
};

const suggestNextNode = (tree, inputBox) => {
  const cursor = inputBox.selectionStart - 1;
  const query = inputBox.value;

  let lastTokenIndex = cursor;
  // let distFromLastToken = 0;
  while (query[lastTokenIndex] === ' ') {
    lastTokenIndex--;
    // distFromLastToken++;
  }

  // if(query === "visit_type = []") debugger;

  const lastTokenPosition = {row: 0, column: lastTokenIndex};
  const lastTokenNode = tree.rootNode.descendantForPosition(lastTokenPosition, lastTokenPosition);

  const missingNode = findMissingNode(tree.rootNode);

  // Find last token node wrapper
  let lastTokenNodeWrapper = lastTokenNode;
  while (isWrapperNode(lastTokenNodeWrapper, lastTokenNodeWrapper.parent)) {
    lastTokenNodeWrapper = lastTokenNodeWrapper.parent;
  }

  // Find last token node wrapper sibling
  const lastTokenNodeWrapperSibling = lastTokenNodeWrapper.previousSibling;

  // Find current filter category
  let currentFilterCategory = lastTokenNode;
  while (!isCategoryNode(currentFilterCategory)) {
    currentFilterCategory = currentFilterCategory.parent;
  }

  console.log(lastTokenNode);
  console.log(`LAST NODE: ${lastTokenNode.type}`);
  console.log(`LAST NODE ANCESTOR: ${lastTokenNodeWrapper.type}`);
  console.log(`LAST NODE ANCESTOR SIBLING: ${lastTokenNodeWrapperSibling?.type}`);
  console.log(`LAST CATEGORY: ${currentFilterCategory.type}`);

  // Suggest options for array valued filters
  if ((lastTokenNode.type === ',' && lastTokenNodeWrapper.type.indexOf('Val') > 0) ||
    (lastTokenNode.type === '[' && currentFilterCategory)
  ) {
    const filter = languageSyntax.filter(f => f.category === currentFilterCategory.type)[0];
    console.log(filter.options);
    return filter.options ?? [];
  }
  if (
    (!tree.rootNode.hasError() && (lastTokenNodeWrapper.type.indexOf('Val') > 0)) ||
    (lastTokenNode.type === ')' || lastTokenNode.type === ']')
  ) {
    // Suggest AND/OR
    return [AND, OR];
  }
  if (missingNode && missingNode !== null) {
    // Suggest missing nodes (Automatically suggested by Tree-sitter)
    if (missingNode.type === ')') {
      return [AND, OR, ')'];
    } else if (missingNode.type === ']') {
      return [',', ']'];
    }
  }

  if (lastTokenNode.type === 'ERROR' ||
    (lastTokenNode.type === '(') ||
    ((lastTokenNode.type === AND || lastTokenNode.type === OR))
  ) {
    // Suggest field names
    return filterNames.concat('(');
  } else if (languageSyntax.map(f => f.field).includes(lastTokenNode.type)) {
    // Suggest operators
    const filter = languageSyntax.filter(f => f.field === lastTokenNode.type)[0];
    return filterOperators[filter.operator];
  } else if (lastTokenNode.type in filterOperators) {
    // Suggest values
    const filter = languageSyntax.filter(f => (
      f.field === lastTokenNodeWrapperSibling.type
    ))[0];
    return filter.suggestion;
  }

  return [];
};

export const initAutocomplete = (inputBox, validQueryCallback) => {
  Parser.init().then(async() => {
    const parser = new Parser();

    const swhSearchQL = await Parser.Language.load(`${window.location.origin}/static/swh_ql.wasm`);
    parser.setLanguage(swhSearchQL);

    const autocomplete = new Autocomplete(
      {inputBox, suggestions: ['('].concat(filterNames)}
    );

    const getSuggestions = (e) => {
      // if (e.keycode !== 32) // space
      // return;
      const tree = parser.parse(inputBox.value);

      if (tree.rootNode.hasError()) {
        validQueryCallback(false);
        // inputBox.classList.add('invalid');
      } else {
        validQueryCallback(true);
        // inputBox.classList.remove('invalid');
      }

      console.log(`input(${inputBox.value})  => ${tree.rootNode.toString()}`);

      const suggestions = suggestNextNode(tree, inputBox);
      // if (suggestions)
      autocomplete.suggestions = suggestions; // .map(item => `${item} `);
    };

    inputBox.addEventListener('keydown', getSuggestions.bind(this));
  });
};
