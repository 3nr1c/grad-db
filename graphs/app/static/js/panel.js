/** FUNCTIONS **/
function clearPanel() {
    document.getElementById("searchField").value = "";
    document.getElementById("name").innerHTML = "";
    document.getElementById("department").innerHTML = "";
    document.getElementById("searchResults").innerHTML = "";
    document.getElementById("neighbours-list").innerHTML = "";
    document.getElementById("extra-list").innerHTML = "";
}

function subjectColoring() {
    svg.selectAll("circle")
        .attr("fill", function(d) {
            //return d3.interpolateSpectral((subject_types.indexOf(d.type) + 1)/subject_types.length);
            return d3.schemeCategory10[subject_types.indexOf(d.type) + 1];
        });

    var colorLegendDiv = document.getElementById("color-legend");
    colorLegendDiv.innerHTML = "";
    for (i=0; i < subject_types.length; i++) {
        colorLegendDiv.innerHTML += '<span style="color:' + d3.schemeCategory10[i+1] + '">' + subject_types[i];
        colorLegendDiv.innerHTML += "</span> ";
        colorLegendDiv.innerHTML += '<div class="colorPatch" style="background-color:' + d3.schemeCategory10[i+1] + '">';
        colorLegendDiv.innerHTML += '</div> ';
    }
}

function degreeColoring() {
    var z = d3.scaleLinear().domain([0, window.max_weight]).range(["rgb(73,0,146)", "rgb(36,255,36)"]);

    svg.selectAll("circle")
        .attr("fill", function(d) { return z(d.weight);});


    var colorLegendDiv = document.getElementById("color-legend");
    colorLegendDiv.innerHTML = '<span style="color: rgb(73, 0, 146)">0</span> ';
    for (i=0; i <= window.max_weight; i += window.max_weight / 10.0) {
        colorLegendDiv.innerHTML += '<div class="colorPatch" title="' + Math.round(i) + '" style="background-color:' + z(i) + '">';
        colorLegendDiv.innerHTML += '</div>';
    }
    colorLegendDiv.innerHTML += ' <span style="color: rgb(36,255,36)">' + window.max_weight + "</span>";
}

function departmentColoring() {
    var departments = [],
        z = d3.interpolateTurbo;
    svg.selectAll("circle").each(function(c) {
        if (departments.indexOf(c.department) === -1) {
            departments.push(c.department);
        }
    });
    departments = departments.sort();
    console.log(departments);

    svg.selectAll("circle")
        .attr("fill", function(d) {
            if (d.department === null) return "#666";
            else {
                return z((1+departments.indexOf(d.department)) / departments.length);
            }
        });

    var colorLegendDiv = document.getElementById("color-legend");
    colorLegendDiv.innerHTML = "";
    for (i=0; i < departments.length; i++) {
        var color = z((i+1) / departments.length);
        colorLegendDiv.innerHTML += '<div class="colorPatch" title="' + departments[i] + '" style="background-color:' + color + '">';
        colorLegendDiv.innerHTML += '</div>';

        colorLegendDiv.innerHTML += ' <span style="color:' + color + '">' + ((departments[i] !== "") ? departments[i].slice(0,40) : "(buit)") + '</span> ';
    }

    colorLegendDiv.innerHTML += '<div class="colorPatch" style="background-color: #666"></div><span style="color:#666">N/D</span>';
}

function makeUrl() {
    return "/degree/" + prevDegree + "/" + prevDataset + ".json?from_year=" + fromYear + "&to_year=" + toYear + "&k=" + minimumK;
}

var coloring = document.panelForm.coloring,
    dataset = document.panelForm.dataset,
    fromYearInput = document.panelForm.fromYear,
    toYearInput = document.panelForm.toYear,
    minimumKInput = document.panelForm.minimumK;
    prevDegree = document.panelForm.degree.value,
    prevColoring = coloring.value,
    prevDataset = dataset.value,
    fromYear = document.panelForm.fromYear.value,
    toYear = document.panelForm.toYear.value,
    minimumK = document.panelForm.minimumK.value;

var searchField = document.searchForm.searchField;

// Coloring by subject type (only subjects)
coloring[0].addEventListener('change', function() {
    prevColoring = this.value;
    subjectColoring();
});

// Coloring by connectivity degree
coloring[2].addEventListener('change', function() {
    prevColoring = this.value;
    degreeColoring();
});

// Coloring by department (only professors)
coloring[1].addEventListener('change', function() {
    prevColoring = this.value;
    departmentColoring();
});

document.panelForm.degree.addEventListener('change', function() {
    if (this.value !== prevDegree) {
        prevDegree = this.value;
        clearPanel();
        visualizeData(makeUrl());
    }
});

// Show subjects-competences graph
dataset[0].addEventListener('change', function() {
    if (this.value !== prevDataset) {
        prevDataset = this.value;
        d3.select("#extra-tag").text("Competències");
        d3.select("#coloring_1").style("display", "inline-block");
        d3.select("label[for=coloring_1]").style("display", "inline-block");
        d3.select("#coloring_3").style("display", "none");
        d3.select("label[for=coloring_3]").style("display", "none");

        coloring.value = "subject_type";
        prevColoring = "subject_type";

        clearPanel();
        visualizeData(makeUrl());
    }
});

// Show professors graph
dataset[1].addEventListener('change', function() {
    if (this.value !== prevDataset) {
        prevDataset = this.value;
        d3.select("#extra-tag").text("Assignatures");
        d3.select("#coloring_1").style("display", "none");
        d3.select("label[for=coloring_1]").style("display", "none");
        d3.select("#coloring_3").style("display", "inline-block");
        d3.select("label[for=coloring_3]").style("display", "inline-block");

        coloring.value = "department";
        prevColoring = "department";

        clearPanel();
        visualizeData(makeUrl());
    }
});

fromYearInput.addEventListener('input', function() {
    if (this.value.length === 4) {
        fromYear = this.value;

        clearPanel();
        visualizeData(makeUrl());
    }
});

toYearInput.addEventListener('input', function() {
    if (this.value.length === 4) {
        toYear = this.value;

        clearPanel();
        visualizeData(makeUrl());
    }
});

minimumKInput.addEventListener('input', function() {
    minimumK = this.value;

    clearPanel();
    visualizeData(makeUrl());
});

searchField.addEventListener('input', function() {
    var searchText = this.value.toLocaleLowerCase().trim(),
        results = document.getElementById("searchResults"),
        links = svg.selectAll("line").data(),
        children = [];

    results.innerHTML = "";
    if (searchText === "") return;

    svg.selectAll("circle")
        .filter(function(c) {
            if (-1 !== c.name.toLocaleLowerCase().indexOf(searchText)) {
                var tempChild = document.createElement("li");
                tempChild.innerText = c.name;

                var that = this;
                // results.appendChild(tempChild);
                children.push(tempChild);

                tempChild.addEventListener('mouseover', function() {
                    highlight_node(that, links);
                });
            }
        });

    // sort items by name
    children.sort(function(a, b) {
        return a.innerHTML < b.innerHTML ? -1 : 1;
    });

    for (var i = 0; i < children.length; i++) {
        results.appendChild(children[i]);
    }

});

visualizeData("/degree/TG1077/subjects.json?from_year=" + fromYear + "&to_year=" + toYear);
