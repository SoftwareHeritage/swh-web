import hljs from 'highlight.js';

/**
 * @name Lox
 * @author jaacko-torus <jaacko.torus@gmail.com> (https://github.com/jaacko-torus)
 * @website http://craftinginterpreters.com/
 * @license MIT
 */
const regex = hljs.regex;
const IDENT_RE = "[A-Za-z][0-9A-Za-z]*";
const LANGUAGE_KEYWORDS = [
    "class",
    "else",
    "for",
    "function",
    "if",
    "print",
    "return",
    "var",
    "while",
];
const LITERALS = [
    "false",
    "nil",
    "true",
];
const BUILT_IN_VARIABLES = [
    "super",
    "this",
];
const KEYWORDS = {
    $pattern: IDENT_RE,
    keyword: LANGUAGE_KEYWORDS,
    literal: LITERALS,
    "variable.language": BUILT_IN_VARIABLES
};
const NUMBER = {
    scope: "number",
    variants: [
        { begin: "[\\d]+" },
        { begin: "\\d+(\.\\d+)?" },
    ],
    relevance: 0
};
const PARAMS_CONTAINS = [
    hljs.C_LINE_COMMENT_MODE,
    // eat recursive parens in sub expressions
    {
        begin: /\(/,
        end: /\)/,
        keywords: KEYWORDS,
        contains: ["self", hljs.C_LINE_COMMENT_MODE]
    }
];
const PARAMS = {
    scope: "params",
    begin: /\(/,
    end: /\)/,
    excludeBegin: true,
    excludeEnd: true,
    keywords: KEYWORDS,
    contains: PARAMS_CONTAINS
};
const CLASS_OR_EXTENDS = {
    variants: [
        // class Car < Vehicle
        {
            match: [
                /class/,
                /\s+/,
                IDENT_RE,
                /\s+/,
                /</,
                /\s+/,
            ],
            scope: {
                1: "keyword",
                3: "title.class",
                5: "keyword",
                7: "title.class.inherited"
            }
        },
        // class Car
        {
            match: [
                /class/,
                /\s+/,
                IDENT_RE
            ],
            scope: {
                1: "keyword",
                3: "title.class"
            }
        },
    ]
};
const FUNCTION_DEFINITION = {
    variants: [
        {
            match: [
                /function/,
                /\s+/,
                IDENT_RE,
                /(?=\s*\()/
            ]
        },
    ],
    scope: {
        1: "keyword",
        3: "title.function"
    },
    label: "func.def",
    contains: [PARAMS],
    illegal: /%/
};
const UPPER_CASE_CONSTANT = {
    relevance: 0,
    match: /\b[A-Z][A-Z0-9]+\b/,
    scope: "variable.constant"
};
function noneOf(list) {
    return regex.concat("(?!", list.join("|"), ")");
}
const FUNCTION_CALL = {
    match: regex.concat(/\b/, noneOf(["super"]), IDENT_RE, regex.lookahead(/\(/)),
    scope: "title.function",
    relevance: 0
};
const PROPERTY_ACCESS = {
    begin: regex.concat(/\./, regex.lookahead(regex.concat(IDENT_RE, /(?![0-9A-Za-z(])/))),
    end: IDENT_RE,
    excludeBegin: true,
    scope: "property",
    relevance: 0
};
/**
 * @name Lox
 * @param {HLJSApi} hljs
 * @website http://craftinginterpreters.com/
 */
function lox(hljs) {
    return {
        name: "Lox",
        aliases: ["lox"],
        keywords: KEYWORDS,
        illegal: /#(?![$_A-z])/,
        contains: [
            hljs.QUOTE_STRING_MODE,
            hljs.C_LINE_COMMENT_MODE,
            NUMBER,
            {
                begin: "(" + hljs.RE_STARTERS_RE + "|\\b(return)\\b)\\s*",
                keywords: "return",
                relevance: 0,
                contains: [
                    hljs.C_LINE_COMMENT_MODE,
                    hljs.REGEXP_MODE,
                    {
                        begin: /,/,
                        relevance: 0
                    },
                    {
                        match: /\s+/,
                        relevance: 0
                    },
                ],
            },
            FUNCTION_DEFINITION,
            {
                // prevent this from getting swallowed up by function since they appear "function like"
                beginKeywords: "while if for"
            },
            {
                // we have to count the parens to make sure we actually have the correct
                // bounding ( ).  There could be any number of sub-expressions inside
                // also surrounded by parens.
                begin: "\\b(?!function)" + hljs.UNDERSCORE_IDENT_RE +
                    "\\(" + // first parens
                    "[^()]*(\\(" +
                    "[^()]*(\\(" +
                    "[^()]*" +
                    "\\)[^()]*)*" +
                    "\\)[^()]*)*" +
                    "\\)\\s*\\{",
                returnBegin: true,
                label: "func.def",
                contains: [
                    PARAMS,
                    hljs.inherit(hljs.TITLE_MODE, { begin: IDENT_RE, scope: "title.function" })
                ]
            },
            PROPERTY_ACCESS,
            {
                match: [/\binit(?=\s*\()/],
                scope: { 1: "title.function" },
                contains: [PARAMS]
            },
            FUNCTION_CALL,
            UPPER_CASE_CONSTANT,
            CLASS_OR_EXTENDS,
            {
                match: /\$[(.]/ // relevance booster for a pattern common to JS libs: `$(something)` and `$.something`
            }
        ]
    };
}

export { lox as default };
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoibG94Lm1qcyIsInNvdXJjZXMiOlsiLi4vLi4vc3JjL2xveC50cyJdLCJzb3VyY2VzQ29udGVudCI6WyIvKipcbiAqIEBuYW1lIExveFxuICogQGF1dGhvciBqYWFja28tdG9ydXMgPGphYWNrby50b3J1c0BnbWFpbC5jb20+IChodHRwczovL2dpdGh1Yi5jb20vamFhY2tvLXRvcnVzKVxuICogQHdlYnNpdGUgaHR0cDovL2NyYWZ0aW5naW50ZXJwcmV0ZXJzLmNvbS9cbiAqIEBsaWNlbnNlIE1JVFxuICovXG5cbmltcG9ydCB0eXBlIHsgSExKU1JlZ2V4IH0gZnJvbSBcIi4uL3R5cGVzXCJcbmltcG9ydCB0eXBlIHsgSExKU0FwaSwgTGFuZ3VhZ2UsIExhbmd1YWdlRm4sIE1vZGUgfSBmcm9tIFwiaGlnaGxpZ2h0LmpzXCJcbmltcG9ydCBobGpzIGZyb20gXCJoaWdobGlnaHQuanNcIlxuXG5jb25zdCByZWdleCA9IChobGpzIGFzIEhMSlNBcGkgJiBITEpTUmVnZXgpLnJlZ2V4XG5cbmNvbnN0IElERU5UX1JFID0gXCJbQS1aYS16XVswLTlBLVphLXpdKlwiXG5cbmNvbnN0IExBTkdVQUdFX0tFWVdPUkRTID0gW1xuXHRcImNsYXNzXCIsXG5cdFwiZWxzZVwiLFxuXHRcImZvclwiLFxuXHRcImZ1bmN0aW9uXCIsXG5cdFwiaWZcIixcblx0XCJwcmludFwiLFxuXHRcInJldHVyblwiLFxuXHRcInZhclwiLFxuXHRcIndoaWxlXCIsXG5dXG5cbmNvbnN0IExJVEVSQUxTID0gW1xuXHRcImZhbHNlXCIsXG5cdFwibmlsXCIsXG5cdFwidHJ1ZVwiLFxuXVxuXG5jb25zdCBCVUlMVF9JTl9WQVJJQUJMRVMgPSBbXG5cdFwic3VwZXJcIixcblx0XCJ0aGlzXCIsXG5dXG5cbmNvbnN0IEtFWVdPUkRTID0ge1xuXHQkcGF0dGVybjogSURFTlRfUkUsXG5cdGtleXdvcmQ6IExBTkdVQUdFX0tFWVdPUkRTLFxuXHRsaXRlcmFsOiBMSVRFUkFMUyxcblx0XCJ2YXJpYWJsZS5sYW5ndWFnZVwiOiBCVUlMVF9JTl9WQVJJQUJMRVNcbn07XG5cbmNvbnN0IE5VTUJFUjogTW9kZSA9IHtcblx0c2NvcGU6IFwibnVtYmVyXCIsXG5cdHZhcmlhbnRzOiBbXG5cdFx0eyBiZWdpbjogXCJbXFxcXGRdK1wiIH0sXG5cdFx0eyBiZWdpbjogXCJcXFxcZCsoXFwuXFxcXGQrKT9cIiB9LFxuXHRdLFxuXHRyZWxldmFuY2U6IDBcbn07XG5cbmNvbnN0IFBBUkFNU19DT05UQUlOUyA9IFtcblx0aGxqcy5DX0xJTkVfQ09NTUVOVF9NT0RFLFxuXHQvLyBlYXQgcmVjdXJzaXZlIHBhcmVucyBpbiBzdWIgZXhwcmVzc2lvbnNcblx0e1xuXHRcdGJlZ2luOiAvXFwoLyxcblx0XHRlbmQ6IC9cXCkvLFxuXHRcdGtleXdvcmRzOiBLRVlXT1JEUyxcblx0XHRjb250YWluczogW1wic2VsZlwiLCBobGpzLkNfTElORV9DT01NRU5UX01PREVdXG5cdH0gYXMgTW9kZVxuXTtcblxuY29uc3QgUEFSQU1TOiBNb2RlID0ge1xuXHRzY29wZTogXCJwYXJhbXNcIixcblx0YmVnaW46IC9cXCgvLFxuXHRlbmQ6IC9cXCkvLFxuXHRleGNsdWRlQmVnaW46IHRydWUsXG5cdGV4Y2x1ZGVFbmQ6IHRydWUsXG5cdGtleXdvcmRzOiBLRVlXT1JEUyxcblx0Y29udGFpbnM6IFBBUkFNU19DT05UQUlOU1xufTtcblxuY29uc3QgQ0xBU1NfT1JfRVhURU5EUzogTW9kZSA9IHtcblx0dmFyaWFudHM6IFtcblx0XHQvLyBjbGFzcyBDYXIgPCBWZWhpY2xlXG5cdFx0e1xuXHRcdFx0bWF0Y2g6IFtcblx0XHRcdFx0L2NsYXNzLyxcblx0XHRcdFx0L1xccysvLFxuXHRcdFx0XHRJREVOVF9SRSxcblx0XHRcdFx0L1xccysvLFxuXHRcdFx0XHQvPC8sXG5cdFx0XHRcdC9cXHMrLyxcblx0XHRcdF0sXG5cdFx0XHRzY29wZToge1xuXHRcdFx0XHQxOiBcImtleXdvcmRcIixcblx0XHRcdFx0MzogXCJ0aXRsZS5jbGFzc1wiLFxuXHRcdFx0XHQ1OiBcImtleXdvcmRcIixcblx0XHRcdFx0NzogXCJ0aXRsZS5jbGFzcy5pbmhlcml0ZWRcIlxuXHRcdFx0fVxuXHRcdH0sXG5cdFx0Ly8gY2xhc3MgQ2FyXG5cdFx0e1xuXHRcdFx0bWF0Y2g6IFtcblx0XHRcdFx0L2NsYXNzLyxcblx0XHRcdFx0L1xccysvLFxuXHRcdFx0XHRJREVOVF9SRVxuXHRcdFx0XSxcblx0XHRcdHNjb3BlOiB7XG5cdFx0XHRcdDE6IFwia2V5d29yZFwiLFxuXHRcdFx0XHQzOiBcInRpdGxlLmNsYXNzXCJcblx0XHRcdH1cblx0XHR9LFxuXHRdXG59O1xuXG5jb25zdCBGVU5DVElPTl9ERUZJTklUSU9OOiBNb2RlID0ge1xuXHR2YXJpYW50czogW1xuXHRcdHtcblx0XHRcdG1hdGNoOiBbXG5cdFx0XHRcdC9mdW5jdGlvbi8sXG5cdFx0XHRcdC9cXHMrLyxcblx0XHRcdFx0SURFTlRfUkUsXG5cdFx0XHRcdC8oPz1cXHMqXFwoKS9cblx0XHRcdF1cblx0XHR9LFxuXHRdLFxuXHRzY29wZToge1xuXHRcdDE6IFwia2V5d29yZFwiLFxuXHRcdDM6IFwidGl0bGUuZnVuY3Rpb25cIlxuXHR9LFxuXHRsYWJlbDogXCJmdW5jLmRlZlwiLFxuXHRjb250YWluczogW1BBUkFNU10sXG5cdGlsbGVnYWw6IC8lL1xufTtcblxuY29uc3QgVVBQRVJfQ0FTRV9DT05TVEFOVDogTW9kZSA9IHtcblx0cmVsZXZhbmNlOiAwLFxuXHRtYXRjaDogL1xcYltBLVpdW0EtWjAtOV0rXFxiLyxcblx0c2NvcGU6IFwidmFyaWFibGUuY29uc3RhbnRcIlxufTtcblxuZnVuY3Rpb24gbm9uZU9mKGxpc3Q6IHN0cmluZ1tdKSB7XG5cdHJldHVybiByZWdleC5jb25jYXQoXCIoPyFcIiwgbGlzdC5qb2luKFwifFwiKSwgXCIpXCIpO1xufVxuXG5jb25zdCBGVU5DVElPTl9DQUxMOiBNb2RlID0ge1xuXHRtYXRjaDogcmVnZXguY29uY2F0KFxuXHRcdC9cXGIvLFxuXHRcdG5vbmVPZihbXCJzdXBlclwiXSksXG5cdFx0SURFTlRfUkUsIHJlZ2V4Lmxvb2thaGVhZCgvXFwoLykpLFxuXHRzY29wZTogXCJ0aXRsZS5mdW5jdGlvblwiLFxuXHRyZWxldmFuY2U6IDBcbn07XG5cbmNvbnN0IFBST1BFUlRZX0FDQ0VTUzogTW9kZSA9IHtcblx0YmVnaW46IHJlZ2V4LmNvbmNhdCgvXFwuLywgcmVnZXgubG9va2FoZWFkKFxuXHRcdHJlZ2V4LmNvbmNhdChJREVOVF9SRSwgLyg/IVswLTlBLVphLXooXSkvKVxuXHQpKSxcblx0ZW5kOiBJREVOVF9SRSxcblx0ZXhjbHVkZUJlZ2luOiB0cnVlLFxuXHRzY29wZTogXCJwcm9wZXJ0eVwiLFxuXHRyZWxldmFuY2U6IDBcbn07XG5cbi8qKlxuICogQG5hbWUgTG94XG4gKiBAcGFyYW0ge0hMSlNBcGl9IGhsanNcbiAqIEB3ZWJzaXRlIGh0dHA6Ly9jcmFmdGluZ2ludGVycHJldGVycy5jb20vXG4gKi9cbmZ1bmN0aW9uIGxveChobGpzOiBITEpTQXBpKSB7XG5cdHJldHVybiB7XG5cdFx0bmFtZTogXCJMb3hcIixcblx0XHRhbGlhc2VzOiBbXCJsb3hcIl0sXG5cdFx0a2V5d29yZHM6IEtFWVdPUkRTLFxuXHRcdGlsbGVnYWw6IC8jKD8hWyRfQS16XSkvLFxuXHRcdGNvbnRhaW5zOiBbXG5cdFx0XHRobGpzLlFVT1RFX1NUUklOR19NT0RFLFxuXHRcdFx0aGxqcy5DX0xJTkVfQ09NTUVOVF9NT0RFLFxuXHRcdFx0TlVNQkVSLFxuXHRcdFx0eyAvLyBcInZhbHVlXCIgY29udGFpbmVyXG5cdFx0XHRcdGJlZ2luOiBcIihcIiArIGhsanMuUkVfU1RBUlRFUlNfUkUgKyBcInxcXFxcYihyZXR1cm4pXFxcXGIpXFxcXHMqXCIsXG5cdFx0XHRcdGtleXdvcmRzOiBcInJldHVyblwiLFxuXHRcdFx0XHRyZWxldmFuY2U6IDAsXG5cdFx0XHRcdGNvbnRhaW5zOiBbXG5cdFx0XHRcdFx0aGxqcy5DX0xJTkVfQ09NTUVOVF9NT0RFLFxuXHRcdFx0XHRcdGhsanMuUkVHRVhQX01PREUsXG5cdFx0XHRcdFx0eyAvLyBjb3VsZCBiZSBhIGNvbW1hIGRlbGltaXRlZCBsaXN0IG9mIHBhcmFtcyB0byBhIGZ1bmN0aW9uIGNhbGxcblx0XHRcdFx0XHRcdGJlZ2luOiAvLC8sXG5cdFx0XHRcdFx0XHRyZWxldmFuY2U6IDBcblx0XHRcdFx0XHR9LFxuXHRcdFx0XHRcdHtcblx0XHRcdFx0XHRcdG1hdGNoOiAvXFxzKy8sXG5cdFx0XHRcdFx0XHRyZWxldmFuY2U6IDBcblx0XHRcdFx0XHR9LFxuXHRcdFx0XHRdLFxuXHRcdFx0fSxcblx0XHRcdEZVTkNUSU9OX0RFRklOSVRJT04sXG5cdFx0XHR7XG5cdFx0XHRcdC8vIHByZXZlbnQgdGhpcyBmcm9tIGdldHRpbmcgc3dhbGxvd2VkIHVwIGJ5IGZ1bmN0aW9uIHNpbmNlIHRoZXkgYXBwZWFyIFwiZnVuY3Rpb24gbGlrZVwiXG5cdFx0XHRcdGJlZ2luS2V5d29yZHM6IFwid2hpbGUgaWYgZm9yXCJcblx0XHRcdH0sXG5cdFx0XHR7XG5cdFx0XHRcdC8vIHdlIGhhdmUgdG8gY291bnQgdGhlIHBhcmVucyB0byBtYWtlIHN1cmUgd2UgYWN0dWFsbHkgaGF2ZSB0aGUgY29ycmVjdFxuXHRcdFx0XHQvLyBib3VuZGluZyAoICkuICBUaGVyZSBjb3VsZCBiZSBhbnkgbnVtYmVyIG9mIHN1Yi1leHByZXNzaW9ucyBpbnNpZGVcblx0XHRcdFx0Ly8gYWxzbyBzdXJyb3VuZGVkIGJ5IHBhcmVucy5cblx0XHRcdFx0YmVnaW46IFwiXFxcXGIoPyFmdW5jdGlvbilcIiArIGhsanMuVU5ERVJTQ09SRV9JREVOVF9SRSArXG5cdFx0XHRcdFx0XCJcXFxcKFwiICsgLy8gZmlyc3QgcGFyZW5zXG5cdFx0XHRcdFx0XCJbXigpXSooXFxcXChcIiArXG5cdFx0XHRcdFx0XCJbXigpXSooXFxcXChcIiArXG5cdFx0XHRcdFx0XCJbXigpXSpcIiArXG5cdFx0XHRcdFx0XCJcXFxcKVteKCldKikqXCIgK1xuXHRcdFx0XHRcdFwiXFxcXClbXigpXSopKlwiICtcblx0XHRcdFx0XHRcIlxcXFwpXFxcXHMqXFxcXHtcIiwgLy8gZW5kIHBhcmVuc1xuXHRcdFx0XHRyZXR1cm5CZWdpbjogdHJ1ZSxcblx0XHRcdFx0bGFiZWw6IFwiZnVuYy5kZWZcIixcblx0XHRcdFx0Y29udGFpbnM6IFtcblx0XHRcdFx0XHRQQVJBTVMsXG5cdFx0XHRcdFx0aGxqcy5pbmhlcml0KGhsanMuVElUTEVfTU9ERSwgeyBiZWdpbjogSURFTlRfUkUsIHNjb3BlOiBcInRpdGxlLmZ1bmN0aW9uXCIgfSlcblx0XHRcdFx0XVxuXHRcdFx0fSxcblx0XHRcdFBST1BFUlRZX0FDQ0VTUyxcblx0XHRcdHtcblx0XHRcdFx0bWF0Y2g6IFsvXFxiaW5pdCg/PVxccypcXCgpL10sXG5cdFx0XHRcdHNjb3BlOiB7IDE6IFwidGl0bGUuZnVuY3Rpb25cIiB9LFxuXHRcdFx0XHRjb250YWluczogW1BBUkFNU11cblx0XHRcdH0sXG5cdFx0XHRGVU5DVElPTl9DQUxMLFxuXHRcdFx0VVBQRVJfQ0FTRV9DT05TVEFOVCxcblx0XHRcdENMQVNTX09SX0VYVEVORFMsXG5cdFx0XHR7XG5cdFx0XHRcdG1hdGNoOiAvXFwkWyguXS8gLy8gcmVsZXZhbmNlIGJvb3N0ZXIgZm9yIGEgcGF0dGVybiBjb21tb24gdG8gSlMgbGliczogYCQoc29tZXRoaW5nKWAgYW5kIGAkLnNvbWV0aGluZ2Bcblx0XHRcdH1cblx0XHRdXG5cdH0gYXMgTGFuZ3VhZ2U7XG59XG5cbmV4cG9ydCBkZWZhdWx0IGxveCBhcyBMYW5ndWFnZUZuOyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBOzs7Ozs7QUFXQSxNQUFNLEtBQUssR0FBSSxJQUE0QixDQUFDLEtBQUssQ0FBQTtBQUVqRCxNQUFNLFFBQVEsR0FBRyxzQkFBc0IsQ0FBQTtBQUV2QyxNQUFNLGlCQUFpQixHQUFHO0lBQ3pCLE9BQU87SUFDUCxNQUFNO0lBQ04sS0FBSztJQUNMLFVBQVU7SUFDVixJQUFJO0lBQ0osT0FBTztJQUNQLFFBQVE7SUFDUixLQUFLO0lBQ0ws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
