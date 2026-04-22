let currentN = 4;
let signs = [];  // массив строк '+', '-', '0'

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
    html += '<table>';
    $('#tableContainer').html(html);
    attachSignChangeHandlers();
    $('#result').empty();
    $('#pyramidImage').empty();
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
    const opts = ['+', '-'];
    const newSigns = [];
    for (let i = 0; i < numStates; i++) {
        newSigns.push(opts[Math.floor(Math.random() * 2)]);
    }
    rebuildTable(n, newSigns);
}

function checkSeparability() {
    const n = currentN;
    const numStates = 1 << n;
    if (signs.length !== numStates) {
        alert('Сначала сгенерируйте таблицу для выбранного n');
        return;
    }

    $.ajax({
        url: '/check_separable_submit',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({n: n, signs: signs}),
        success: function(data) {
            let html = '';
            if (data.is_separable) {
                html += '<p>Состояние полностью сепарабельно</p>';
                html += '<p>Разложение на однокубитные состояния:</p><ul>';
                for (let i = 0; i < n; i++) {
                    let signChar = data.t[i] === 1 ? '+' : '-';
                    html += `<li>кубит ${i+1}: |0> + ${signChar}|1></li>`;
                }
                html += '</ul>';
            } else {
                html += '<p>Состояние запутано</p>';
                if (data.mismatches && data.mismatches.length > 0) {
                    html += '<p>Несовпадения в базисных состояниях: ';
                    html += data.mismatches.map(m => `|${m.toString(2).padStart(n, '0')}>`).join(', ');
                    html += '</p>';
                }
            }
            $('#result').html(html);
            if (data.image) {
                $('#pyramidImage').html(`<img src="data:image/png;base64,${data.image}" style="max-width:100%;">`);
            } else {
                $('#pyramidImage').html('<p>Изображение не сгенерировано</p>');
            }
        }
    });
}

function loadAmplitudesFromCSV(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const lines = content.split('\n');
        let startIdx = 0;
        if (lines[0].toLowerCase().includes('базис')) startIdx = 1;
        const amplitudes = [];
        for (let i = startIdx; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line === '') continue;
            const parts = line.split(',');
            if (parts.length < 2) continue;
            let ampStr = parts[1].trim();
            let match = ampStr.match(/\(?([+-]?\d*\.?\d+)/);
            let realPart = match ? parseFloat(match[1]) : 0;
            if (isNaN(realPart)) realPart = 0;
            amplitudes.push(realPart);
        }
        const n = Math.round(Math.log2(amplitudes.length));
        if (2**n !== amplitudes.length) {
            alert('Некорректное количество амплитуд');
            return;
        }
        const expectedNorm = 1.0 / Math.sqrt(2**n);
        const allEqual = amplitudes.every(a => Math.abs(Math.abs(a) - expectedNorm) < 1e-8);
        if (!allEqual) {
            alert('Модули амплитуд не равны. Знаковый критерий неприменим.');
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
        alert('Сначала сгенерируйте таблицу для текущего n!');
        return;
    }
    const nonzeroCount = signs.filter(s => s !== '0').length;
    const norm = nonzeroCount > 0 ? 1.0 / Math.sqrt(nonzeroCount) : 0;
    let csvContent = 'базис,амплитуда\n';
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
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = 'amplitudes.csv';
    link.click();
    URL.revokeObjectURL(url);
}

$(document).ready(function() {
    generateTable();
    $('#generateTable').click(generateTable);
    $('#randomSigns').click(randomSigns);
    $('#checkBtn').click(checkSeparability);
    $('#loadCsvBtn').click(function() {
        const fileInput = document.getElementById('csvFileInput');
        if (fileInput.files.length === 0) {
            alert('Выберите CSV-файл');
            return;
        }
        loadAmplitudesFromCSV(fileInput.files[0]);
    });
    $('#exportCsvBtn').click(exportAmplitudesToCSV);
});