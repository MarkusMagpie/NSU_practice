$(function() {
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

    $('#buildBtn').click(function() {
        let vertices = $('#vertices').val().split(',').map(Number);
        let edgesStr = $('#edges').val().split(' ');
        let edges = edgesStr.map(pair => pair.split('-').map(Number));
        
        $.ajax({
            url: '/build_state',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({vertices: vertices, edges: edges}),
            success: function(data) {
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
    });

    $('#checkGraphBtn').click(function() {
        if (!currentVertices || !currentAmplitudes) {
            alert('Требуется сначала получить амплитуды. Для этого нужно нажать кнопку "Построить состояние"');
            return;
        }

        $.ajax({
            url: '/check_graph_state',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({vertices: currentVertices, amplitudes: currentAmplitudes}),
            success: function(data) {
                $('#result .graph-check-result').remove();

                let msg = '';
                if (data.is_graph) {
                    let edgesStr = data.edges.map(e => `${e[0]}-${e[1]}`).join(', ');
                    msg = `<p class="graph-check-result" style="color: green;">Состояние является графовым. Найденный граф: ребра [${edgesStr}]</p>`;
                } else {
                    msg = `<p class="graph-check-result" style="color: red;">Состояние НЕ является графовым.</p>`;
                }
                $('#result').append(msg);
            }
        });
    });

    $('#schmidtBtn').click(function() {
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
                $('#result').append(html);
            }
        });
    });
});