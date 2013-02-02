var nodes;
var links;

var nodeToIdx = {};
var linkToIdx = {};

window.nodeFromEUI = function(eui) {
    return nodes.findProperty('eui', eui);
}

window.addNode = function(node) {
    var n = nodes.findProperty('eui', node.eui);
    node.key = node.eui;
    if (n) {
	n = node;
    } else {
	nodes.push(node);
    }
    updateMesh();
};

window.removeNode = function(eui) {
    var n = nodes.findProperty('eui', eui);
    var rmLinks = [];

    // find all the edges with this node and remove them
    links.forEach(function(l) {
	if (l.target.eui == eui || l.source.eui == eui) {
	    rmLinks.pushObject(l);
	}
    });
    rmLinks.forEach(function(l) { links.removeObject(l); });

    if (n) {
	nodes.removeObject(n);
    }

    updateMesh();
}

window.removeEdge = function(edge) {
    var key = edge.source.eui + "->" + edge.target.eui;
    var e = links.findProperty('key', key);
    if (e) {
	links.removeObject(e);
    }
    updateMesh();
}

window.addEdge = function(edge) {
    var key = edge.source.eui + "->" + edge.target.eui;
    edge.key = key;
    var e = links.findProperty('key', key);
    if (e) {
	e.etx = edge.etx;
	e.pref = edge.pref;
    } else {
	links.pushObject(edge);
    }
    updateMesh();
};

function resize() {
    var mh = $("#mesh").height();
    var mw = $("#mesh").width();

    // older firefoxes can compute this :(
    var sh = $("#splashtitle").height();
    var sw = $("#splashtitle").width();

    // fake up a percent margin on the text    
    var mar = mw * .05
    
    $("#splashtitle").attr("x", mar).attr("y",mh/2);
 
};

$().ready(function() {
    resize();
});

$(window).resize(function() {
    resize();
});

function nodeClick(eui) {
    node = nodeFromEUI(eui);
    node.select();
}

function updateMesh() {

    var link = svg.select("#links").selectAll(".link")
	.data(links, function(l) { 
	    return l.source.eui + "->" + l.target.eui;
	} );

    link.enter()
	.append("line")
	.attr("class", "link normal")
        .style("opacity", 1e-6)
	.transition()
	 .duration(500)
	.style("opacity", 1);

    link.attr("class", function(l) {
     	if (l.pref) {
     	    return "link preferred";
     	} else {
     	    return "link normal";
     	}});
    link.attr("marker-end", function(l) {
	if (l.pref) {
	    return "url(#prefarrow)";
	} else {
	    return "url(#normarrow)";
	}});
   
    link.exit()
	.transition()
	.duration(300)
	.style("opacity", 1e-6)
	.remove();

    var node = svg.select("#nodes").selectAll(".node")
	.data(nodes, function(n) { return n.eui; });

    node.enter()
	.append("circle")
     	.attr("onclick", function(d) { return "nodeClick('" + d.eui + "')"})
     	.attr("class", "node")
     	.attr("id", function(d) { return "eui" + d.eui; })
     	.attr("r", 10)
        .style("opacity", 1e-6)
	.transition()
	.duration(500)
	.style("opacity", 1);

    node.call(force.drag);

    node.exit()
	.transition()
	.duration(500)
	.style("opacity", 1e-6)
	.remove();

    force.start();

}

var svg;
var force;

(function() {

    var h = $(window).height() * .33;

    $("#mesh").height(h);

    svg = d3.select("#mesh").append("svg");
    svg.append("defs").append("marker")
	.attr("id", "prefarrow").attr("orient", "auto").attr("viewBox","0 0 20 20")
	.attr("refX", "35").attr("refY", "10")
	.append("path").attr("d", "M 0 0 L 20 10 L 0 20 z");
    svg.select("defs").append("marker")
	.attr("id", "normarrow").attr("orient", "auto").attr("viewBox","0 0 20 20")
	.attr("refX", "55").attr("refY", "10").attr("stroke", "gray").attr("fill", "gray")
	.append("path").attr("d", "M 0 0 L 20 10 L 0 20 z");
    svg.append("g").attr("id","links");
    svg.append("g").attr("id","nodes");

    svg.append("text").text("BRadmin").attr("id", "splashtitle")
	.style("opacity", 1e-6)
	.transition().duration(2000)
	.style("opacity", 1);
    
    window.mesh = svg;

    force = d3.layout.force()
	.linkDistance(function(d) { if (d.etx > 1 ) { return d.etx * 100; } else { return 75; }})
	.charge(-100)
	.gravity(0.01)
	.size([$("#mesh").width(), h]);

    nodes = force.nodes();
    links  = force.links();

    force.on("tick", function() {
	svg.selectAll(".node")
	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

	svg.selectAll(".link")
	    .attr("x1", function(d) { return d.source.x; })
	    .attr("y1", function(d) { return d.source.y; })
	    .attr("x2", function(d) { return d.target.x; })
	    .attr("y2", function(d) { return d.target.y; });
    });

    updateMesh();
 
})(); 
