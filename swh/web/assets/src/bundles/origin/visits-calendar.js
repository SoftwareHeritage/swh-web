import 'bootstrap-year-calendar';
import 'bootstrap-year-calendar/css/bootstrap-year-calendar.css';

let minSize = 15;
let maxSize = 28;
let currentPopover = null;
let visitsByYear = [];
let visitsByDate = {};

function closePopover() {
  if (currentPopover) {
    $(currentPopover).popover('destroy');
    currentPopover = null;
  }
}

// function to update the visits calendar view based on the selected year
export function updateCalendar(year, filteredVisits) {
  visitsByYear = [];
  visitsByDate = {};
  for (let i = 0; i < filteredVisits.length; ++i) {
    if (filteredVisits[i].date.getUTCFullYear() === year) {
      visitsByYear.push(filteredVisits[i]);
    }
  }
  let maxNbVisitsByDate = 0;
  let minDate, maxDate;
  for (let i = 0; i < visitsByYear.length; ++i) {
    visitsByYear[i]['startDate'] = visitsByYear[i]['date'];
    visitsByYear[i]['endDate'] = visitsByYear[i]['startDate'];
    let date = new Date(visitsByYear[i]['date']);
    date.setHours(0, 0, 0, 0);
    let dateStr = date.toDateString();
    if (!visitsByDate.hasOwnProperty(dateStr)) {
      visitsByDate[dateStr] = [visitsByYear[i]];
    } else {
      visitsByDate[dateStr].push(visitsByYear[i]);
    }
    maxNbVisitsByDate = Math.max(maxNbVisitsByDate, visitsByDate[dateStr].length);
    if (i === 0) {
      minDate = maxDate = date;
    } else {
      if (date.getTime() < minDate.getTime()) {
        minDate = date;
      }
      if (date.getTime() > maxDate.getTime()) {
        maxDate = date;
      }
    }
  }

  closePopover();

  $('#swh-visits-calendar').calendar({
    dataSource: visitsByYear,
    style: 'custom',
    minDate: new Date(year, 0, 1),
    maxDate: new Date(year, 11, 31),
    startYear: year,
    customDataSourceRenderer: (element, date, events) => {
      let dateStr = date.toDateString();
      let nbVisits = visitsByDate[dateStr].length;
      let t = nbVisits / maxNbVisitsByDate;
      if (maxNbVisitsByDate === 1) {
        t = 0;
      }
      let size = minSize + t * (maxSize - minSize);
      let offsetX = (maxSize - size) / 2 - parseInt($(element).css('padding-left'));
      let offsetY = (maxSize - size) / 2 - parseInt($(element).css('padding-top')) + 1;
      let cellWrapper = $('<div></div>');
      cellWrapper.css('position', 'relative');
      let dayNumber = $('<div></div>');
      dayNumber.text($(element).text());
      let circle = $('<div></div>');
      let r = 0;
      let g = 0;
      for (let i = 0; i < nbVisits; ++i) {
        let visit = visitsByDate[dateStr][i];
        if (visit.status === 'full') {
          g += 255;
        } else if (visit.status === 'partial') {
          r += 255;
          g += 255;
        } else {
          r += 255;
        }
      }
      r /= nbVisits;
      g /= nbVisits;
      circle.css('background-color', 'rgba(' + r + ', ' + g + ', 0, 0.3)');
      circle.css('width', size + 'px');
      circle.css('height', size + 'px');
      circle.css('border-radius', size + 'px');
      circle.css('position', 'absolute');
      circle.css('top', offsetY + 'px');
      circle.css('left', offsetX + 'px');
      cellWrapper.append(dayNumber);
      cellWrapper.append(circle);
      $(element)[0].innerHTML = $(cellWrapper)[0].outerHTML;
    },
    mouseOnDay: e => {
      if (currentPopover !== e.element) {
        closePopover();
      }
      let dateStr = e.date.toDateString();
      if (visitsByDate.hasOwnProperty(dateStr)) {

        let visits = visitsByDate[dateStr];
        let content = '<div><h2>' + e.date.toDateString() + '</h2></div>';
        content += '<ul style="list-style-type: none;">';
        for (let i = 0; i < visits.length; ++i) {
          let visitTime = visits[i].fmt_date.substr(visits[i].fmt_date.indexOf(',') + 2);
          content += '<li><a class="swh-visit-' + visits[i].status + '" title="' + visits[i].status +
                     ' visit" href="' + visits[i].browse_url + '">' + visitTime + '</a></li>';
        }
        content += '</ul>';

        $(e.element).popover({
          trigger: 'manual',
          container: 'body',
          html: true,
          content: content
        });

        $(e.element).popover('show');
        currentPopover = e.element;
      }
    }
  });
  $('#swh-visits-timeline').mouseenter(() => {
    closePopover();
  });
  $('#swh-visits-list').mouseenter(() => {
    closePopover();
  });
  $('#swh-visits-calendar.calendar table td').css('width', maxSize + 'px');
  $('#swh-visits-calendar.calendar table td').css('height', maxSize + 'px');
  $('#swh-visits-calendar.calendar table td').css('padding', '0px');
}
