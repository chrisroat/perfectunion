var width = 960,
    height = 600;

var projection = d3.geo.albersUsa()
    .scale(1280)
    .translate([width / 2, height / 2]);

var path = d3.geo.path()
    .projection(projection);

var svg = d3.select("#content").append("svg")
    .attr("width", width)
    .attr("height", height);

queue()
    .defer(d3.json, "/static/us.json")
    .defer(d3.json, "/static/us-congress.json")
    .await(ready);

function ready(error, us, congress) {
    if (error) throw error;

    svg.append("defs").append("path")
    	.attr("id", "land")
    	.datum(topojson.feature(us, us.objects.land))
    	.attr("d", path);

    svg.append("clipPath")
    	.attr("id", "clip-land")
    	.append("use")
    	.attr("xlink:href", "#land");

    svg.append("g")
	.attr("class", "districts")
	.attr("clip-path", "url(#clip-land)")
	.selectAll("path")
	.data(topojson.feature(congress, congress.objects.districts).features)
	.enter().append("path")
	.attr("d", path)
	.attr("id", function(d) { return d.id;})
	.append("title")
	.text(function(d) { return d.id; });

    svg.append("path")
    	.attr("class", "district-boundaries")
    	.datum(topojson.mesh(congress, congress.objects.districts,
    			     function(a, b) { return a !== b && (a.id / 1000 | 0) === (b.id / 1000 | 0); }))
    	.attr("d", path);

    svg.append("path")
    	.attr("class", "state-boundaries")
    	.datum(topojson.mesh(us, us.objects.states, function(a, b) { return a !== b; }))
    	.attr("d", path);

    $(".districts path").each(function() {
        var clicked_id = $(this).attr("id");
	$(this).click(function() {
	    fillComment(clicked_id);
	});
    });
    $.getJSON("/counts", function(data) {
	$(".districts path").each(function() {
            var clicked_id = $(this).attr("id");
	    var title = data.title[clicked_id];
	    if (!title) {
		title = "id:" + clicked_id;
	    }
	    $(this).find("title").html(title);
	});
    });
}

$(function() {
    $(".no-comment-div").hide();
    $(".has-comment-div").hide();
});

function fillComment(clicked_id) {
    $.getJSON("/data", {fips: clicked_id})
	.done(function(data) {
	    $("#next").off('click').click(function() {
		fillComment(clicked_id);
	    });

	    $("#state_name").text(data.state_name);
	    $("#state_abbr").text(data.state_abbr);
	    $("#district").text(data.district);

	    if (data.name != null) {
		$("#name").text(data.name);
		$("#city").text(data.city);
		$("#comment").html(data.comment);
		$("#fcc_link").attr("href", data.fcc_link);
		$(".no-comment-div").hide();
		$(".has-comment-div").show();
	    } else {
		$(".no-comment-div").show();
		$(".has-comment-div").hide();
	    }
	    $('#data').modal('show');
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert("Request Failed: " + jqxhr.responseText);
	});
}

d3.select(self.frameElement).style("height", height + "px");
