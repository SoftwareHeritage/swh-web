/**
 * Copyright (C) 2023-205  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

const filesToCheck = [
  {name: 'robots.txt', path: '/robots.txt', should_contain: 'Disallow'},
  {name: 'security.txt', path: '/security.txt', should_contain: 'Expires'}
];

describe('Static content', function() {

  filesToCheck.forEach(file => {
    it(`should access '${file.name}' and find '${file.should_contain} in it'`, function() {
      cy.visit(file.path);
      cy.contains(file.should_contain);
    });

  });
});
