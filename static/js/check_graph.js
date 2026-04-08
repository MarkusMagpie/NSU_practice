let currentN = 4;
let signs = [];  // массив строк + -
let lastVertices = null;
let lastEdges = null;
let network = null; // ссылка на активный экземпляр графв

function drawGraph(vertices, edges) {
    // изменились ли данные
    let verticesChanged = JSON.stringify(vertices) !== JSON.stringify(lastVertices);
    let edgesChanged = JSON.stringify(edges) !== JSON.stringify(lastEdges);
    if (!verticesChanged && !edgesChanged && network !== null) {
        return;
    }
    lastVertices = vertices;
    lastEdges = edges;

    let nodes = vertices.map(v => ({id: v, label: v.toString()}));
    let edgesVis = edges.map(e => ({from: e[0], to: e[1]}));

    let container = document.getElementById('graph');
    let data = {nodes: nodes, edges: edgesVis};
    let options = {nodes: {shape: 'circle', size: 20}, physics: false};
    if (network) network.destroy();
    network = new vis.Network(container, data, options);
}

function attachSignClickHandlers() {
    $('.sign-selector').off('click').on('click', function() {
        const idx = $(this).data('idx');
        if (signs[idx] === '+') {
            signs[idx] = '-';
            $(this).text('-').removeClass('plus').addClass('minus');
        } else {
            signs[idx] = '+';
            $(this).text('+').removeClass('minus').addClass('plus');
        }
    });

    // синхронизация отображения знаков на странице с signs
    $('.sign-selector').each(function() {
        const idx = $(this).data('idx');
        const sign = signs[idx];
        $(this).text(sign);
        if (sign === '+') {
            $(this).addClass('plus').removeClass('minus');
        } else {
            $(this).addClass('minus').removeClass('plus');
        }
    });
}

function generateTable() {
    const n = parseInt($('#n').val());
    currentN = n;
    const numStates = 1 << n;
    signs = new Array(numStates).fill('+');
    let html = '<table border="1" cellpadding="5" style="border-collapse: collapse">';
    html += '<tr><th>Базис</th><th>Знак</th></tr>';
    for (let i = 0; i < numStates; i++) {
        let basis = i.toString(2).padStart(n, '0');
        html += `<tr><td>|${basis}></td><td><span class="sign-selector" data-idx="${i}"> +</span></td></tr>`;
    }
    html += '</table>';
    $('#tableContainer').html(html);

    attachSignClickHandlers();

    // при смене n очистить вывод о графовости 
    if (network) network.destroy();
    network = null;
    lastVertices = null;
    lastEdges = null;
    $('#result').empty();
}

function randomSigns() {
    const n = currentN;
    const numStates = 1 << n;
    for (let i = 0; i < numStates; i++) {
        signs[i] = Math.random() < 0.5 ? '+' : '-';
    }

    $('.sign-selector').each(function() {
        const idx = $(this).data('idx');
        const sign = signs[idx];
        $(this).text(sign);
        if (sign === '+') $(this).addClass('plus').removeClass('minus');
        else $(this).addClass('minus').removeClass('plus');
    });
}

function checkGraph() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Сначала сгенерируйте таблицу для выбранного n');
        return;
    }

    $.ajax({
        url: '/check_graph_submit',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({n: n, signs: signs}),
        success: function(data) {
            if (data.is_graph) {
                let edgesStr = data.edges.map(e => `${e[0]}-${e[1]}`).join(', ');
                $('#result').html(`<p style="color: green;">Состояние является графовым! Найденный граф: ребра [${edgesStr}]</p>`);

                let vertices = [];
                for (let i = 1; i <= n; i++) {
                    vertices.push(i);
                }
                drawGraph(vertices, data.edges);
            } else {
                $('#result').html('<p style="color: red;">Состояние НЕ является графовым.</p>');
                if (network) network.destroy();
                network = null;
                lastVertices = null;
                lastEdges = null;
            }
        }
    });
}

$(document).ready(function() {
    generateTable();

    $('#generateTable').click(generateTable);
    $('#randomSigns').click(randomSigns);
    $('#checkBtn').click(checkGraph);
});