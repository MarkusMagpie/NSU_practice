let currentN = 4;
let signs = [];  // массив строк + - 0
let lastVertices = null;
let lastEdges = null;
let network = null; // ссылка на активный экземпляр графв
let entanglementButton = null;

function clearEntanglementUI() {
    if (entanglementButton) {
        entanglementButton.remove();
        entanglementButton = null;
    }

    $('#entanglementResult').empty();
}

function checkEntanglement() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Ошибка: таблица знаков не соответствует текущему n');
        return;
    }
    $('#entanglementResult').html('<p style="color: blue;">Проверка запутанности критерием PPT</p>');
    $.ajax({
        url: '/check_entanglement_ppt',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({n: n, signs: signs}),
        success: function(data) {
            let html = '';
            if (data.is_entangled) {
                html += `<p">Состояние запутано</p>`;
            } else {
                html += `<p>Состояние сепарабельно</p>`;
            }
            if (data.message) {
                html += `<p><em>${data.message}</em></p>`;
            }
            $('#entanglementResult').html(html);
        }
    });
}

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

function attachSignChangeHandlers() {
    $('.sign-selector').off('change').on('change', function() {
        const idx = $(this).data('idx');
        signs[idx] = $(this).val();
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
        html += `<tr><td>|${basis}></td>`;
        html += `<td><select class="sign-selector" data-idx="${i}">
                    <option value="+" ${sign === '+' ? 'selected' : ''}>+</option>
                    <option value="-" ${sign === '-' ? 'selected' : ''}>-</option>
                    <option value="0" ${sign === '0' ? 'selected' : ''}>0</option>
                  </select></td>`;
        html += `</tr>`;
    }
    html += '</table>';
    $('#tableContainer').html(html);

    attachSignChangeHandlers();
    
    if (network) network.destroy();
    network = null;
    lastVertices = null;
    lastEdges = null;
    $('#result').empty();
    clearEntanglementUI(); 
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
    const opts = ['+', '-', '0'];
    const newSigns = [];
    for (let i = 0; i < numStates; i++) {
        newSigns.push(opts[Math.floor(Math.random() * 3)]);
    }

    rebuildTable(n, newSigns);
}

function checkGraph() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Сначала сгенерируйте таблицу для выбранного n');
        return;
    }
    clearEntanglementUI();

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

                // + кнопка для проверки запутанности
                if (entanglementButton) entanglementButton.remove();
                entanglementButton = $('<button>', {
                    text: 'Проверить запутанность (PPT)',
                    id: 'checkEntanglementBtn'
                }).appendTo('#result');
                entanglementButton.on('click', checkEntanglement);
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

        const newSigns = amplitudes.map(a => {
            if (Math.abs(a) < 1e-8) return '0';
            return a > 0 ? '+' : '-';
        });

        rebuildTable(n, newSigns);
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
    const nonzeroCount = signs.filter(s => s !== '0').length;
    const norm = nonzeroCount > 0 ? 1.0 / Math.sqrt(nonzeroCount) : 0;
    let csvContent = 'базис,амплитуда\n'; // в этой строке формирую контент для blob файла для экспорта
    for (let i = 0; i < numStates; i++) {
        const basis = i.toString(2).padStart(n, '0');
        let amp = 0;
        if (signs[i] === '+') amp = norm;
        else if (signs[i] === '-') amp = -norm;
        else amp = 0;
        const ampComplex = `(${amp}+0j)`;
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