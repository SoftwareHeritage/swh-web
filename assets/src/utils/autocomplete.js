import 'utils/autocomplete.css';

export class Autocomplete {
  constructor(params) {
    const {inputBox, suggestions} = params;
    this.inputBox = inputBox;
    this.suggestions = suggestions;
    this.currentIndex = -1;

    this.autocompleteList = document.createElement('div');
    this.autocompleteList.setAttribute('class', 'autocomplete-items');
    this.inputBox.parentNode.appendChild(this.autocompleteList);

    this.initListeners();
  }

  initListeners() {
    this.inputBox.addEventListener('focus', this.updateLists.bind(this));
    this.inputBox.addEventListener('input', this.updateLists.bind(this));

    this.inputBox.addEventListener('keydown', (e) => {
      if (e.keyCode === 40) { // down
        e.preventDefault();
        this.currentIndex++;
        this.addActive();
      } else if (e.keyCode === 38) { // up
        e.preventDefault();
        this.currentIndex--;
        this.addActive();
      } else if (e.keyCode === 13 || e.keyCode === 9) { // enter or tab
        e.preventDefault();
        if (this.currentIndex > -1) {
          // Simulate a click on the "active" item:
          if (this.autocompleteList) this.autocompleteList.children[this.currentIndex].click();
        }
      } else if (e.keyCode === 27) { // escape
        e.preventDefault();
        this.removeAllItems(e.target);
      }
    });

    document.addEventListener('click', (e) => { this.removeAllItems(e.target); });
  }

  updateLists() {
    const inputValue = this.inputBox.value;

    const tokens = inputValue.split();
    const lastToken = tokens[tokens.length - 1];
    const lastChar = lastToken[lastToken.length - 1];

    /* close any already open lists of autocompleted values */
    this.removeAllItems();

    this.currentIndex = -1;

    const suggestions = this.suggestions.filter(s => (s.indexOf(lastToken) >= 0 || lastChar === ' '));

    suggestions.slice(0, 10).forEach(suggestion => {
      const itemDiv = document.createElement('div');
      if (lastChar === ' ') {
        itemDiv.innerHTML = suggestion;
      } else {
        const indexOfLastToken = suggestion.indexOf(lastToken);

        itemDiv.innerHTML = suggestion.substr(0, indexOfLastToken) +
          '<strong>' +
          suggestion.substr(indexOfLastToken, lastToken.length) +
          '</strong>' +
          suggestion.substr(
            indexOfLastToken + lastToken.length, suggestion.length - (lastToken.length - 2)
          );

      }

      itemDiv.setAttribute('data-value', suggestion);
      itemDiv.setAttribute('data-editable-suggestion', 'false');
      itemDiv.setAttribute('title', 'Include repos with the provided term in their url (origin)');

      const suggestionClick = (e) => {
        const toInsert = e.target.getAttribute('data-value');
        const isEditableSuggestion = e.target.getAttribute('data-editable-suggestion');

        if (isEditableSuggestion === 'true') return;

        const oldValue = this.inputBox.value;
        const tokens = oldValue.split();
        const lastToken = tokens[tokens.length - 1];
        const lastChar = lastToken[lastToken.length - 1];

        let newValue = '';

        if (lastChar === ' ' || oldValue === '') {
          newValue = oldValue + toInsert;
        } else {
          // const position = this.inputBox.selectionStart;
          const queryWithoutLastToken = tokens.slice(0, tokens.length - 2).join(' ');
          newValue = queryWithoutLastToken + ((queryWithoutLastToken !== '') ? ' ' : '') + toInsert;
        }

        this.inputBox.value = newValue;
        this.inputBox.blur();
        this.inputBox.focus();
        // this.inputBox.dispatchEvent(new Event('input'))
      };

      itemDiv.addEventListener('click', suggestionClick.bind(this));

      this.autocompleteList.appendChild(itemDiv);
    });

    if (suggestions?.length) {
      // Select first element on each update
      this.currentIndex = 0;
      this.addActive();
    }
  }

  addActive() {
    //  a function to classify an item as "active":
    if (!this.autocompleteList) return false;
    //  start by removing the "active" class on all items:
    const n = this.autocompleteList.childElementCount;
    this.removeActive();
    if (this.currentIndex >= n) this.currentIndex = 0;
    if (this.currentIndex < 0) this.currentIndex = (n - 1);
    // add class "autocomplete-active":
    this.autocompleteList.children[this.currentIndex].classList.add('autocomplete-active');
  }

  removeActive() {
    /* a function to remove the "active" class from all autocomplete items */
    Array.from(this.autocompleteList.children).forEach(autocompleteItem => {
      autocompleteItem.classList.remove('autocomplete-active');
    });
  }

  removeAllItems(element) {
    /*
        close all autocomplete lists in the document,
        except the one passed as an argument
        */
    if (element !== this.inputBox && this.autocompleteList) {
      this.autocompleteList.innerHTML = '';
    }
  }

}
