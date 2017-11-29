/**
 *  Calendar:
 *     A one-off object that makes an AJAX call to the API's visit stats
 *     endpoint, then displays these statistics in a zoomable timeline-like
 *     format.
 *  Args:
 *     browse_url: the relative URL for browsing a revision via the web ui,
 *     accurate up to the origin
 *     visit_url: the complete relative URL for getting the origin's visit
 *     stats
 *     origin_id: the origin being browsed
 *     zoomw: the element that should contain the zoomable part of the calendar
 *     staticw: the element that should contain the static part of the calendar
 *     reset: the element that should reset the zoom level on click
 */

var Calendar = function(browse_url, data, origin_id,
                        zoomw, staticw, reset) {

    /** Constants **/
    this.month_names = ['Jan', 'Feb', 'Mar',
                        'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep',
                        'Oct', 'Nov', 'Dec'];

    /** Display **/
    this.desiredPxWidth = 7;

    /** Object vars **/
    this.origin_id = origin_id;
    this.zoomw = zoomw;
    this.staticw = staticw;
    /** Calendar data **/
    this.cal_data = null;
    this.static = {
        group_factor: 3600 * 1000,
        group_data: null,
        plot_data: null
    };
    this.zoom = {
        group_factor: 3600 * 1000,
        group_data: null,
        plot_data: null
    };

    zoomw.css('height', '100%');

    /**
     *  Keep a reference to the Calendar object context.
     *  Otherwise, 'this' changes to represent current function caller scope
     */
    var self = this;

    /**
     *  Group the plot's base data according to the grouping ratio and the
     *  range required
     *  Args:
     *     groupFactor: the amount the data should be grouped by
     *     range:
     *  Returns:
     *     A dictionary containing timestamps divided by the grouping ratio as
     *     keys, a list of the corresponding complete timestamps as values
     */

    this.dataGroupedRange = function(groupFactor, range) {
        var group_dict = {};
        var start = range.xaxis.from;
        var end = range.xaxis.to;
        var range_data = self.cal_data.filter(function(item, index, arr) {
            return item >= start && item <= end;
        });
        for (var date_idx in range_data) {
	    var date = range_data[date_idx];
            var floor = Math.floor(date / groupFactor);
            if (group_dict[floor] == undefined)
                group_dict[floor] = [date];
            else
                group_dict[floor].push(date);
        }
        return group_dict;
    };

    /**
     *  Update the ratio that governs how the data is grouped based on changes
     *  in the data range or the display size, and regroup the plot's data
     *  according to this value.
     *
     *  Args:
     *     element: the element in which the plot is displayed
     *     plotprops: the properties corresponding to that plot
     *     range: the range of the data displayed
     */
    this.updateGroupFactorAndData = function(element, plotprops, range) {
        var milli_length = range.xaxis.to - range.xaxis.from;
        var px_length = element.width();
        plotprops.group_factor = Math.floor(
            self.desiredPxWidth * (milli_length / px_length));
        plotprops.group_data = self.dataGroupedRange(
            plotprops.group_factor, range);
    };


    /** Get plot data from the group data **/
    this.getPlotData = function(grouped_data) {
        var plot_data = [];
        if (self.cal_data.length == 1) {
            plot_data = [[self.cal_data[0] - 3600*1000*24*30, 0],
                         [self.cal_data[0], 1],
                         [self.cal_data[0] + 3600*1000*24*30, 0]];
        }
        else {
            $.each(grouped_data, function(key, value) {
                plot_data.push([value[0], value.length]);
            });
        }
        return [{ label: 'Calendar', data: plot_data }];
    };

    this.plotZoom = function(zoom_options) {
        return $.plot(self.zoomw, self.zoom.plot_data, zoom_options);
    };

    this.plotStatic = function(static_options) {
        return $.plot(self.staticw, self.static.plot_data, static_options);
    };

    /**
     *  Display a zoomable calendar with click-through links to revisions
     *  of the same origin
     *
     *  Args:
     *     data: the data that the calendar should present, as a list of
     *           POSIX second-since-epoch timestamps
     */
    this.calendar = function(data) {
        // POSIX timestamps to JS timestamps
        self.cal_data = data.map(function(e)
                                 { return Math.floor(e['date'] * 1000); });
        /** Bootstrap the group ratio  **/
        var cal_data_range = null;
        if (self.cal_data.length == 1) {
            var padding_qty = 3600*1000*24*30;
            cal_data_range = {xaxis: {from: self.cal_data[0] - padding_qty,
                                      to: self.cal_data[0] + padding_qty}};
        }
        else
            cal_data_range = {xaxis: {from: self.cal_data[0],
                                      to: self.cal_data[self.cal_data.length -1]
                                     }
                             };
        self.updateGroupFactorAndData(self.zoomw,
                                      self.zoom,
                                      cal_data_range);
        self.updateGroupFactorAndData(self.staticw,
                                      self.static,
                                      cal_data_range);
        /** Bootstrap the plot data **/
        self.zoom.plot_data = self.getPlotData(self.zoom.group_data);
        self.static.plot_data = self.getPlotData(self.zoom.group_data);

        /**
         *  Return the flot-required function for displaying tooltips, according to
         *  the group we want to display the tooltip for
         *  Args:
         *     group_options: the group we want to display the tooltip for (self.static
         *     or self.zoom)
         */
        function tooltip_fn(group_options) {
            return function (label, x_timestamp, y_hits, item) {
                var floor_index = Math.floor(
                    item.datapoint[0] / group_options.group_factor);
                var tooltip_text = group_options.group_data[floor_index].map(
                    function(elem) {
                        var date = new Date(elem);
                        var year = date.getUTCFullYear();
                        var month = self.month_names[date.getUTCMonth()];
                        var day = date.getUTCDate();
                        var hr = date.getUTCHours();
                        var min = date.getUTCMinutes();
                        if (min < 10) min = '0'+min;
                        return [day,
                                month,
                                year + ',',
                                hr+':'+min,
                                'UTC'].join(' ');
                    }
                );
                return tooltip_text.join('<br/>');
            };
        }

        /** Plot options for both graph windows **/
        var zoom_options = {
            legend: {
                show: false
            },
            series: {
                clickable: true,
                bars: {
                    show: true,
                    lineWidth: 1,
                    barWidth: self.zoom.group_factor
                }
            },
            xaxis: {
                mode: 'time',
                minTickSize: [1, 'day'],
                // monthNames: self.month_names,
                position: 'top',
                timeformat: "%e %b %Y"
            },
            yaxis: {
                show: false
            },
            selection: {
                mode: 'x'
            },
            grid: {
                clickable: true,
                hoverable: true,
                margin: {
                    left: 30,
                    right: 30
                }
            },
            tooltip: {
                show: true,
                content: tooltip_fn(self.zoom)
            }
        };

        var overview_options = {
            legend: {
                show: false
            },
            series: {
                clickable: true,
                bars: {
                    show: true,
                    lineWidth: 1,
                    barWidth: self.static.group_factor
                },
                shadowSize: 0
            },
            yaxis: {
                show: false
            },
            xaxis: {
                mode: 'time',
                minTickSize: [1, 'day']
            },
            grid: {
                clickable: true,
                hoverable: true,
                color: '#999',
                margin: {
                    left: 30,
                    right: 30
                }
            },
            selection: {
                mode: 'x'
            },
            tooltip: {
                show: true,
                content: tooltip_fn(self.static)
            }
        };

        /** draw the windows **/
        var plot = self.plotZoom(zoom_options);
        var overview = self.plotStatic(overview_options);

        var current_ranges = $.extend(true, {}, cal_data_range);

        /**
         *  Zoom to the mouse-selected range in the given window
         *
         *  Args:
         *     plotzone: the jQuery-selected element the zoomed plot should be
         *     in (usually the same as the original 'zoom plot' element)
         *     range: the data range as a dict {xaxis: {from:, to:},
         *                                      yaxis:{from:, to:}}
         */
        function zoom(ranges) {
            current_ranges.xaxis.from = ranges.xaxis.from;
            current_ranges.xaxis.to = ranges.xaxis.to;
            self.updateGroupFactorAndData(
                self.zoomw, self.zoom, current_ranges);
            self.zoom.plot_data = self.getPlotData(self.zoom.group_data);
            var zoomedopts = $.extend(true, {}, zoom_options, {
                xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                series: {
                    bars: {barWidth: self.zoom.group_factor}
                }
            });
            return self.plotZoom(zoomedopts);
        }

        function resetZoomW(plot_options) {
            self.zoom.group_data = self.static.group_data;
            self.zoom.plot_data = self.static.plot_data;
            self.updateGroupFactorAndData(zoomw, self.zoom, cal_data_range);
            plot = self.plotZoom(plot_options);
        }

        // now connect the two
        self.zoomw.bind('plotselected', function (event, ranges) {
            zoomw.css('height', '60%');
            staticw.show();
            reset.show();
            // clamp the zooming to prevent eternal zoom
            if (ranges.xaxis.to - ranges.xaxis.from < 0.00001)
                ranges.xaxis.to = ranges.xaxis.from + 0.00001;
            // do the zooming
            plot = zoom(ranges);
            // don't fire event on the overview to prevent eternal loop
            overview.setSelection(ranges, true);
        });

        self.staticw_just_selected = false;

        self.staticw.bind('plotselected', function (event, ranges) {
            plot.setSelection(ranges);
            self.staticw_just_selected = true;
        });

        function unbindClick() {
            self.zoomw.unbind('plotclick');
            self.staticw.unbind('plotclick');
        }

        function bindClick() {
            self.zoomw.bind('plotclick', redirect_to_revision);
            self.staticw.bind('plotclick', redirect_to_revision);
        }

        function redirect_to_revision(event, pos, item) {
            if (item && !self.staticw_just_selected) {
                var js_date = new Date(item.datapoint[0]);
                js_date.setUTCSeconds(0);
                js_date.setUTCMilliseconds(0);
                var date = js_date.toISOString();
                var url = browse_url + 'ts/' + date + '/directory/';
                window.location.href = url;
            }
            self.staticw_just_selected = false;
        }

        reset.click(function(event) {
            plot.clearSelection();
            overview.clearSelection();
            current_ranges = $.extend(true, {}, cal_data_range);
            zoomw.css('height', '100%');
            resetZoomW(zoom_options);
            staticw.hide();
            reset.hide();

        });

        $(window).resize(function(event) {
            /** Update zoom display **/
            self.updateGroupFactorAndData(zoomw, self.zoom, current_ranges);
            self.zoom.plot_data = self.getPlotData(self.zoom.group_data);
            /** Update static display **/
            self.updateGroupFactorAndData(staticw, self.static, cal_data_range);
            self.static.plot_data = self.getPlotData(self.static.group_data);
            /** Replot **/
            plot = self.plotZoom(zoom_options);
            overview = self.plotStatic(overview_options);
        });

        bindClick();
        staticw.hide();
        reset.hide();

    };
    self.calendar(data);
};
