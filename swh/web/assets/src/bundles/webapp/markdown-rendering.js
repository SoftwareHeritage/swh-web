export async function renderMarkdown(domElt, markdownDocUrl) {

  let showdown = await import(/* webpackChunkName: "showdown" */ 'utils/showdown');

  $(document).ready(() => {
    let converter = new showdown.Converter({tables: true});
    fetch(markdownDocUrl, {credentials: 'same-origin'})
      .then(response => response.text())
      .then(data => {
        $(domElt).html(converter.makeHtml(data));
      });
  });

}
