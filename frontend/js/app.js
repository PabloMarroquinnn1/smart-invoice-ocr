const API = window.location.origin + '/api';
let TOKEN = localStorage.getItem('token') || '';
let USER = JSON.parse(localStorage.getItem('user') || 'null');

function headers(isJson = true) {
    const h = { 'Authorization': 'Bearer ' + TOKEN };
    if (isJson) h['Content-Type'] = 'application/json';
    return h;
}

function showRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    document.getElementById('login-alert').innerHTML = '';
}
function showLogin() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-alert').innerHTML = '';
}

async function doLogin() {
    const username = document.getElementById('login-user').value.trim();
    const password = document.getElementById('login-pass').value;
    if (!username || !password) { showAlert('login-alert', 'Complete todos los campos', 'error'); return; }
    try {
        const r = await fetch(API + '/auth/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Credenciales incorrectas');
        TOKEN = data.access_token; USER = data.usuario;
        localStorage.setItem('token', TOKEN); localStorage.setItem('user', JSON.stringify(USER));
        enterApp();
    } catch (e) { showAlert('login-alert', e.message, 'error'); }
}

async function doRegister() {
    const username = document.getElementById('reg-user').value.trim();
    const password = document.getElementById('reg-pass').value;
    const nombre = document.getElementById('reg-nombre').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    if (!username || !password) { showAlert('login-alert', 'Usuario y contraseña obligatorios', 'error'); return; }
    try {
        const r = await fetch(API + '/auth/register', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, nombre, email })
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || 'Error al registrar');
        TOKEN = data.access_token; USER = data.usuario;
        localStorage.setItem('token', TOKEN); localStorage.setItem('user', JSON.stringify(USER));
        enterApp();
    } catch (e) { showAlert('login-alert', e.message, 'error'); }
}

function doLogout() {
    TOKEN = ''; USER = null;
    localStorage.removeItem('token'); localStorage.removeItem('user');
    document.getElementById('login-page').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
}

async function enterApp() {
    try {
        const r = await fetch(API + '/facturas/', { headers: headers() });
        if (r.status === 401 || r.status === 403) {
            doLogout();
            return;
        }
        document.getElementById('login-page').style.display = 'none';
        document.getElementById('app').style.display = 'block';
        showSection('dashboard');
    } catch (e) {
        doLogout();
    }
}

function showSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
    document.getElementById('sec-' + name).classList.add('active');
    const nav = document.getElementById('nav-' + name);
    if (nav) nav.classList.add('active');
    switch (name) {
        case 'dashboard': loadDashboard(); break;
        case 'facturas': loadFacturas(); break;
        case 'proveedores': loadProveedores(); break;
        case 'bitacora': loadBitacora(); break;
    }
}

async function loadDashboard() {
    try {
        const [fRes, pRes] = await Promise.all([
            fetch(API + '/facturas/', { headers: headers() }),
            fetch(API + '/proveedores/', { headers: headers() })
        ]);
        const facturas = await fRes.json();
        const proveedores = await pRes.json();
        const procesadas = facturas.filter(f => f.estado === 'Procesado');
        const errores = facturas.filter(f => f.estado === 'Error');
        const monto = procesadas.reduce((sum, f) => sum + f.total, 0);
        document.getElementById('stat-total').textContent = procesadas.length;
        document.getElementById('stat-monto').textContent = monto.toLocaleString('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        document.getElementById('stat-proveedores').textContent = proveedores.length;
        document.getElementById('stat-errores').textContent = errores.length;
        const tbody = document.getElementById('dash-facturas');
        tbody.innerHTML = facturas.slice(0, 5).map(f => `
            <tr>
                <td>${esc(f.numero_factura)}</td>
                <td>${esc(f.nombre_proveedor || '-')}</td>
                <td>${esc(f.fecha || '-')}</td>
                <td>Q ${f.total.toFixed(2)}</td>
                <td>${badgeEstado(f.estado)}</td>
            </tr>
        `).join('') || '<tr><td colspan="5" style="text-align:center;color:#999;padding:20px">No hay facturas aún</td></tr>';
    } catch (e) { console.error(e); }
}

async function loadFacturas() {
    try {
        const r = await fetch(API + '/facturas/', { headers: headers() });
        const facturas = await r.json();
        const tbody = document.getElementById('facturas-table');
        tbody.innerHTML = facturas.map(f => `
            <tr>
                <td>${esc(f.numero_factura)}</td>
                <td>${esc(f.nombre_proveedor || '-')}</td>
                <td>${esc(f.nit_proveedor || '-')}</td>
                <td>${esc(f.fecha || '-')}</td>
                <td>Q ${f.subtotal.toFixed(2)}</td>
                <td>Q ${f.impuestos.toFixed(2)}</td>
                <td><strong>Q ${f.total.toFixed(2)}</strong></td>
                <td>${badgeEstado(f.estado)}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="viewFactura(${f.id})">Ver</button>
                    <button class="btn btn-success btn-sm" onclick="ejecutarRPA(${f.id})">RPA</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteFactura(${f.id})">Eliminar</button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="9" style="text-align:center;color:#999;padding:20px">No hay facturas</td></tr>';
    } catch (e) { console.error(e); }
}

async function viewFactura(id) {
    try {
        const r = await fetch(API + '/facturas/' + id, { headers: headers() });
        const f = await r.json();
        document.getElementById('factura-detail').innerHTML = `
            <div class="detail-grid">
                <div class="detail-item"><div class="label">No. Factura</div><div class="value">${esc(f.numero_factura)}</div></div>
                <div class="detail-item"><div class="label">Estado</div><div class="value">${badgeEstado(f.estado)}</div></div>
                <div class="detail-item"><div class="label">Proveedor</div><div class="value">${esc(f.nombre_proveedor || '-')}</div></div>
                <div class="detail-item"><div class="label">NIT</div><div class="value">${esc(f.nit_proveedor || '-')}</div></div>
                <div class="detail-item"><div class="label">Fecha</div><div class="value">${esc(f.fecha || '-')}</div></div>
                <div class="detail-item"><div class="label">Cliente</div><div class="value">${esc(f.cliente_nombre || '-')}</div></div>
                <div class="detail-item" style="grid-column:span 2"><div class="label">Dirección</div><div class="value">${esc(f.cliente_direccion || '-')}</div></div>
            </div>
            <h4 style="margin:16px 0 8px">Items de la factura</h4>
            <table><thead><tr><th>Cant.</th><th>Descripción</th><th>Precio unit.</th><th>Total</th></tr></thead>
            <tbody>${f.detalles.map(d => `<tr><td>${d.cantidad}</td><td>${esc(d.descripcion)}</td><td>Q ${d.precio_unitario.toFixed(2)}</td><td>Q ${d.total_linea.toFixed(2)}</td></tr>`).join('')}</tbody></table>
            <div class="factura-totals">
                <div class="subtotal">Subtotal: Q ${f.subtotal.toFixed(2)}</div>
                <div class="subtotal">IVA 12%: Q ${f.impuestos.toFixed(2)}</div>
                <div class="total">Total: Q ${f.total.toFixed(2)}</div>
            </div>`;
        openModal('modal-factura');
    } catch (e) { console.error(e); }
}

async function deleteFactura(id) {
    if (!confirm('¿Eliminar esta factura?')) return;
    await fetch(API + '/facturas/' + id, { method: 'DELETE', headers: headers() });
    loadFacturas();
}

function setupDragDrop() {
    const zone = document.getElementById('upload-zone');
    if (!zone) return;
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]); });
}

async function uploadFile(file) {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'jpg', 'jpeg', 'png'].includes(ext)) { showAlert('upload-alert', 'Formato no permitido', 'error'); return; }
    document.getElementById('upload-zone').style.display = 'none';
    document.getElementById('upload-processing').style.display = 'block';
    document.getElementById('upload-result').style.display = 'none';
    document.getElementById('upload-alert').innerHTML = '';
    const formData = new FormData();
    formData.append('file', file);
    try {
        const r = await fetch(API + '/facturas/upload', { method: 'POST', headers: { 'Authorization': 'Bearer ' + TOKEN }, body: formData });
        const data = await r.json();
        document.getElementById('upload-processing').style.display = 'none';
        document.getElementById('upload-result').style.display = 'block';
        if (data.estado === 'Procesado') {
            document.getElementById('upload-result').innerHTML = `
                <div class="alert alert-success">Factura procesada exitosamente</div>
                <div class="detail-grid">
                    <div class="detail-item"><div class="label">No. Factura</div><div class="value">${esc(data.numero_factura)}</div></div>
                    <div class="detail-item"><div class="label">Proveedor</div><div class="value">${esc(data.nombre_proveedor || '-')}</div></div>
                    <div class="detail-item"><div class="label">NIT</div><div class="value">${esc(data.nit_proveedor || '-')}</div></div>
                    <div class="detail-item"><div class="label">Fecha</div><div class="value">${esc(data.fecha || '-')}</div></div>
                    <div class="detail-item"><div class="label">Subtotal</div><div class="value">Q ${data.subtotal.toFixed(2)}</div></div>
                    <div class="detail-item"><div class="label">IVA 12%</div><div class="value">Q ${data.impuestos.toFixed(2)}</div></div>
                    <div class="detail-item" style="grid-column:span 2"><div class="label">Total</div><div class="value" style="font-size:22px;color:#27ae60">Q ${data.total.toFixed(2)}</div></div>
                </div>
                <div style="margin-top:16px;display:flex;gap:8px">
                    <button class="btn btn-primary" onclick="resetUpload()">Cargar otra</button>
                    <button class="btn btn-success" onclick="viewFactura(${data.id})">Ver detalle</button>
                </div>`;
        } else {
            document.getElementById('upload-result').innerHTML = `
                <div class="alert alert-error">Error: ${esc(data.texto_extraido || 'Error desconocido')}</div>
                <button class="btn btn-primary" onclick="resetUpload()">Intentar de nuevo</button>`;
        }
    } catch (e) {
        document.getElementById('upload-processing').style.display = 'none';
        document.getElementById('upload-zone').style.display = 'block';
        showAlert('upload-alert', 'Error: ' + e.message, 'error');
    }
}

function resetUpload() {
    document.getElementById('upload-zone').style.display = 'block';
    document.getElementById('upload-result').style.display = 'none';
    document.getElementById('upload-processing').style.display = 'none';
    document.getElementById('file-input').value = '';
}

async function loadProveedores() {
    try {
        const r = await fetch(API + '/proveedores/', { headers: headers() });
        const provs = await r.json();
        document.getElementById('proveedores-table').innerHTML = provs.map(p => `
            <tr>
                <td>${esc(p.nombre)}</td><td>${esc(p.nit)}</td><td>${esc(p.direccion || '-')}</td>
                <td>${esc(p.telefono || '-')}</td><td>${esc(p.email || '-')}</td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="editProveedor(${p.id})">Editar</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteProveedor(${p.id})">Eliminar</button>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="6" style="text-align:center;color:#999;padding:20px">No hay proveedores</td></tr>';
    } catch (e) { console.error(e); }
}

function openProveedorModal(data) {
    document.getElementById('prov-id').value = data ? data.id : '';
    document.getElementById('prov-nombre').value = data ? data.nombre : '';
    document.getElementById('prov-nit').value = data ? data.nit : '';
    document.getElementById('prov-direccion').value = data ? (data.direccion || '') : '';
    document.getElementById('prov-telefono').value = data ? (data.telefono || '') : '';
    document.getElementById('prov-email').value = data ? (data.email || '') : '';
    document.getElementById('modal-prov-title').textContent = data ? 'Editar proveedor' : 'Nuevo proveedor';
    openModal('modal-proveedor');
}

async function editProveedor(id) {
    const r = await fetch(API + '/proveedores/' + id, { headers: headers() });
    openProveedorModal(await r.json());
}

async function saveProveedor() {
    const id = document.getElementById('prov-id').value;
    const nombre = document.getElementById('prov-nombre').value.trim();
    const nit = document.getElementById('prov-nit').value.trim();
    if (!nombre || !nit) { alert('Nombre y NIT obligatorios'); return; }
    const body = { nombre, nit, direccion: document.getElementById('prov-direccion').value.trim(), telefono: document.getElementById('prov-telefono').value.trim(), email: document.getElementById('prov-email').value.trim() };
    await fetch(id ? API + '/proveedores/' + id : API + '/proveedores/', { method: id ? 'PUT' : 'POST', headers: headers(), body: JSON.stringify(body) });
    closeModal('modal-proveedor');
    loadProveedores();
}

async function deleteProveedor(id) {
    if (!confirm('¿Eliminar proveedor?')) return;
    await fetch(API + '/proveedores/' + id, { method: 'DELETE', headers: headers() });
    loadProveedores();
}

async function loadBitacora() {
    try {
        const r = await fetch(API + '/bitacora/', { headers: headers() });
        const logs = await r.json();
        document.getElementById('bitacora-table').innerHTML = logs.map(l => `
            <tr>
                <td>${new Date(l.fecha_hora).toLocaleString('es-GT')}</td>
                <td>${esc(l.accion || '-')}</td>
                <td>${esc(l.documento || '-')}</td>
                <td>${badgeEstado(l.estado)}</td>
                <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(l.resultado || '-')}</td>
            </tr>
        `).join('') || '<tr><td colspan="5" style="text-align:center;color:#999;padding:20px">Sin registros</td></tr>';
    } catch (e) { console.error(e); }
}

function descargarReporte(formato) {
    window.open(API + '/reportes/' + formato, '_blank');
}

async function enviarReporteEmail() {
    const email = prompt('Ingrese el correo destino:');
    if (!email) return;
    const formato = prompt('Formato del reporte (pdf, excel, csv):', 'pdf');
    try {
        const r = await fetch(API + '/reportes/email', {
            method: 'POST', headers: headers(),
            body: JSON.stringify({ destinatario: email, formato: formato || 'pdf' })
        });
        const data = await r.json();
        alert(data.mensaje || data.detail);
    } catch (e) { alert('Error: ' + e.message); }
}

async function ejecutarRPA(facturaId) {
    if (!confirm('¿Ejecutar RPA para registrar esta factura en el formulario simulado?')) return;
    try {
        const r = await fetch(API + '/reportes/rpa/ejecutar/' + facturaId, {
            method: 'POST', headers: headers()
        });
        const data = await r.json();
        alert(data.mensaje);
    } catch (e) { alert('Error RPA: ' + e.message); }
}

function badgeEstado(estado) {
    const map = { 'Procesado': 'badge-success', 'Éxito': 'badge-success', 'Pendiente': 'badge-warning', 'Error': 'badge-danger', 'Rechazado': 'badge-danger' };
    return '<span class="badge ' + (map[estado] || 'badge-info') + '">' + esc(estado || '-') + '</span>';
}

function esc(text) { const d = document.createElement('div'); d.textContent = text || ''; return d.innerHTML; }

function showAlert(id, msg, type) { const c = document.getElementById(id); if (c) c.innerHTML = '<div class="alert alert-' + type + '">' + esc(msg) + '</div>'; }

function openModal(id) { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

window.onload = function () {
    setupDragDrop();
    document.querySelectorAll('.modal-overlay').forEach(o => o.addEventListener('click', function (e) { if (e.target === o) o.classList.remove('show'); }));
    document.getElementById('login-pass').addEventListener('keypress', function (e) { if (e.key === 'Enter') doLogin(); });
    if (TOKEN && USER) {
        enterApp();
    } else {
        document.getElementById('login-page').style.display = 'flex';
    }
};
