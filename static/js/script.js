let lastVertices = null;
let lastEdges = null;
let currentVertices = null;
let currentAmplitudes = null;

function drawGraph(vertices, edges) {
    // изменились ли данные
    let verticesChanged = JSON.stringify(vertices) !== JSON.stringify(lastVertices);
    let edgesChanged = JSON.stringify(edges) !== JSON.stringify(lastEdges);
    if (!verticesChanged && !edgesChanged && network !== null) {
        return; // граф уже отрисован и данные не изменились
    }
    lastVertices = vertices;
    lastEdges = edges;

    let nodes = vertices.map(v => ({id: v, label: v.toString()}));
    let edgesVis = edges.map(e => ({from: e[0], to: e[1]}));

    let container = document.getElementById('graph');
    let data = {nodes: nodes, edges: edgesVis};
    let options = {nodes: {shape: 'circle', size: 20}, physics: false};
    new vis.Network(container, data, options);
}

function buildState() {
    let vertices = $('#vertices').val().split(',').map(Number);
    let edgesStr = $('#edges').val().split(' ');
    let edges = edgesStr.map(pair => pair.split('-').map(Number));
    
    $.ajax({
        url: '/build_state',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({vertices: vertices, edges: edges}),
        success: function(data) {
            $('#schmidtResult').empty();
            
            currentVertices = vertices;
            currentAmplitudes = data.amplitudes;

            let html = '<h3>Амплитуды (все):</h3>';
            html += '<div style="max-height: 400px; overflow-y: auto;">';
            html += '<table border="1" cellpadding="5" style="border-collapse: collapse; width: 50%;">';
            html += '<tr><th>Базис</th><th>Амплитуда</th></tr>';
            for (let i = 0; i < data.amplitudes.length; i++) {
                let basis = i.toString(2).padStart(data.vertices.length, '0');
                html += `<tr><td>|${basis}⟩</td><td>${data.amplitudes[i]}</td></tr>`;
            }
            html += '</table></div>';
            $('#result').html(html);

            drawGraph(vertices, edges);
        }
    });
};

function Schmidt_ranks() {
    let vertices = $('#vertices').val().split(',').map(Number);
    let edgesStr = $('#edges').val().split(' ');
    let edges = edgesStr.map(pair => pair.split('-').map(Number));
    $.ajax({
        url: '/schmidt_ranks',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({vertices: vertices, edges: edges}),
        success: function(data) {
            let html = `<h3>Ранги Шмидта:</h3><pre>${JSON.stringify(data.rank_list, null, 2)}</pre><p>Максимальный ранг: ${data.max_rank}</p>`;
            $('#schmidtResult').html(html); // в отдельный контейнер
        }
    });
};

$(document).ready(function() {
    $('#buildBtn').click(buildState);
    $('#schmidtBtn').click(Schmidt_ranks);
});