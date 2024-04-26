/**
 * Copyright (C) 2018-2024  The Software Heritage developers
 * See the AUTHORS file at the top-level directory of this distribution
 * License: GNU Affero General Public License version 3, or any later version
 * See top-level LICENSE file for more information
 */

// adapted from pdf.js examples located at http://mozilla.github.io/pdf.js/examples/

import {staticAsset} from 'utils/functions';

export async function renderPdf(pdfUrl) {

  let pdfDoc = null;
  let pageNum = 1;
  let pageRendering = false;
  let pageNumPending = null;
  const defaultScale = 1.5;
  const canvas = $('#pdf-canvas')[0];
  const ctx = canvas.getContext('2d');

  // Get page info from document, resize canvas accordingly, and render page.
  async function renderPage(num) {
    pageRendering = true;
    // Using promise to fetch the page
    const page = await pdfDoc.getPage(num);

    const divWidth = $('.swh-content').width();
    const scale = Math.min(defaultScale, divWidth / page.getViewport({scale: 1.0}).width);

    const viewport = page.getViewport({scale: scale});
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    // Render PDF page into canvas context
    const renderContext = {
      canvasContext: ctx,
      viewport: viewport
    };

    // Wait for rendering to finish
    await page.render(renderContext);

    pageRendering = false;
    if (pageNumPending !== null) {
      // New page rendering is pending
      renderPage(pageNumPending);
      pageNumPending = null;
    }

    // Update page counters
    $('#pdf-page-num').text(num);
  }

  // If another page rendering in progress, waits until the rendering is
  // finished. Otherwise, executes rendering immediately.
  function queueRenderPage(num) {
    if (pageRendering) {
      pageNumPending = num;
    } else {
      renderPage(num);
    }
  }

  // Displays previous page.
  function onPrevPage() {
    if (pageNum <= 1) {
      return;
    }
    pageNum--;
    queueRenderPage(pageNum);
  }

  // Displays next page.
  function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
      return;
    }
    pageNum++;
    queueRenderPage(pageNum);
  }

  const pdfjs = await import(/* webpackChunkName: "pdfjs" */ 'pdfjs-dist/legacy/build/pdf.mjs');

  pdfjs.GlobalWorkerOptions.workerSrc = staticAsset('js/pdf.worker.min.js');

  $(document).ready(async() => {
    $('#pdf-prev').click(onPrevPage);
    $('#pdf-next').click(onNextPage);
    try {
      const pdf = await pdfjs.getDocument(pdfUrl).promise;
      pdfDoc = pdf;
      $('#pdf-page-count').text(pdfDoc.numPages);
      // Initial/first page rendering
      renderPage(pageNum);
    } catch (reason) {
      // PDF loading error
      console.error(reason);
    }

    // Render PDF on resize
    $(window).on('resize', function() {
      queueRenderPage(pageNum);
    });
  });

}
