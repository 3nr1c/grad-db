var subject_types = ["FB", "OB", "OT", "PR", "TR"],
    max_weight = 0,
    svg,
    subject_type_tags = {
        "FB": "Formació Bàsica",
        "OB": "Obligatòria",
        "OT": "Optativa",
        "PR": "Pràctiques",
        "TR": "Treball Final de Grau"
    },
    prevDegree = document.panelForm.degree.value,
    prevColoring = document.panelForm.coloring.value,
    prevDataset = document.panelForm.dataset.value,
    fromYear = document.panelForm.fromYear.value,
    toYear = document.panelForm.toYear.value,
    minimumK = document.panelForm.minimumK.value;

d3.json("/degrees.json").then(function(data) {
    d3.select("#degree")
        .selectAll("option")
        .data(data).enter()
        .append("option")
        .attr("value", function(d) { return d.code; })
        .property("selected", function(d) { return d.code === "TG1077"; })
        .text(function(d) { return d.code + " " + d.name; });

    prevDegree = "TG1077";
});