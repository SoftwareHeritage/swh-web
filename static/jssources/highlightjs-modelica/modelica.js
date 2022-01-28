/*
Language: Modelica
Category: common, scripting
*/

/* globals define */

function modelica (hljs) {
  var KEYWORDS = {
    keyword:
      'constant final parameter expandable replaceable redeclare constrainedby import flow stream input output discrete connector ' +
      'for if when while then loop end if end when end for end while else elsewhen and break return each elseif ' +
      'and or not ' +
      'algorithm equation initial algorithm initial equation protected public end pure impure external encapsulated in inner operator outer '
    ,
    literal:
      'true false', // null undefined NaN Infinity',
    built_in:
      'Real Integer Boolean String enumeration type ' +
      'acos asin atan atan2 cos cosh exp log log10 sin sinh tan tanh abs sign sqrt max min product sum ' +
      'scalar vector matrix identity diagonal zeros ones fill linspace transpose outerProduct symmetric cross skew ' +
      'ceil div fill floor integer max min mod rem pre noEvent change edge initial terminal reinit sample smooth terminate ' +
      'connect der inStream actualStream semiLinear spatialDistribution getInstanceName homotopy delay assert ndims size cardinality isPresent ' +
      'extends partial within '
  }
  var NUMBER = {
    className: 'number',
    variants: [
      { begin: '\\b((0(x|X)[0-9a-fA-F]*)|(([0-9]+\\.?[0-9]*)|(\\.[0-9]+))((e|E)(\\+|-)?[0-9]+)?)\\b' }
    ],
    relevance: 0
  }
  var SUBST = {
    className: 'subst',
    begin: '\\$\\{', end: '\\}',
    keywords: KEYWORDS,
    contains: []  // defined later
  }
  var TEMPLATE_STRING = {
    className: 'string',
    begin: '`', end: '`',
    contains: [
      hljs.BACKSLASH_ESCAPE,
      SUBST
    ]
  }
  SUBST.contains = [
    hljs.APOS_STRING_MODE,
    hljs.QUOTE_STRING_MODE,
    TEMPLATE_STRING,
    NUMBER,
    hljs.REGEXP_MODE
  ]
  var SYMBOL = {
    className: 'symbol',
    begin: '\\b([a-zA-Z])(?:([^ ;,\\($]+)(;)?)([.]([a-zA-Z])(?:([^ ;,\\($]+)(;)?)?)+\\b',
    relevance: 0
  }

  return {
    aliases: ['mo'],
    keywords: KEYWORDS,
    contains: [
      hljs.APOS_STRING_MODE,
      hljs.QUOTE_STRING_MODE,
      TEMPLATE_STRING,
      hljs.C_LINE_COMMENT_MODE,
      hljs.C_BLOCK_COMMENT_MODE,
      hljs.COMMENT('annotation', '\\)\\s*;\\s*$'),
      NUMBER,
      SYMBOL,
      {
        className: 'class',
        beginKeywords: 'model class record block package',
        end: '$',
        illegal: /;/,
        contains: [
          {
            className: 'symbol',
            begin: /\w+/,
            relevance: 0
          },
          hljs.COMMENT('"', '"')
        ]
      },
      {
        className: 'class',
        beginKeywords: 'end',
        end: ';',
        contains: [
          {
            className: 'symbol',
            begin: /\w+/,
            relevance: 0
          }
        ]
      },
      hljs.METHOD_GUARD
    ]
  }
}

/**
 * hljs.registerLanguage('modelica', window.hljsDefineModelica);
 */
(function factory (ctx) {
  if (typeof process !== 'undefined' && typeof module !== 'undefined' && module.exports) {
    // nodejs
    module.exports = modelica
  } else if (typeof define !== 'undefined' && define.amd) {
    // AMD / RequireJS
    define([], () => modelica)
  } else if (typeof ctx.Window !== 'undefined' && !ctx.modelica) {
    // included in browser via <script> tag
    ctx.hljsDefineModelica = modelica
  }
})(this)
