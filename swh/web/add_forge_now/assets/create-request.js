/**
 * Copyright (C) 2022-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

import {
  csrfPost, errorMessageFromResponse, genLink, getHumanReadableDate,
  handleFetchError, validateUrl
} from 'utils/functions';
import userRequestsFilterCheckboxFn from 'utils/requests-filter-checkbox.ejs';
import {dataTableCommonConfig} from 'utils/constants';

let requestBrowseTable;

const addForgeCheckboxId = 'swh-add-forge-user-filter';
const userRequestsFilterCheckbox = userRequestsFilterCheckboxFn({
  'inputId': addForgeCheckboxId,
  'checked': false
});

export function onCreateRequestPageLoad() {
  $(document).ready(() => {
    $('#requestCreateForm').submit(async function(event) {
      event.preventDefault();
      try {
        const response = await csrfPost($(this).attr('action'),
                                        {'Content-Type': 'application/x-www-form-urlencoded'},
                                        $(this).serialize());
        handleFetchError(response);
        $('#userMessageDetail').empty();
        $('#userMessage').text('Your request has been submitted');
        $('#userMessage').removeClass('text-bg-danger');
        $('#userMessage').addClass('text-bg-success');
        requestBrowseTable.draw(); // redraw the table to update the list
      } catch (errorResponse) {
        $('#userMessageDetail').empty();

        let errorMessage;
        const errorData = await errorResponse.json();
        // if (errorResponse.content_type === 'text/plain') { // does not work?
        if (errorResponse.status === 409) {
          errorMessage = errorData;
        } else { // assuming json response
          // const exception = errorData['exception'];
          errorMessage = errorMessageFromResponse(
            errorData, 'An unknown error occurred during the request creation');
        }
        $('#userMessage').text(errorMessage);
        $('#userMessage').removeClass('text-bg-success');
        $('#userMessage').addClass('text-bg-danger');
      }
    });

    populateRequestBrowseList(); // Load existing requests
  });
}

export function populateRequestBrowseList() {
  requestBrowseTable = $('#add-forge-request-browse')
    .on('error.dt', (e, settings, techNote, message) => {
      $('#add-forge-browse-request-error').text(message);
    })
    .DataTable({
      ...dataTableCommonConfig,
      retrieve: true,
      searching: true,
      // Layout configuration, see [1] for more details
      // [1] https://datatables.net/reference/option/dom
      dom: '<"row mb-2"<"col-sm-3"l><"col-sm-6 text-start user-requests-filter"><"col-sm-3"f>>' +
           '<"row"<"col-sm-12"tr>>' +
           '<"row mt-2"<"col-sm-5"i><"col-sm-7"p>>',
      ajax: {
        'url': Urls.add_forge_request_list_datatables(),
        data: (d) => {
          const checked = $(`#${addForgeCheckboxId}`).prop('checked');
          // If this function is called while the page is loading, 'checked' is
          // undefined. As the checkbox defaults to being checked, coerce this to true.
          if (swh.webapp.isUserLoggedIn() && (checked === undefined || checked)) {
            d.user_requests_only = '1';
          }
        }
      },
      fnInitComplete: function() {
        if (swh.webapp.isUserLoggedIn()) {
          $('div.user-requests-filter').html(userRequestsFilterCheckbox);
          $(`#${addForgeCheckboxId}`).on('change', () => {
            requestBrowseTable.draw();
          });
          requestBrowseTable.draw();
        }
      },
      columns: [
        {
          data: 'submission_date',
          name: 'submission_date',
          render: getHumanReadableDate
        },
        {
          data: 'forge_type',
          name: 'forge_type',
          render: $.fn.dataTable.render.text()
        },
        {
          data: 'forge_url',
          name: 'forge_url',
          render: (data, type, row) => {
            const sanitizedURL = $.fn.dataTable.render.text().display(data);
            return genLink(sanitizedURL, type, true);
          }
        },
        {
          data: 'status',
          name: 'status',
          render: function(data, type, row, meta) {
            return swh.add_forge_now.formatRequestStatusName(data);
          }
        },
        {
          render: (data, type, row) => {
            if (row.status === 'FIRST_ORIGIN_LOADED') {
              const sanitizedURL = $.fn.dataTable.render.text().display(row.forge_url);
              let originsSearchUrl = `${Urls.browse_search()}?q=${encodeURIComponent(sanitizedURL)}`;
              originsSearchUrl += '&with_visit=true&with_content=true';
              return `<a href="${originsSearchUrl}" target="_blank" rel="noopener noreferrer" ` +
                     'class="swh-search-forge-origins" title="Search for origins listed from that forge">' +
                     '<i class="mdi mdi-magnify" aria-hidden="true"></i></a>';
            }
            return '';
          }
        }
      ],
      order: [[0, 'desc']]
    });
}

function isGitHubUrl(url) {
  let originUrl;
  try {
    originUrl = new URL(url);
  } catch (_) {
    return false;
  }
  const hostname = originUrl.hostname;

  const github = ['github.com', 'www.github.com'];
  if (github.includes(hostname)) {
    return true;
  }

  const githubRe = new RegExp('(^|\\.)github\\.(com|org|io)$');
  if (githubRe.test(hostname)) {
    return true;
  }

  return false;
}

function isGitLabUrl(url) {
  let originUrl;
  try {
    originUrl = new URL(url);
  } catch (_) {
    return false;
  }
  const hostname = originUrl.hostname;

  const gitlab = ['gitlab.com', 'www.gitlab.com'];
  if (gitlab.includes(hostname)) {
    return true;
  }

  const gitlabRe = new RegExp('(^|\\.)gitlab\\.(com|org|io)$');
  if (gitlabRe.test(hostname)) {
    return true;
  }

  return false;
}

function isMissingSlash(url) {
  let originUrl;
  try {
    originUrl = new URL(url);
  } catch (_) {
    return false;
  }
  return originUrl.origin === url;
}

function RegExpX(re) {
  return RegExp(re.replace(/\s+|#.*/g, ''));
}

const bitbucketPathnameExtraRe = RegExpX(`
  /
  (
    (projects|users)
    (
      # end of URL path
    |
      /
      (
        # end of URL path
      |
        [^/]+
        (
          # end of URL path
        |
          /repos/[^/]+/browse
        )
      )
    )
  |
    repos
  |
    login
  |
    getting-started
  |
    about
  |
    plugins/servlet/search
  )$`);

const cgitPathnameExtraRe = RegExpX(`
  /
  (
    [^/]+/(refs|log|commit|diff|patch|stats|plain|snapshot)/.*
  )$`);

const cgitSearchExtraRe = RegExpX(`
  ^
  (
    \\?q=[^;&]+
  )$`);

const gitlabPathnameExtraRe = RegExpX(`
  /
  (
    explore
    (
      # end of URL path
    |
      /
      (
        projects
        (
          # end of URL path
        |
          /
          (trending|starred|topics)
        )
      |
        groups
      |
        catalog
      |
        snippets
      )
    )
  |
    help
    (
      # end of URL path
    |
      /
      (
        # end of URL path
      |
        .*\\.md
      )
    )
  |
    users/
    (
      sign_(in|up)
    |
      password/new
    )
  |
    [^/]+/([^/]+/)+(activity|container_registry)
  |
    [^/]+/([^/]+/)+-/(tree|commits?|archive|blob|raw|blame|network|wikis|issues?|
                      activity|project_members|labels|boards|milestones|merge_requests|
                      branches|tags|starrers|compare|snippets?|pipelines?|jobs?|pipeline_schedules?|
                      artifacts?|releases?|ml|environments?|incidents?|graphs|value_stream_analytics)/.*
  )$`);

const giteaPathnameExtraRe = RegExpX(`
  /
  (
    explore
    (
      # end of URL path
    |
      /
      (
        repos
      |
        users
      |
        organizations
      |
        code
      )
    )
  |
    user/(login|forgot_password)
  |
    [^/]+/([^/]+/)+
    (
      \\.rss
    |
      /
      (
        actions|activity|branches|commits?|src|compare|find|forks|issues|packages
        |projects|pulls|labels|milestones|releases|stars|tags|watchers|wiki
      )(|/.*)
    )
  )$`);

const gitilesSearchExtraRe = RegExpX(`
  ^
  (
    \\?format=(TEXT|JSON)
  )$`);

const gitilesPathnameExtraRe = RegExpX(`
  /
  (
    login/.*
  |
    [^/]+/\\+
    (
      refs
    |
      /refs/(heads|tags)/.*
    |
      log
    |
      log/refs/(heads|tags)/.*
    |
      log/[a-f0-9]{40}(|/.*)
    |
      blame/[a-f0-9]{40}/.+
    |
      archive/refs/(heads|tags)/.*
    |
      archive/[a-f0-9]{40}\\.tar\\.gz
    |
      /[a-f0-9]{40}(|/.*|\\^|\\^/.*|\\^!|\\^!/.*)
    )
  )$`);

const gitwebSearchExtraRe = RegExpX(`
  (
    \\?
    (
      p=.*
    |
      a=project_list[&;].*
    |
      a=project_index
    |
      a=opml
    )
  )$`);

const stagitPathnameExtraRe = RegExpX(`
  /
  (
    [^/]+/log\\.html
  |
    [^/]+/files\\.html
  |
    [^/]+/refs\\.html
  |
    [^/]+/file/.*\\.html
  |
    [^/]+/commit/[a-f0-9]{40}\\.html
  |
  )$`);

function getUrlExtra(url) {
  let originUrl;
  try {
    originUrl = new URL(url);
  } catch (_) {
    return null;
  }
  let m = null;
  const forgeType = $('#swh-input-forge-type').val();
  if (forgeType === 'bitbucket') {
    m = bitbucketPathnameExtraRe.exec(originUrl.pathname);
  } else if (forgeType === 'cgit') {
    m = cgitPathnameExtraRe.exec(originUrl.pathname) ||
        cgitSearchExtraRe.exec(originUrl.search);
  } else if (['gitlab', 'heptapod'].includes(forgeType)) {
    m = gitlabPathnameExtraRe.exec(originUrl.pathname);
  } else if (['gogs', 'gitea', 'forgejo'].includes(forgeType)) {
    m = giteaPathnameExtraRe.exec(originUrl.pathname);
  } else if (forgeType === 'gitiles') {
    m = gitilesPathnameExtraRe.exec(originUrl.pathname) ||
        gitilesSearchExtraRe.exec(originUrl.search);
  } else if (forgeType === 'gitweb') {
    m = gitwebSearchExtraRe.exec(originUrl.search);
  } else if (forgeType === 'stagit') {
    m = stagitPathnameExtraRe.exec(originUrl.pathname);
  }
  return m ? m[1] : null;
}

export function validateForgeUrl(input) {
  let customValidity = '';
  if (!validateUrl(input.value.trim(), ['http:', 'https:'])) {
    customValidity = 'The provided forge URL is not valid.';
  }
  if (isGitHubUrl(input.value.trim())) {
    customValidity = 'The provided forge URL is on GitHub.\nUse Save code now instead.';
  }
  if (isGitLabUrl(input.value.trim())) {
    customValidity = 'The provided forge URL is on GitLab.\nUse Save code now instead.';
  }
  if (isMissingSlash(input.value.trim())) {
    customValidity = 'The provided forge URL was not a canonical URL.\nAdd a forward slash character to the end.';
  }
  const extra = getUrlExtra(input.value.trim());
  if (extra) {
    customValidity = `
      The provided forge URL was not a base URL.

      Remove this string from the URL:

      ${extra}

      Remove all user/group/repo names.
      Remove everything after both of those.`
      .replace(/^\s+/, '').replace(/\n[ \t]+/g, '\n');
  }
  input.setCustomValidity(customValidity);
}
