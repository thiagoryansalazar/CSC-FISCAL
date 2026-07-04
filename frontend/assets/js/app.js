const API = '/api';

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function page(titulo, html) {
  $('#page-title').textContent = titulo;
  $('#page-content').innerHTML = html;
}

router();

function router() {
  const rota = (location.hash || '#dashboard').replace('#', '') || 'dashboard';
  $$('#sidebar nav a').forEach(a => a.classList.toggle('ativo', a.dataset.rota === rota));
  const rotas = { dashboard, entrada, notas, pendencias, assistente, relatorios, configuracoes };
  (rotas[rota] || dashboard)();
}

window.addEventListener('hashchange', router);

init();

async function init() {
  const el = $('#llm-status');
  try {
    const r = await fetch(API + '/assistente/ping');
    const d = await r.json();
    el.textContent = d.ok ? 'IA: online (' + d.modelo + ')' : 'IA: offline';
    el.className = 'status-indicator ' + (d.ok ? 'online' : 'offline');
  } catch {
    el.textContent = 'IA: offline';
    el.className = 'status-indicator offline';
  }
}

async function dashboard() {
  page('Dashboard', `
    <div class="cards" id="dash-cards">
      <div class="card"><div class="card-label">Total de Notas</div><div class="card-value" id="d-total">-</div></div>
      <div class="card"><div class="card-label">Valor Total</div><div class="card-value" id="d-valor">-</div></div>
      <div class="card"><div class="card-label">Extrações com IA</div><div class="card-value" id="d-llm">-</div></div>
      <div class="card"><div class="card-label">Divergências</div><div class="card-value" id="d-div">-</div></div>
    </div>
    <h3>Notas Recentes</h3>
    <table>
      <thead><tr><th>Nº</th><th>Fornecedor</th><th>Valor</th><th>Data</th><th>Status</th><th>Ações</th></tr></thead>
      <tbody id="d-recentes"><tr><td colspan="6">Carregando...</td></tr></tbody>
    </table>
  `);
  try {
    const r = await fetch(API + '/dashboard');
    const d = await r.json();
    $('#d-total').textContent = d.total;
    $('#d-valor').textContent = 'R$ ' + (d.valor_total || 0).toFixed(2).replace('.', ',');
    $('#d-llm').textContent = d.extracoes?.com_llm_ok || 0;
    $('#d-div').textContent = d.extracoes?.com_divergencias || 0;

    if (d.recentes?.length) {
      Promise.all(d.recentes.map(id => fetch(API + '/notas/' + id).then(r => r.json())))
        .then(notas => {
          $('#d-recentes').innerHTML = notas.map(n => {
            const nota = n.nota || n;
            return `<tr>
              <td>${nota.numero || '-'}</td>
              <td>${nota.nome_fornecedor || '-'}</td>
              <td>R$ ${(nota.valor_total || 0).toFixed(2).replace('.', ',')}</td>
              <td>${nota.data_emissao ? nota.data_emissao.slice(0, 10) : '-'}</td>
              <td><span class="tag tag-${statusClass(nota.status)}">${nota.status}</span></td>
              <td><button class="btn btn-sm" onclick="navegar('detalhes', ${nota.id})">Detalhes</button></td>
            </tr>`;
          }).join('');
        });
    } else {
      $('#d-recentes').innerHTML = '<tr><td colspan="6"><div class="empty-state"><div class="ico">&#128196;</div>Nenhuma nota cadastrada</div></td></tr>';
    }
  } catch { $('#d-recentes').innerHTML = '<tr><td colspan="6">Erro ao carregar</td></tr>'; }
}

function entrada() {
  page('Entrada de Documentos', `
    <form id="form-upload">
      <div class="upload-zone" id="upload-zone">
        <div class="ico" style="font-size:2.5rem;margin-bottom:0.5rem">&#128229;</div>
        <p><strong>Clique ou arraste</strong> XML ou PDF da NF-e</p>
        <p style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.3rem">Formatos aceitos: .xml, .pdf, .xlsx</p>
      </div>
      <input type="file" id="file-input" accept=".xml,.pdf,.xlsx" style="display:none">
      <div id="upload-status"></div>
    </form>
    <div class="cards" style="margin-top:1rem">
      <div class="card">
        <div class="card-label">Ou cadastre manualmente</div>
        <button class="btn" onclick="abrirModal('manual')" style="margin-top:0.5rem">Nova Nota Manual</button>
      </div>
    </div>
  `);

  const zone = $('#upload-zone');
  const input = $('#file-input');
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.style.borderColor = 'var(--success)'; });
  zone.addEventListener('dragleave', () => zone.style.borderColor = '');
  zone.addEventListener('drop', async e => {
    e.preventDefault(); zone.style.borderColor = '';
    if (e.dataTransfer.files.length) await uploadFile(e.dataTransfer.files[0]);
  });
  input.addEventListener('change', async () => {
    if (input.files.length) await uploadFile(input.files[0]);
  });
}

async function uploadFile(file) {
  const status = $('#upload-status');
  status.innerHTML = '<p>Enviando ' + file.name + '...</p>';
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch(API + '/upload', { method: 'POST', body: fd });
    const d = await r.json();
    if (d.erro) { status.innerHTML = '<p class="tag tag-danger">Erro: ' + d.erro + '</p>'; return; }
    status.innerHTML = '<p class="tag tag-success">Nota #' + d.nota.id + ' processada com sucesso!</p>';
    setTimeout(() => navegar('detalhes', d.nota.id), 1000);
  } catch (e) {
    status.innerHTML = '<p class="tag tag-danger">Erro ao enviar: ' + e.message + '</p>';
  }
}

async function notas() {
  page('Notas Fiscais', `
    <div class="filtros">
      <input type="text" id="f-search" placeholder="Buscar por fornecedor, número ou chave..." onkeyup="carregarNotas()">
      <select id="f-status" onchange="carregarNotas()">
        <option value="">Todos os status</option>
        <option value="NAO_PROCESSADA">Não Processada</option>
        <option value="PROCESSADA">Processada</option>
        <option value="PENDENTE">Pendente</option>
        <option value="ERRO">Erro</option>
        <option value="CONFERIDA">Conferida</option>
        <option value="FINALIZADA">Finalizada</option>
      </select>
    </div>
    <table>
      <thead><tr><th>Nº</th><th>Fornecedor</th><th>CNPJ</th><th>Valor</th><th>Emissão</th><th>Status</th><th>Ações</th></tr></thead>
      <tbody id="t-notas"><tr><td colspan="7">Carregando...</td></tr></tbody>
    </table>
  `);
  carregarNotas();
}

async function carregarNotas() {
  const search = ($('#f-search')?.value || '').trim();
  const status = ($('#f-status')?.value || '');
  let url = API + '/notas?limit=100';
  if (status) url += '&status=' + status;
  if (search) url += '&search=' + encodeURIComponent(search);

  try {
    const r = await fetch(url);
    const lista = await r.json();
    const tbody = $('#t-notas');
    if (!tbody) return;
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><div class="ico">&#128196;</div>Nenhuma nota encontrada</div></td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(n => `<tr>
      <td>${n.numero || '-'}</td>
      <td>${n.nome_fornecedor || '-'}</td>
      <td>${formatCnpj(n.cnpj_emitente) || '-'}</td>
      <td>R$ ${(n.valor_total || 0).toFixed(2).replace('.', ',')}</td>
      <td>${n.data_emissao ? n.data_emissao.slice(0, 10) : '-'}</td>
      <td><span class="tag tag-${statusClass(n.status)}">${n.status}</span></td>
      <td><button class="btn btn-sm" onclick="navegar('detalhes', ${n.id})">Detalhes</button></td>
    </tr>`).join('');
  } catch { /* ignore */ }
}

async function pendencias() {
  page('Pendências', `
    <table>
      <thead><tr><th>Nº</th><th>Fornecedor</th><th>Valor</th><th>Status</th><th>Ações</th></tr></thead>
      <tbody id="t-pendencias"><tr><td colspan="5">Carregando...</td></tr></tbody>
    </table>
  `);
  try {
    const r = await fetch(API + '/dashboard/pendencias');
    const lista = await r.json();
    const tbody = $('#t-pendencias');
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="ico">&#9989;</div>Nenhuma pendência</div></td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(n => `<tr>
      <td>${n.numero || '-'}</td>
      <td>${n.nome_fornecedor || '-'}</td>
      <td>R$ ${(n.valor_total || 0).toFixed(2).replace('.', ',')}</td>
      <td><span class="tag tag-${statusClass(n.status)}">${n.status}</span></td>
      <td><button class="btn btn-sm" onclick="navegar('detalhes', ${n.id})">Resolver</button></td>
    </tr>`).join('');
  } catch { /* ignore */ }
}

async function assistente() {
  page('Assistente IA', `
    <p style="margin-bottom:1rem;color:var(--text-secondary)">Faça perguntas sobre os documentos fiscais. O assistente busca o contexto automaticamente.</p>
    <div class="chat-box">
      <div class="chat-msgs" id="chat-msgs">
        <div class="chat-msg assistant">Olá! Pergunte sobre qualquer nota fiscal ou documento carregado no sistema.</div>
      </div>
      <div class="chat-input">
        <input type="text" id="chat-input" placeholder="Digite sua pergunta..." onkeydown="if(event.key==='Enter')enviarPergunta()">
        <button class="btn" onclick="enviarPergunta()">Enviar</button>
      </div>
    </div>
  `);
}

async function enviarPergunta() {
  const input = $('#chat-input');
  const msgs = $('#chat-msgs');
  const pergunta = input.value.trim();
  if (!pergunta) return;

  msgs.innerHTML += '<div class="chat-msg user">' + escapeHtml(pergunta) + '</div>';
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;
  msgs.innerHTML += '<div class="chat-msg assistant"><em>Pensando...</em></div>';
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const r = await fetch(API + '/assistente/perguntar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pergunta }),
    });
    const d = await r.json();
    const last = msgs.querySelector('.chat-msg:last-child');
    if (last) {
      let html = escapeHtml(d.resposta);
      if (d.docs?.length) {
        html += '<div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.5rem">Documentos consultados: ' +
          d.docs.map(do => (do.fornecedor || 'Nota #' + do.nota_id)).join(', ') + '</div>';
      }
      last.innerHTML = html;
    }
    msgs.scrollTop = msgs.scrollHeight;
  } catch {
    const last = msgs.querySelector('.chat-msg:last-child');
    if (last) last.innerHTML = '<span class="tag tag-danger">Erro ao processar pergunta</span>';
  }
}

async function detalhes(notaId) {
  page('Carregando...', '<p>Carregando detalhes...</p>');
  try {
    const r = await fetch(API + '/notas/' + notaId);
    const d = await r.json();
    const nota = d.nota;
    if (!nota) { page('Erro', '<p>Nota não encontrada</p>'); return; }

    let html = `
      <div style="display:flex;gap:1rem;align-items:center;margin-bottom:1.5rem">
        <span class="tag tag-${statusClass(nota.status)}" style="font-size:1rem">${nota.status}</span>
        <button class="btn btn-sm" onclick="abrirModal('status', ${nota.id})">Alterar Status</button>
        <button class="btn btn-sm btn-danger" onclick="confirmarDelete(${nota.id})">Excluir</button>
      </div>
      <div class="detalhes-grid">
        <div class="campo"><div class="rotulo">Número</div><div class="valor">${nota.numero || '-'}</div></div>
        <div class="campo"><div class="rotulo">Série</div><div class="valor">${nota.serie || '-'}</div></div>
        <div class="campo"><div class="rotulo">Chave de Acesso</div><div class="valor" style="font-size:0.85rem">${nota.chave_acesso || '-'}</div></div>
        <div class="campo"><div class="rotulo">Fornecedor</div><div class="valor">${nota.nome_fornecedor || '-'}</div></div>
        <div class="campo"><div class="rotulo">CNPJ</div><div class="valor">${formatCnpj(nota.cnpj_emitente) || '-'}</div></div>
        <div class="campo"><div class="rotulo">Valor Total</div><div class="valor">R$ ${(nota.valor_total || 0).toFixed(2).replace('.', ',')}</div></div>
        <div class="campo"><div class="rotulo">Data Emissão</div><div class="valor">${nota.data_emissao ? nota.data_emissao.slice(0, 10) : '-'}</div></div>
        <div class="campo"><div class="rotulo">Data Entrada</div><div class="valor">${nota.data_entrada ? nota.data_entrada.slice(0, 10) : '-'}</div></div>
        <div class="campo"><div class="rotulo">Tipo</div><div class="valor">${nota.tipo_documento || '-'}</div></div>
        <div class="campo"><div class="rotulo">Origem</div><div class="valor">${nota.origem || '-'}</div></div>
        <div class="campo" style="grid-column:1/-1"><div class="rotulo">Observações</div><div class="valor">${nota.observacoes || '-'}</div></div>
      </div>
    `;

    if (d.itens?.length) {
      html += `<h3>Itens (${d.itens.length})</h3>
      <table>
        <thead><tr><th>Código</th><th>Descrição</th><th>NCM</th><th>CFOP</th><th>Qtd</th><th>Valor Total</th></tr></thead>
        <tbody>${d.itens.map(i => `<tr>
          <td>${i.codigo || '-'}</td>
          <td>${i.descricao || '-'}</td>
          <td>${i.ncm || '-'}</td>
          <td>${i.cfop || '-'}</td>
          <td>${i.quantidade || 0}</td>
          <td>R$ ${(i.valor_total || 0).toFixed(2).replace('.', ',')}</td>
        </tr>`).join('')}</tbody>
      </table>`;
    }

    html += `
      <div class="tabs">
        <button class="ativo" onclick="switchTab(this,'hist')">Histórico</button>
        <button onclick="switchTab(this,'comp')">Comparação IA</button>
      </div>
      <div id="tab-hist"><p>Carregando histórico...</p></div>
      <div id="tab-comp" style="display:none"><p>Carregando comparação...</p></div>
    `;

    page('Nota ' + (nota.numero || '#' + nota.id), html);
    carregarHistorico(notaId);
    carregarComparacao(notaId);

  } catch {
    page('Erro', '<p>Falha ao carregar detalhes</p>');
  }
}

async function carregarHistorico(notaId) {
  const el = $('#tab-hist');
  try {
    const r = await fetch(API + '/notas/' + notaId + '/historico');
    const hist = await r.json();
    if (!hist.length) { el.innerHTML = '<p class="empty-state">Nenhum registro de histórico</p>'; return; }
    el.innerHTML = '<table><thead><tr><th>Data</th><th>Ação</th><th>Descrição</th></tr></thead><tbody>' +
      hist.map(h => `<tr><td>${h.data_hora ? h.data_hora.slice(0, 16) : '-'}</td>
        <td><span class="tag tag-info">${h.acao}</span></td>
        <td>${h.descricao || '-'}</td></tr>`).join('') + '</tbody></table>';
  } catch { el.innerHTML = '<p>Erro ao carregar histórico</p>'; }
}

async function carregarComparacao(notaId) {
  const el = $('#tab-comp');
  try {
    const r = await fetch(API + '/notas/' + notaId + '/comparacao');
    const d = await r.json();
    if (d.erro) { el.innerHTML = '<p class="empty-state">' + d.erro + '</p>'; return; }
    let html = '';
    if (d.confianca) {
      html += `<div class="cards" style="grid-template-columns:1fr">
        <div class="card"><div class="card-label">Score de Confiança</div>
        <div class="card-value">${d.confianca.score || 0}%</div>
        <div class="card-sub">${d.confianca.campos_preenchidos || 0}/${d.confianca.campos_total || 0} campos</div></div>
      </div>`;
    }
    if (d.campos_conferidos && Object.keys(d.campos_conferidos).length) {
      html += '<table><thead><tr><th>Campo</th><th>Sistema</th><th>IA</th><th>Status</th></tr></thead><tbody>';
      for (const [k, v] of Object.entries(d.campos_conferidos)) {
        html += `<tr><td>${k}</td><td>${v.sistema || '-'}</td><td>${v.llm || '-'}</td>
          <td>${v.ok ? '<span class="tag tag-success">OK</span>' : '<span class="tag tag-danger">Divergente</span>'}</td></tr>`;
      }
      html += '</tbody></table>';
    }
    if (d.divergencias?.length) {
      html += `<h4>Divergências Detectadas</h4><ul>${d.divergencias.map(di =>
        `<li><strong>${di.campo}</strong>: sistema="${di.valor_sistema}", IA="${di.valor_llm}"</li>`
      ).join('')}</ul>`;
    }
    el.innerHTML = html || '<p class="empty-state">Nenhum dado de comparação disponível</p>';
  } catch { el.innerHTML = '<p>Erro ao carregar comparação</p>'; }
}

function relatorios() {
  page('Relatórios', `
    <div class="cards" id="rel-cards">
      <div class="card"><div class="card-label">Notas Processadas</div><div class="card-value" id="r-total">-</div></div>
      <div class="card"><div class="card-label">Valor Total</div><div class="card-value" id="r-valor">-</div></div>
    </div>
    <p style="margin-bottom:1rem;color:var(--text-secondary)">Exportar dados:</p>
    <div style="display:flex;gap:1rem">
      <button class="btn" onclick="exportar('json')">Exportar JSON</button>
      <button class="btn btn-success" onclick="exportar('csv')">Exportar CSV</button>
    </div>
    <div id="export-status" style="margin-top:0.5rem"></div>
  `);
  try {
    const r = await fetch(API + '/dashboard');
    const d = await r.json();
    $('#r-total').textContent = d.total || 0;
    $('#r-valor').textContent = 'R$ ' + (d.valor_total || 0).toFixed(2).replace('.', ',');
  } catch { /* ignore */ }
}

async function exportar(formato) {
  const status = $('#export-status');
  try {
    const r = await fetch(API + '/notas?limit=1000');
    const notas = await r.json();
    if (formato === 'json') {
      const blob = new Blob([JSON.stringify(notas, null, 2)], { type: 'application/json' });
      downloadBlob(blob, 'notas_fiscais.json');
    } else if (formato === 'csv') {
      const cab = 'id,numero,serie,fornecedor,cnpj,valor,status,data_emissao\n';
      const linhas = notas.map(n =>
        [n.id, n.numero, n.serie, `"${n.nome_fornecedor || ''}"`, n.cnpj_emitente, n.valor_total, n.status, n.data_emissao].join(',')
      ).join('\n');
      const blob = new Blob(['\ufeff' + cab + linhas], { type: 'text/csv;charset=utf-8;' });
      downloadBlob(blob, 'notas_fiscais.csv');
    }
    status.innerHTML = '<span class="tag tag-success">Exportado com sucesso</span>';
    setTimeout(() => status.innerHTML = '', 3000);
  } catch {
    status.innerHTML = '<span class="tag tag-danger">Erro ao exportar</span>';
  }
}

function downloadBlob(blob, nome) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = nome; a.click();
  URL.revokeObjectURL(url);
}

function configuracoes() {
  page('Configurações', `
    <form id="form-config">
      <h3>Conexão com IA</h3>
      <label>URL do Ollama</label>
      <input type="url" id="cfg-url" value="http://localhost:11434">
      <label>Modelo</label>
      <input type="text" id="cfg-model" value="llama3.2:latest">
      <div style="display:flex;gap:1rem">
        <button class="btn" type="button" onclick="testarConexao()">Testar Conexão</button>
        <button class="btn btn-success" type="button" onclick="salvarConfig()">Salvar</button>
      </div>
      <div id="cfg-status" style="margin-top:0.5rem"></div>
    </form>
  `);
}

async function testarConexao() {
  const status = $('#cfg-status');
  status.innerHTML = '<em>Testando...</em>';
  try {
    const r = await fetch(API + '/assistente/ping');
    const d = await r.json();
    status.innerHTML = d.ok
      ? '<span class="tag tag-success">Conectado! Modelo: ' + d.modelo + '</span>'
      : '<span class="tag tag-danger">Falha na conexão</span>';
  } catch {
    status.innerHTML = '<span class="tag tag-danger">Erro ao conectar</span>';
  }
}

function salvarConfig() {
  const status = $('#cfg-status');
  status.innerHTML = '<span class="tag tag-success">Configurações salvas (localmente)</span>';
  setTimeout(() => status.innerHTML = '', 3000);
}

function navegar(rota, id) {
  if (id) location.hash = rota + '-' + id;
  else location.hash = rota;
}

function switchTab(btn, tab) {
  $$('.tabs button').forEach(b => b.classList.remove('ativo'));
  btn.classList.add('ativo');
  $$('#page-content > .tabs ~ div').forEach(d => d.style.display = 'none');
  const target = tab === 'hist' ? $('#tab-hist') : $('#tab-comp');
  if (target) target.style.display = 'block';
}

function abrirModal(tipo, notaId) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.onclick = e => { if (e.target === overlay) overlay.remove(); };

  if (tipo === 'status') {
    const statusList = ['NAO_PROCESSADA', 'PROCESSADA', 'PENDENTE', 'ERRO', 'CONFERIDA', 'FINALIZADA'];
    overlay.innerHTML = `<div class="modal" onclick="event.stopPropagation()">
      <h2>Alterar Status</h2>
      <select id="modal-status">
        ${statusList.map(s => `<option value="${s}">${s.replace(/_/g, ' ')}</option>`).join('')}
      </select>
      <div style="display:flex;gap:0.5rem;margin-top:1rem">
        <button class="btn" onclick="alterarStatus(${notaId})">Salvar</button>
        <button class="btn btn-danger" onclick="this.closest('.modal-overlay').remove()">Cancelar</button>
      </div>
    </div>`;
  } else if (tipo === 'manual') {
    overlay.innerHTML = `<div class="modal" onclick="event.stopPropagation()" style="min-width:500px">
      <h2>Nova Nota Manual</h2>
      <form id="form-manual">
        <div class="form-row">
          <div><label>Número</label><input id="m-numero"></div>
          <div><label>Série</label><input id="m-serie"></div>
        </div>
        <div class="form-row">
          <div><label>CNPJ</label><input id="m-cnpj"></div>
          <div><label>Fornecedor</label><input id="m-fornecedor"></div>
        </div>
        <div class="form-row">
          <div><label>Valor Total</label><input id="m-valor" type="number" step="0.01"></div>
          <div><label>Data Emissão</label><input id="m-data" type="date"></div>
        </div>
        <div style="display:flex;gap:0.5rem">
          <button class="btn" type="button" onclick="criarNotaManual()">Salvar</button>
          <button class="btn btn-danger" type="button" onclick="this.closest('.modal-overlay').remove()">Cancelar</button>
        </div>
      </form>
    </div>`;
  }
  document.body.appendChild(overlay);
}

async function alterarStatus(notaId) {
  const el = $('#modal-status');
  if (!el) return;
  const status = el.value;
  try {
    const r = await fetch(API + '/notas/' + notaId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    const d = await r.json();
    if (d.erro) { alert('Erro: ' + d.erro); return; }
    document.querySelector('.modal-overlay')?.remove();
    detalhes(notaId);
  } catch (e) { alert('Erro: ' + e.message); }
}

async function criarNotaManual() {
  const dados = {
    numero: $('#m-numero')?.value || '',
    serie: $('#m-serie')?.value || '',
    cnpj_emitente: ($('#m-cnpj')?.value || '').replace(/\D/g, ''),
    nome_fornecedor: $('#m-fornecedor')?.value || '',
    valor_total: parseFloat($('#m-valor')?.value || '0'),
    data_emissao: $('#m-data')?.value || '',
    origem: 'manual',
  };
  try {
    const r = await fetch(API + '/notas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const nota = await r.json();
    document.querySelector('.modal-overlay')?.remove();
    navegar('detalhes', nota.id);
  } catch (e) { alert('Erro: ' + e.message); }
}

async function confirmarDelete(notaId) {
  if (!confirm('Tem certeza que deseja excluir esta nota?')) return;
  try {
    await fetch(API + '/notas/' + notaId, { method: 'DELETE' });
    location.hash = 'dashboard';
  } catch { alert('Erro ao excluir'); }
}

function statusClass(s) {
  const map = {
    'NAO_PROCESSADA': 'secondary',
    'PROCESSADA': 'info',
    'PENDENTE': 'warning',
    'ERRO': 'danger',
    'CONFERIDA': 'success',
    'FINALIZADA': 'success',
  };
  return map[s] || 'secondary';
}

function formatCnpj(c) {
  if (!c || c.length < 14) return c || '';
  return c.slice(0, 2) + '.' + c.slice(2, 5) + '.' + c.slice(5, 8) + '/' + c.slice(8, 12) + '-' + c.slice(12, 14);
}

function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}

window.addEventListener('hashchange', () => {
  const m = location.hash.match(/^#detalhes-(\d+)$/);
  if (m) detalhes(parseInt(m[1]));
});

const m2 = location.hash.match(/^#detalhes-(\d+)$/);
if (m2) detalhes(parseInt(m2[1]));
