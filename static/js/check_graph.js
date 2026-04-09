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

function rebuildTable(n, signsArray) {
    currentN = n;
    const numStates = 1 << n;
    signs = [...signsArray];
    let html = '<table border="1" cellpadding="5" style="border-collapse: collapse">';
    html += '<tr><th>Базис</th><th>Знак</th></tr>';
    for (let i = 0; i < numStates; i++) {
        let basis = i.toString(2).padStart(n, '0');
        let sign = signs[i];
        html += `<tr><td>|${basis}></td><td><span class="sign-selector" data-idx="${i}"> ${sign}</span></td></tr>`;
    }
    html += '</table>';
    $('#tableContainer').html(html);

    attachSignClickHandlers();
    
    if (network) network.destroy();
    network = null;
    lastVertices = null;
    lastEdges = null;
    $('#result').empty();
}

function generateTable() {
    const n = parseInt($('#n').val());
    const numStates = 1 << n;
    const defaultSigns = new Array(numStates).fill('+');
    rebuildTable(n, defaultSigns);
    $('#n').val(n);
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

function loadAmplitudesFromCSV(file) {
    const reader = new FileReader();

    reader.onload = function(e) {
        const content = e.target.result;
        const lines = content.split('\n');
        // поиск заголовка файла - "базис,амплитуда"
        let startIdx = 0;
        if (lines[0].toLowerCase().includes('базис')) startIdx = 1;
        
        const amplitudes = [];
        for (let i = startIdx; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line === '') continue;
            const parts = line.split(',');
            if (parts.length < 2) continue;
            let ampStr = parts[1].trim();
            // Re часть (0.25+0j)
            let match = ampStr.match(/\(?([+-]?\d*\.?\d+)/);
            let realPart = match ? parseFloat(match[1]) : 0;
            if (isNaN(realPart)) realPart = 0;
            amplitudes.push(realPart);
        }

        const n = Math.round(Math.log2(amplitudes.length));
        if (2**n !== amplitudes.length) {
            alert('Некорректное количество амплитуд. Должно быть степенью двойки.');
            return;
        }

        // все модули равны
        const expectedNorm = 1.0 / Math.sqrt(2**n);
        const allEqual = amplitudes.every(a => Math.abs(Math.abs(a) - expectedNorm) < 1e-8);
        if (!allEqual) {
            alert('Модули амплитуд не равны. Состояние не может быть графовым.');
            return;
        }

        currentN = n;
        signs = amplitudes.map(a => a > 0 ? '+' : '-');

        rebuildTable(n, signs);
        // после регенерации таблицы обновление знаков в DOM
        $('.sign-selector').each(function() {
            const idx = $(this).data('idx');
            const sign = signs[idx];
            $(this).text(sign);
            if (sign === '+') $(this).addClass('plus').removeClass('minus');
            else $(this).addClass('minus').removeClass('plus');
        });
        // обновление значения поля ввода n
        $('#n').val(n);
        alert(`Загружено ${amplitudes.length} амплитуд для n=${n}`);
    };

    reader.readAsText(file);
}

function exportAmplitudesToCSV() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Сначала сгенерируй таблицу для текущего n!');
        return;
    }
    const norm = 1.0 / Math.sqrt(2**n);
    let csvContent = 'базис,амплитуда\n'; // в этой строке формирую контент для blob файла для экспорта
    for (let i = 0; i < numStates; i++) {
        const basis = i.toString(2).padStart(n, '0');
        const sign = signs[i] === '+' ? '' : '-';
        const amplitude = `${sign}${norm}`;
        // действительная часть + 0j
        const ampComplex = `(${amplitude}+0j)`;
        csvContent += `${basis},${ampComplex}\n`;
    }
    const blob = new Blob([csvContent], {type: 'text/csv'});
    const link = document.createElement('a'); // временная ссылука на blob
    const downloadurl = URL.createObjectURL(blob); // temp local url
    link.href = downloadurl;
    link.download = 'amplitudes.csv';
    link.click();
    URL.revokeObjectURL(link.href);
}

$(document).ready(function() {
    // generateTable();

    $('#generateTable').click(generateTable);
    $('#randomSigns').click(randomSigns);
    $('#checkBtn').click(checkGraph);

    $('#loadCsvBtn').click(function() {
        const fileInput = document.getElementById('csvFileInput');
        if (fileInput.files.length === 0) {
            alert('CSV файл не выбран. Пожалуйста выберите.');
            return;
        }
        loadAmplitudesFromCSV(fileInput.files[0]);
    });
    $('#exportCsvBtn').click(exportAmplitudesToCSV);
});