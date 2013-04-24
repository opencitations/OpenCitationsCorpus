/*
 * jquery.graphview.js
 *
 * displays graph data results by querying a specified index
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2013
 *
 * VERSION 0.0.2
 *
 * EXPERIMENTAL / IN EARLY DEVELOPMENT / THINGS MAY NOT WORK / WOMM
 *
 */

// TODO: when viewing one bubble type, add an option to add a search term that is the OR set of the currently displayed bubbles of that type

// TODO: make a particular selection of facet values the search terms of a search on a different facet
// for example given a list if citation IDs, make a term query for identifier IDs that are the same values

// TODO: add a differentiator between queries that require a new hits set to be calculated and those that do not
// so that if a large set of hits is pulled, subsequent changes to the bubble view options can be done with a result set size of 0
// then just combine the earlier result set with the new facet answers

(function($){
    $.fn.graphview = function(options) {

        // specify the defaults
        var defaults = {
            /*"search_url": 'http://localhost:5005/everything',
            "graphable": {
                //"ignore":[], 
                //"only":[], 
                //"promote":{'record':['keywords','tags']}, 
                //"links":{'wikipedia':['topic'],'reference':['_parents'],'record':['children']},
                "ignoreisolated":false,
                "dropfacets":true,
                "drophits":true
            },*/
            //"search_url": 'http://localhost:9200/test/record/_search',
            "search_url": 'http://test.cottagelabs.com:9200/occ/record/_search',
            "graphable": false,
            "datatype": "JSONP",
            "searchbox_suggestions": [
                {"field":"journal.name.exact","display":"journals"},
                {"field":"author.name.exact","display":"authors"},
                {"field":"citation.identifier.id.exact","display":"IDs of cited articles"},
                //{"field":"title.exact","display":"titles"},
                //{"field":"keyword.exact","display":"keywords"}
            ],
            "suggestions_size": 100,
            "paging":{
                "from":0,
                "size":100
            },
            "list_overflow_control": true,
            "showlabels": false,
            "range": "date",
            "nodesize": 100,
            "nodetypes": [
                {'field':'author.name.exact','display':'authors'},
                {'field':'journal.name.exact','display':'journals'},
                {'field':'citation.identifier.id.exact','display':'citations'}
                //{'field':'keywords.exact','display':'keywords'},
                //{'field':'tags.exact','display':'tags'}
            ]

        };

        $.fn.graphview.options = $.extend(defaults, options);
        var options = $.fn.graphview.options;



        // ===============================================
        // force graph functions
        // ===============================================

        var fill = function(pkg) {
            var cols = ['#111','#333','#222','#444','#666','#888','#000','#bbb','#ddd','#c9d2d4','#ed1c24'];
            if ( isNaN(pkg) ) {
                var ln = pkg.charCodeAt(0)%cols.length;
            } else {
                var ln = pkg%cols.length;
            }
            return cols[ln];
        };
        var fill = d3.scale.category20c();
        var fill = d3.scale.category10();

        var showtitle = function(data) {
            var info = '<div class="well" style="margin-right:-10px;"><p>';
            info += '<a class="label graphview_newsearch" style="margin-right:3px;" data-facet="' + data.facet;
            info += '" data-value="' + data.className;
            info += '" alt="search only for this term" title="search only for this term" href="#">search</a> ';
            info += '<a class="label graphview_newterm" style="margin-right:3px;" data-facet="' + data.facet;
            info += '" data-value="' + data.className;
            info += '" alt="include in search terms" title="include in search terms" href="#">+ search</a> ';
            info += data.className;
            data.value && data.value > 1 ? info += ' (' + data.value + ')' : false;
            info += '</p></div>';
            $('.graphview_visinfo', obj).html("");
            $('.graphview_visinfo', obj).append(info);
            $('.graphview_newterm', obj).bind('click',newterm);
        };


        var force = function(json) {
            var w = obj.width();
            var h = obj.height();
            var vis = d3.select(".graphview_panel")
              .append("svg:svg")
                .attr("width", w)
                .attr("height", h)
                .attr("pointer-events", "all")
              .append('svg:g')
                .call(d3.behavior.zoom().on("zoom", redraw))
              .append('svg:g');

            vis.append('svg:rect')
                .attr('width', w)
                .attr('height', h)
                .attr('fill', 'white');

            function redraw() {
              vis.attr("transform",
                  "translate(" + d3.event.translate + ")"
                  + " scale(" + d3.event.scale + ")");
            }

              var force = d3.layout.force()
                  .charge(-180)
                  .linkDistance(60)
                  .nodes(json.nodes)
                  .links(json.links)
                  .size([w, h])
                  .start();

              var link = vis.selectAll("line.link")
                  .data(json.links)
                .enter().append("svg:line")
                  .attr("class", "link")
                  .attr("stroke", "#ddd")
                  .attr("stroke-opacity", 0.8)
                  .style("stroke-width", function(d) { return Math.sqrt(d.value); })
                  .attr("x1", function(d) { return d.source.x; })
                  .attr("y1", function(d) { return d.source.y; })
                  .attr("x2", function(d) { return d.target.x; })
                  .attr("y2", function(d) { return d.target.y; });

              var dom = d3.extent(json.nodes, function(d) {
                  return d.value;
              });
              var cr = d3.scale.sqrt().range([5, 25]).domain(dom);
              
              var node = vis.selectAll("circle.node")
                  .data(json.nodes)
                .enter().append("svg:circle")
                  .attr("class", "node")
                  .attr("cx", function(d) { return d.x; })
                  .attr("cy", function(d) { return d.y; })
                  .attr("r", function(d) { return cr(d.value); })
                  .style("fill", function(d) { return fill(d.group); })
                  .call(force.drag);

            var label = function(d) {
                var l = '';
                if ( d.value ) {
                    d.value > 1 ? l += '(' + d.value + ') ' : false;
                }
                if ( d.className ) {
                    if ( isNaN(d.className) ) {
                        l += d.className;//.substr(0,35);
                        if ( d.className.length == 0 || d.className == "\n" ) {
                            l += 'NO SUITABLE VALUE';
                        }
                        d.className.length > 35 ? l += '...' : false;
                    } else if ( Date.parse(d.className) ) {
                        var date = new Date(d.className);
                        l += date.getDate() + '/' + (date.getMonth() + 1) + '/' + date.getFullYear();
                    } else if (date = new Date(d.className) ) {
                        if ( date.getDate() && date.getMonth() && date.getFullYear() ) {
                            l += date.getDate() + '/' + (date.getMonth() + 1) + '/' + date.getFullYear();
                        } else {
                            l += d.className;
                        }
                    } else {
                        l += d.className;
                    }
                }
                return l;
            }
            var texts = vis.selectAll("text.label")
                .data(json.nodes)
                .enter().append("text")
                .attr("class", "svglabel")
                .attr("fill", "#bbb")
                .text(function(d) {  return label(d); });
                
              node.append("svg:title")
                  .text(function(d) { return 'CLICK FOR OPTIONS - ' + d.className; });

                node.on('click',function(d) {
                    showtitle(d)
                })


              vis.style("opacity", 1e-6)
                .transition()
                  .duration(1000)
                  .style("opacity", 1);

              force.on("tick", function() {
                link.attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node.attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });

               texts.attr("transform", function(d) {
                    return "translate(" + (d.x - cr(d.value)) + "," + (d.y + cr(d.value) + 5) + ")";
                });

              });

            !options.showlabels ? $('.svglabel').hide() : $('.svglabel').show();
        
        };
        
        // ===============================================
        // control functions
        // ===============================================

        var newterm = function(event) {
            event ? event.preventDefault() : false;
            var facet = $(this).attr('data-facet');
            var val = $(this).attr('data-value');
            if ( facet != "none" ) {
                var add = facet + '__________' + val;
            } else {
                var add = val;
            }
            // TODO: add  to the search terms box - or make this the search term, depending on search button pressed
            $(this).parent().parent().remove();
            query();
        };

        // adjust how many results are shown
        var howmany = function(event) {
            event.preventDefault();
            var newhowmany = prompt('Currently displaying ' + options.paging.size + 
                ' results per page. How many would you like instead?');
            if (newhowmany) {
                options.paging.size = parseInt(newhowmany);
                options.paging.from = 0;
                $('.graphview_howmany', obj).html(options.paging.size);
                query();
            }
        };

        // set whether or not to show labels on vis
        var labelling = function() {
            if ( options.showlabels ) {
                options.showlabels = false;
                $('.svglabel').hide();
            } else {
                options.showlabels = true;
                $('.svglabel').show();
            };
        };

        // set whether or not to ignore isolated when graphing backend is available
        var isolated = function() {
            if ( options.graphable.ignoreisolated ) {
                options.graphable.ignoreisolated = false;
            } else {
                options.graphable.ignoreisolated = true;
            };
            query();
        };

        // loop  over an object with a dot notation route to its value if found
        var findthis = function(routeparts,o,matcher) {
            if ( o[routeparts[0]] ) {
                if ( typeof(o[routeparts[0]]) == 'object' ) {
                    //alert(JSON.stringify(o[routeparts[0]]))
                    if ( $.isArray(o[routeparts[0]]) ) {
                        if ( typeof(o[routeparts[0]][0]) == 'object' ) {
                            var matched = false;
                            for ( var i in o[routeparts[0]] ) {
                                !matched ? matched = findthis(routeparts.slice(1),o[routeparts[0]][i],matcher) : false;
                            }
                            return matched;
                        } else {
                            if ( matcher in o[routeparts[0]] ) {
                                return true;
                            } else {
                                return false;
                            }
                        }
                    } else {
                        return findthis(routeparts.slice(1),o[routeparts[0]],matcher);
                    }
                } else {
                    if ( $.isArray(o[routeparts[0]]) ) {
                        if ( typeof(o[routeparts[0]][0]) == 'object' ) {
                            var matched = false;
                            for ( var i in o[routeparts[0]] ) {
                                !matched ? matched = findthis(routeparts.slice(1),o[routeparts[0]][i],matcher) : false;
                            }
                            return matched;
                        } else {
                            if ( matcher in o[routeparts[0]] ) {
                                return true;
                            } else {
                                return false;
                            }
                        }
                    } else if ( matcher == o[routeparts[0]] ) {
                        return true;
                    } else {
                        return false;
                    }
                }
            } else {
                return false;
            }
        }


        // UPDATE THE ON SCREEN CHART
        var build = function(data) {
            data ? options.data = data : false;
            // do some cleaning
            $('.graphview_panel', obj).html('');
            $('.graphview_panel', obj).css({"overflow":"visible"});
            $('.graphview_facetinfo', obj).html("");
            $('.graphview_visinfo', obj).html("");
            $('.graphview_resultcount', obj).html(options.data.hits.total);
            //options.data.hits.total < options.paging.size ? $('.graphview_howmany').val(options.data.hits.total) : false;
            // TODO: enable / disable the result set prev / next buttons depending on result size

            if ( options.graphable ) {
                force({"nodes":options.data.nodes,"links":options.data.links});
            } else { 
                var links = [];
                var sdata = [];
                for ( var i in options.data.hits.hits ) {
                    var indata = options.data.hits.hits[i].fields;
                    !indata ? indata = {} : false;
                    var pn = indata.title;
                    if ( !pn ) {
                        pn = i;
                    } else {
                        pn = pn.substring(0,1).toLowerCase();
                    }
                    $('.graphview_bubbletype:checked', obj).length ? pn = 'records' : false;
                    var arr = {
                        "record":indata,
                        "className": indata.title,
                        "group": pn,
                        "value": 0,
                        "facet": "none"
                    }
                    sdata.push(arr);
                };
                if ( $('.graphview_bubbletype:checked', obj).length ) {
                    for ( var i in options.data.facets ) {
                        //$('body').append(JSON.stringify(options.data.facets[i].terms));
                        if ( i != "range" ) {
                            var facetblurb = '<p>Showing ';
                            if ( options.data.facets[i].other != 0 ) {
                                facetblurb += 'top <input id="' + i.replace(/\./g,'_') + '_graphview_facetsize" class="graphview_facetsizer" style="width:25px;padding:0;margin:0;font-size:10px;" type="text" value="' + options.data.facets[i].terms.length + '" />';
                            } else {
                                facetblurb += 'all ' + options.data.facets[i].terms.length;
                            }
                            var itidy = i;
                            for ( var c in options.nodetypes ) {
                                if ( options.nodetypes[c].field == i ) {
                                    itidy = options.nodetypes[c].display;
                                };
                            }
                            facetblurb += ' ' + itidy + ' in current resultset</p>';
                            $('.graphview_facetinfo', obj).append(facetblurb);
                            for ( var item in options.data.facets[i].terms ) {
                                var indata = options.data.facets[i].terms;
                                if ( $('.graphview_bubbletype:checked', obj).length == 1 ) {
                                    if ( isNaN(indata[item].term) ) {
                                        var pn = indata[item].term.substring(0,1).toLowerCase();
                                    } else {
                                        var pn = indata[item].term;
                                    }
                                } else {
                                    var pn = i;
                                };
                                var pn = i;
                                var arr = {
                                    "className": indata[item].term,
                                    "group": pn,
                                    "value": indata[item].count,
                                    "facet": i
                                }
                                sdata.push(arr);
                                
                                for ( var x = 0; x < options.data.hits.hits.length; x++ ) {
                                    var record = sdata[x].record;
                                    var route = i.replace('.exact','');
                                    var source = sdata.length-1;
                                    var target = x;
                                    var value = 1;
                                    if ( findthis(route.split('.'), record, indata[item].term) ) {
                                        links.push({"source":source,"target":target,"value":value});
                                    }
                                };
                            };
                        };
                    };
                };

                $('.graphview_facetsizer').unbind('change',query).bind('change',query);
                force({"nodes":sdata,"links":links});   
            }
            
            options.range ? ranger(options.data) : false;
        };
        
        // SUBMIT A QUERY FOR MORE DATA AND TRIGGER A CHART BUILD
        var currentquery = function() {
            // check if result size has been augmented
            options.paging.size = $('.graphview_howmany').val();
            var qry = {                
                "query": {
                    "bool": {"must":[]}
                }
            };
            qry["size"] = options.paging.size;
            qry["facets"] = {};
            qry["fields"] = ["title"];
            // TODO: change this to be a check to see if the node type has been selected for display, not just available in options
            // also this will only be required when backend is not graphable
            for ( var i in options.nodetypes ) {
                var t = options.nodetypes[i].field.split('.')[0];
                qry["fields"].push(t);
            }

            var vals = [];
            $('.graphview_searchtype', obj).each(function() {
                vals = vals.concat($(this).select2("val"));
            });
            if ( vals.length != 0 ) {
                for ( var i in vals ) {
                    var kv = vals[i].split('__________');
                    if ( kv.length == 1 ) {
                        qry.query.bool.must.push({"query_string":{"query":kv[0]}});
                    } else {
                        var qobj = {"term":{}};
                        qobj.term[kv[0]] = kv[1];
                        qry.query.bool.must.push(qobj);
                    }
                }
            } else {
                qry.query.bool.must.push({"match_all":{}});
            };
            // check for any ranged values to add to the bool
            if ( $('.lowvalue', obj).val() || $('.highvalue', obj).val() ) {
                var ranged = {
                    'range': {
                        'year': {
                        }
                    }
                };
                $('.lowvalue',obj).val().length ? ranged.range.year.from = endater( $('.lowvalue', obj).val() ) : false;
                $('.highvalue',obj).val().length ? ranged.range.year.to = endater( $('.highvalue', obj).val() ) : false;
                qry.query.bool.must.push(ranged);
            };
            
            var bubbletypes = [];
            $('.graphview_bubbletype:checked', obj).each(function() {
                bubbletypes.push($(this).attr('data-value'));
            });
            for ( var b in bubbletypes ) {
                var bb = bubbletypes[b];
                if ( bb.length != 0 ) {
                    var size = options.nodesize;
                    if ( $('#' + bb.replace(/\./g,'_') + '_graphview_facetsize', obj).val() ) {
                        size = $('#' + bb.replace(/\./g,'_') + '_graphview_facetsize', obj).val();
                    };
                    var f = {
                        "terms": {
                            "field": bb,
                            "order": "count",
                            "size": size
                        }
                    }
                    qry.facets[bb] = f;
                };
            };
            // add a histogram for the range option
            if ( options.range ) {
                qry.facets.range = {
                    "date_histogram": {
                        "interval": "month",
                        "field": options.range
                    }
                };
            };
            // add graphing parameters if the backend supports graphing
            options.graphable ? qry.graph = options.graphable : false;
            options.query = qry;
            return options.query;
        };
        var query = function(event) {
            var qry = currentquery();
            //var currurl = '?source=' + JSON.stringify(qry)
            //window.history.pushState("","search",currurl);
            $('.graphview_graphit').attr('href','../timeline/myindex.html?source=' + JSON.stringify(qry));
            $.ajax({
                type: "GET",
                url: options.search_url + '?source=' + JSON.stringify(qry),
                contentType: "application/json; charset=utf-8",
                dataType: options.datatype,
                success: build
            });
        };


        // ===============================================
        // range functions
        // ===============================================

        var endater = function(d) {
            var reg = /(\d{2})-(\d{2})-(\d{4})/;
            var dateArray = reg.exec(d); 
            var dateObject = new Date(
                (+dateArray[3]),
                (+dateArray[2])-1,
                (+dateArray[1]),
                (+00),
                (+00),
                (+00)
            );
            return dateObject;
        };

        var dater = function(d) {
            var day = d.getDate();
            var month = d.getMonth() + 1;
            var year = d.getFullYear();
            var date = day + "-" + month + "-" + year;
            date = date.toString();
            var parts = date.split('-');
            parts[0].length == 1 ? parts[0] = '0' + parts[0] : "";
            parts[1].length == 1 ? parts[1] = '0' + parts[1] : "";
            date = parts[0] + '-' + parts[1] + '-' + parts[2];
            return date;
        };

        var ranger = function(data) {
            $('.lowvalue', obj).datepicker( "destroy" );
            $('.lowvalue', obj).removeClass("hasDatepicker").removeAttr('id');
            $('.highvalue', obj).datepicker( "destroy" );
            $('.highvalue', obj).removeClass("hasDatepicker").removeAttr('id');
            $('.lowvalue', obj).unbind('change',query);
            $('.highvalue', obj).unbind('change',query);
            var entries = data.facets.range.entries;
            var opts = {
                inline: true,
                dateFormat: 'dd-mm-yy',
                defaultDate: dater(new Date(entries[0].time)),
                minDate: dater(new Date(entries[0].time)),
                maxDate: dater(new Date(entries[entries.length-1].time)),
                changeYear: true
            };
            $('.lowvalue', obj).datepicker(opts);
            opts.defaultDate = dater(new Date(entries[entries.length-1].time))
            $('.highvalue', obj).datepicker(opts);
            $('.lowvalue', obj).bind('change',query);
            $('.highvalue', obj).bind('change',query);

        }


        // ===============================================
        // the graphview template to be added to the page
        // ===============================================

        var tg = '<div class="graphview" style="width:100%;height:100%;position:relative;">';

        tg += '<div class="graphview_options" style="margin:5px; z-index:1000;position:absolute;top:0;left:0;">';

        tg += '<div class="graphview_searcharea">';
        //tg += '<input type="text" class="graphview_freetext" placeholder="search term" />';
        if ( options.searchbox_suggestions.length > 0 ) {
            for ( var each in options.searchbox_suggestions ) {
                var obj = options.searchbox_suggestions[each];
                tg += '<br><input class="graphview_searchtype" data-field="' + obj['field'] + '" placeholder="' + obj['display'] + '" />';
            }
        };

        if ( options.range ) {
            tg += '<br><input type="text" class="lowvalue" style="width:100px;" placeholder="from date" />';
            tg += '<input type="text" class="highvalue" style="width:100px;" placeholder="to date" />';
            tg += '<br><a class="btn graphview_graphit" target="_blank" href="#">timeline</a>';
        }
        tg += '<div class="graphview_resultopts" style="margin:2px 0 5px 2px;color:#999;">';
        tg += 'showing <input class="graphview_howmany" type="text" value="';
        tg += options.paging.size;
        tg += '" style="width:30px;margin:1px 0 0 0;padding:0;" /> \
             of \
            <span class="graphview_resultcount" style="font-size:16px;font-weight:bold;color:#999;"></span>';
        tg += '</div>';
        tg += '</div>';

        tg += '<div class="graphview_visopts" style="margin-top:5px;"></div>';
        if ( options.graphable ) {
            tg += ' <div class="label label-info" style="display:inline;margin-right:2px;">ignore isolated';
            tg += '<input type="checkbox" class="graphview_isolated" ';
            options.graphable.ignoreisolated ? tg += "checked " : false;
            tg +='/></div>'; 
        }
        for ( var item in options.nodetypes ) {
            var node = options.nodetypes[item];
            tg += '<div class="label" style="display:inline;margin-right:2px;">' + node.display + '<input type="checkbox" class="graphview_bubbletype" data-value="' + node.field + '" /></div>';
        };
        tg += '<div class="graphview_facetinfo" style="color:#999;margin-top:10px;"></div>';
        tg += '<div class="graphview_visinfo" style="margin-top:5px;color:#999;"></div>';
        tg += '</div>';
        tg += '</div>';

        tg += '<div class="graphview_panel" style="position:absolute;top:0;left:0;">';
        tg += '</div>';
        
        tg += '</div>';

        var setsearchtype = function() {
            $('.graphview_searchtype', obj).each(function() {
                var field = $(this).attr('data-field');
                $(this).select2({
                    "tags": function(q) {
                        var qry = {
                            "query": {
                                "match_all": {}
                            },
                            "size": 0,
                            "facets": {
                                "tags":{
                                    "terms": {
                                        "field": field,
                                        "order": "count",
                                        "size": options.suggestions_size
                                    }
                                }
                            }
                        };
                        qry.facets.tags.facet_filter = {"query": currentquery().query };
                        if ( qry.facets.tags.facet_filter.query.bool.must[0].match_all !== undefined ) {
                            qry.facets.tags.facet_filter.query.bool.must = [];
                        };
                        var dropdownfilter = true;
                        if ( q.term.length ) {
                            if ( q.term.length == 1 ) {
                                var ts = {
                                    "bool":{
                                        "should":[
                                            {"prefix":{}},
                                            {"prefix":{}}
                                        ]
                                    }
                                };
                                ts.bool.should[0].prefix[field] = q.term.toLowerCase();
                                ts.bool.should[1].prefix[field] = q.term.toUpperCase();
                                qry.facets.tags.facet_filter.query.bool.must.push(ts);
                                qry.facets.tags.terms.order = "term";
                            } else {
                                if ( q.term.indexOf('*') != -1 && q.term.indexOf('~') != -1 && q.term.indexOf(':') != -1 ) {
                                    var qs = q.term;
                                    dropdownfilter = false;
                                } else if ( q.term.indexOf(' ') == -1 ) {
                                    var qs = '*' + q.term + '*';
                                } else {
                                    var qs = q.term.replace(/ /g,' AND ') + '*';
                                }
                                var ts = {
                                    "query_string":{
                                        "query": qs,
                                        "default_field": field.replace('.exact','')//,
                                        //"analyzer":"simple"
                                    }
                                };
                                qry.facets.tags.facet_filter.query.bool.must.push(ts);
                            }
                        };
                        if ( qry.facets.tags.facet_filter.query.bool.must.length == 0 ) {
                            delete qry.facets.tags.facet_filter;
                        };
                                                
                        $.ajax({
                            type: "GET",
                            url: options.search_url + '?source=' + JSON.stringify(qry),
                            contentType: "application/json; charset=utf-8",
                            dataType: options.datatype,
                            q: q,
                            field: field,
                            dropdownfilter: dropdownfilter,
                            success: function(data) {
                                var qa = this.q;
                                var t = qa.term, filtered = {results: []};
                                var tags = [];
                                var terms = data.facets.tags.terms;
                                for ( var item in terms ) {
                                    tags.push({'id':this.field + '__________' + terms[item].term,'text':terms[item].term + ' (' + terms[item].count + ')'});
                                };
                                $(tags).each(function () {
                                    var isObject = this.text !== undefined,
                                        text = isObject ? this.text : this;
                                    if ( dropdownfilter ) {
                                        if (t === "" || qa.matcher(t, text)) {
                                            filtered.results.push(isObject ? this : {id: this, text: this});
                                        }
                                    } else {
                                        filtered.results.push(isObject ? this : {id: this, text: this});
                                    };
                                });
                                qa.callback(filtered);
                            }
                        });
                    },
                    "tokenSeparators":[","],
                    "width":"element",
                });

            })
        };

        var obj = undefined;

        // ===============================================
        // now create the plugin on the page
        return this.each(function() {
            obj = $(this);

            obj.append(tg);
            
            //options.graphable ? $('.graphview_labelling', obj).bind('click',labelling) : false;
            $('.graphview_bubbletype', obj).bind('change',query);
            $('.graphview_searchtype', obj).bind('change',query);
            $('.graphview_howmany', obj).bind('change',query);
            $('.graphview_isolated', obj).bind('click',isolated);
            setsearchtype();
            
            query();

        }); // end of the function  


    };


    // graphview options are declared as a function so that they can be retrieved
    // externally (which allows for saving them remotely etc)
    $.fn.graphview.options = {};
    
})(jQuery);
