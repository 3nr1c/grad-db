
// https://stackoverflow.com/questions/1248081/get-the-browser-viewport-dimensions-with-javascript
var w = document.getElementById("chart").offsetWidth,
    h = document.getElementById("chart").offsetHeight,
    r = 5,
    charge = -100;

var simulation = d3.forceSimulation()
    .alphaTarget(0.2)
    .force("forceX", d3.forceX(w/2).strength(0.1))
    .force("forceY", d3.forceY(h/2).strength(0.1))
    .force("charge", d3.forceManyBody().strength(charge).distanceMax(r+250))
    .force("collide", d3.forceCollide(r+4));


function visualizeData(data_source) {
    // clean previous data, in case
    // we're updating the view
    d3.select("#chart").html("");

    svg = d3.select("#chart").append("svg:svg")
    .attr("width", w)
    .attr("height", h)
    .attr("color", "#fff");

    var current_clicked = null;

    d3.json(data_source).then(function(obj) {
        /** NODES BINDING **/
        var nodes = [];
        var num_nodes = 0;
        for (i=0; i < obj.nodes.length; i++) {
            for (j=0; j < obj.links.length; j++) {
                if (obj.nodes[i].id === obj.links[j].source
                    || obj.nodes[i].id === obj.links[j].target) {
                    num_nodes++;
                    nodes.push(obj.nodes[i]);
                    break;
                }
            }
        }

        for (i=0; i < num_nodes; i++) {
            nodes[i].x = w/2 + w/5*Math.cos(2*Math.PI * i / num_nodes);
            nodes[i].y = h/2 + h/5*Math.sin(2*Math.PI * i / num_nodes);
            nodes[i].fixed = true;
        }

        simulation.nodes(nodes);

        /** LINK BINDING **/
        simulation.force("links", d3.forceLink(obj.links).id(function id(d) {return d.id;}));

        /** RENDERING **/
        svg.selectAll("line")
            .data(obj.links)
            .enter().append("svg:line")
            .attr("stroke", "#777");

        svg.selectAll("circle")
            .data(nodes)
            .enter().append("svg:circle")
            .attr("r", r)
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; })
            .attr("title", function(d) { return d.name; })
            .on("mouseover", function(d) {
                if (current_clicked !== null) {
                    current_clicked.clicked = false;
                }
                unhighlight();
                highlight_node(this, obj.links, d)
            })
            .on("mouseout", function(d) {
                if (!this.clicked)
                    unhighlight();
            })
            .on("click", function(d) {
                if (current_clicked !== null) {
                    current_clicked.clicked = false;
                }
                this.clicked = true;
                current_clicked = this;
                highlight_node(this, obj.links, d);
            });

        /** COMPUTE NODE WEIGHT AND MAX_WEIGHT **/
        window.max_weight = 0;
        svg.selectAll("circle")
            .each(function(d) {
                d.weight = 0;
            });

        svg.selectAll("line")
            .each(function(l) {
                l.source.weight++;
                l.target.weight++;
                window.max_weight = Math.max(Math.max(window.max_weight, l.source.weight), l.target.weight);
            });

        /** PAINT NODES **/
        if (prevColoring === "subject_type") {
            subjectColoring();
        } else if (prevColoring === "degree") {
            degreeColoring();
        } else if (prevColoring === "department") {
            departmentColoring();
        }

        /** PAINT LINKS BY STRENGTH **/
        var max_strength = 0;
        svg.selectAll("line")
            .each(function(l) {
                max_strength = Math.max(max_strength, l.strength);
            });

        var s = d3.scalePow().exponent(4).domain([0, max_strength]).range([0.4, 1]);
        svg.selectAll("line")
            .attr("stroke-opacity", function(l) { return s(l.strength); });

        /** BOUNDING BOX **/
        simulation.force("box_force", function() {
            for (var i = 0, n = nodes.length, d; i < n; ++i) {
                d = nodes[i];
                d.x = Math.max(2*r+10, Math.min(w - 2*r-10, d.x));
                d.y = Math.max(2*r+10, Math.min(h - 2*r-10, d.y));
            }
        });

        simulation.alpha(1).alphaTarget(0).restart();
    });

    simulation.on("tick", function() {
        svg.selectAll("circle")
            .attr("cx", function(d) { return d.x; })
            .attr("cy", function(d) { return d.y; });

        svg.selectAll("line")
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
    });

    svg.call(
        d3.drag()
        .subject(dragsubject)
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    );
}

function dragsubject() {
    return simulation.find(d3.event.x, d3.event.y);
}

function dragstarted() {
  if (!d3.event.active) simulation.alphaTarget(0.3).restart();
  d3.event.subject.fx = d3.event.subject.x;
  d3.event.subject.fy = d3.event.subject.y;
}

function dragged() {
  d3.event.subject.fx = d3.event.x;
  d3.event.subject.fy = d3.event.y;
}

function dragended() {
  if (!d3.event.active) simulation.alphaTarget(0);
  d3.event.subject.fx = null;
  d3.event.subject.fy = null;
}

function highlight_node(node, links) {
    unhighlight();

    /** DISPLAY INFO */
    data = d3.select(node).data()[0];
    if (data.name !== undefined) d3.select("#name").text(data.name);
    if (data.department !== undefined) d3.select("#department").text(data.department);
    if (data.type !== undefined) d3.select("#department").text(subject_type_tags[data.type]);

    /** DISPLAY EXTRA INFO */
    if (data.extra_list !== undefined) {
        d3.select("#extra-list")
            .html("")
            .selectAll("li")
            .data(data.extra_list).enter()
            .append("li")
            .text(function(li) { return li; });
    }

    /** SEARCH AND DISPLAY NEIGHBOURS LIST */
    var neighboursList = document.getElementById("neighbours-list"),
        list = [];
    neighboursList.innerHTML = "";
    for (i=0; i < links.length; i++) {
        if (links[i].source.id === data.id) {
            list.push(links[i].target.name);
        } else if (links[i].target.id === data.id) {
            list.push(links[i].source.name);
        }
    }
    var unique = list.filter(function (value, index, self) {
        return self.indexOf(value) === index;
    }).sort();
    for (i=0; i < unique.length; i++) {
        neighboursList.innerHTML += "<li>" + unique[i] + "</li>";
    }

    /** HIGHLIGHT LINKS */

    svg.selectAll("line")
        .filter(function(l) {
            return l.source.id !== data.id && l.target.id !== data.id;
        }).classed("link_hover_gray", true);

    svg.selectAll("line")
        .filter(function(l) {
            return l.source.id === data.id || l.target.id === data.id;
        }).raise();

    /** HIGHLIGHT NODES */

    svg.selectAll("circle").classed("circle_hover_gray", true);

    svg.selectAll("circle")
        .filter(function(c) {
            for (i=0; i < links.length; i++) {
                if ((c.id === links[i].source.id && data.id === links[i].target.id)
                    || (data.id === links[i].source.id && c.id === links[i].target.id)) {
                    return true;
                }
            }
            return false;
        })
        .classed("circle_hover_gray", false)
        .classed("circle_hover_neighbour", true).raise();

    d3.select(node)
        .classed("circle_hover_gray", false)
        .classed("circle_hover", true).raise();
}

function unhighlight() {
    svg.selectAll("line").classed("link_hover_gray", false);
    svg.selectAll("circle").classed("circle_hover circle_hover_neighbour circle_hover_gray", false)
        .raise();
}