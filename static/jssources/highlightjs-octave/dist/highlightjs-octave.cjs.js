'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

/*
Language: Octave
Author: Andrew Janke <floss@apjanke.net>
Origin: matlab.js
Description: A FLOSS clone of Matlab
Website: https://octave.org
Category: scientific
*/

/*
  Formal syntax is incomplete, but published at:
  https://octave.org/doc/v5.1.0/Grammar-and-Parser.html
*/
function octave(hljs) {

  var TRANSPOSE_RE = '(\'|\\.\')+';
  var TRANSPOSE = {
    relevance: 0,
    contains: [
      { begin: TRANSPOSE_RE }
    ]
  };

  return {
    name: 'Octave',
    keywords: {
      keyword:
        '__FILE__ __LINE__ arguments break case catch classdef continue do else elseif end ' +
        'end_try_catch|10 end_unwind_protect|10 endclassdef|10 endenumeration endevents endfor|10 endfunction|10 ' +
        'endif|10 endmethods|10 endparfor|10 endproperties|10 endswitch|10 endwhile|10 ' +
        'enumeration events for function global if methods otherwise parfor persistent properties ' +
        'return switch try until unwind_protect|10 unwind_protect_cleanup|10 while',
      built_in:
        'size length ndims numel disp isempty isequal isequalwithequalnans cat reshape diag blkdiag tril ' +
        'triu fliplr flipud flipdim rot90 find sub2ind ind2sub bsxfun ndgrid permute ipermute repmat ' +
        'shiftdim circshift squeeze isscalar isvector ans eps realmax realmin pi i inf Inf nan NaN' +
        'struct cell ' +
        'feature help doc exit quit ' +
        'sin sind sinh asin asind asinh cos cosd cosh acos acosd acosh tan tand tanh atan ' +
        'atand atan2 atanh sec secd sech asec asecd asech csc cscd csch acsc acscd acsch cot ' +
        'cotd coth acot acotd acoth hypot exp expm1 log log1p log10 log2 pow2 realpow reallog ' +
        'realsqrt sqrt nthroot nextpow2 abs angle complex conj imag real unwrap isreal ' +
        'cplxpair fix floor ceil round mod rem sign airy besselj bessely besselh besseli ' +
        'besselk beta betainc betaln ellipj ellipke erf erfc erfcx erfinv expint gamma ' +
        'gammainc gammaln psi legendre cross dot factor isprime primes gcd lcm rat rats perms ' +
        'nchoosek factorial cart2sph cart2pol pol2cart sph2cart hsv2rgb rgb2hsv zeros ones ' +
        'eye rand randn linspace logspace freqspace meshgrid accumarray ' +
        'isnan isinf isfinite j why ' + 
        'compan gallery hadamard hankel hilb invhilb magic pascal ' +
        'rosser toeplitz vander wilkinson max min nanmax nanmin mean nanmean type table ' +
        'readtable writetable sortrows sort figure plot plot3 scatter scatter3 cellfun ' +
        'legend intersect ismember procrustes hold num2cell '
    },
    illegal: '(//|/\\*|\\s+/\\w+)',
    contains: [
      {
        className: 'function',
        beginKeywords: 'function', end: '$',
        contains: [
          hljs.UNDERSCORE_TITLE_MODE,
          {
            className: 'params',
            variants: [
              {begin: '\\(', end: '\\)'},
              {begin: '\\[', end: '\\]'}
            ]
          }
        ]
      },
      {
        className: 'built_in',
        begin: /true|false/,
        relevance: 0,
        starts: TRANSPOSE
      },
      {
        begin: '[a-zA-Z][a-zA-Z_0-9]*' + TRANSPOSE_RE,
        relevance: 0
      },
      {
        className: 'number',
        begin: hljs.C_NUMBER_RE,
        relevance: 0,
        starts: TRANSPOSE
      },
      {
        className: 'string',
        begin: '\'', end: '\'',
        contains: [
          hljs.BACKSLASH_ESCAPE,
          {begin: '\'\''}]
      },
      {
        begin: /\]|}|\)/,
        relevance: 0,
        starts: TRANSPOSE
      },
      {
        className: 'string',
        begin: '"', end: '"',
        contains: [
          hljs.BACKSLASH_ESCAPE,
          {begin: '""'}
        ],
        starts: TRANSPOSE
      },
      hljs.COMMENT('^\\s*\\%\\{\\s*$', '^\\s*\\%\\}\\s*$'),
      hljs.COMMENT('^\\s*\\#\\{\\s*$', '^\\s*\\#\\}\\s*$'),
      hljs.COMMENT('\\%', '$'),
      hljs.COMMENT('\\#', '$')
    ]
  };
}

exports.default = octave;
