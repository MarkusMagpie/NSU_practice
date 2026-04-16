let currentN = 4;
let signs = [];  // массив строк + - 0
let lastVertices = null;
let lastEdges = null;
let network = null; // ссылка на активный экземпляр графв

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
    $('#details').empty();
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

function checkStabilizer() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Сначала сгенерируйте таблицу для выбранного n');
        return;
    }
    $.ajax({
        url: '/check_stabilizer_submit',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({n: n, signs: signs}),

        success: function(data) {
            let html = '';
            if (data.is_stabilizer) {
                html += `<p style="color: green;">Состояние является стабилизаторным!</p>`;
                html += `<p><strong>Генераторы:</strong> ${data.generators.join(', ')}</p>`;
                html += `<p>Ранг: ${data.rank}</p>`;
                html += `<p>Количество найденных операторов: ${data.ops_and_vecs.length}</p>`;
                html += `<details><summary>Операторы </summary><pre>${JSON.stringify(data.ops_and_vecs, null, 2)}</pre></details>`;
            } else {
                html += `<p style="color: red;">Состояние НЕ является стабилизаторным.</p>`;
                html += `<p><strong>Причина:</strong> ${data.reason}</p>`;
            }
            $('#details').html(html);
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

        const newSigns = amplitudes.map(a => {
            if (Math.abs(a) < 1e-8) return '0';
            return a > 0 ? '+' : '-';
        });
        rebuildTable(n, newSigns);
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
    const url = URL.createObjectURL(blob); // temp local url
    link.href = url;
    link.download = 'amplitudes.csv';
    link.click();
    URL.revokeObjectURL(url);
}

$(document).ready(function() {
    // generateTable();

    $('#generateTable').click(generateTable);
    $('#randomSigns').click(randomSigns);
    $('#checkStabBtn').click(checkStabilizer);

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