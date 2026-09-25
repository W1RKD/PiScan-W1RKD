const $ = (id) => document.getElementById(id);
let state = null;
function notice(text, error = false) { $('notice').textContent = text; $('notice').className = error ? 'error' : 'muted'; setTimeout(() => $('notice').textContent = '', 3500); }
async function api(path, options = {}) { const response = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...options}); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed'); return data; }
function render() {
  $('latitude').value = state.location.latitude ?? '';
  $('longitude').value = state.location.longitude ?? '';
  $('radius').value = state.radius_miles;
  $('mode').value = state.mode;
  $('modeBadge').textContent = state.mode.toUpperCase();
  $('count').textContent = `${state.channels.length} channel(s) · ${state.watch_ids.length} watched`;
  $('channels').innerHTML = state.channels.map(c => `<tr><td><strong>${escapeHtml(c.tag)}</strong><small>${escapeHtml(c.id)}</small></td><td>${c.frequency_mhz.toFixed(6)} MHz<br><small>${escapeHtml(c.modulation)} ${c.tone ? '· ' + escapeHtml(c.tone) : ''}</small></td><td>${c.distance_miles == null ? '—' : c.distance_miles.toFixed(1) + ' mi'}</td><td>${c.enabled ? 'Enabled' : 'Disabled'}</td><td><button data-watch="${escapeHtml(c.id)}" class="${state.watch_ids.includes(c.id) ? 'active' : ''}">${state.watch_ids.includes(c.id) ? '★ Watched' : '☆ Watch'}</button></td></tr>`).join('');
  document.querySelectorAll('[data-watch]').forEach(button => button.onclick = async () => { state = await api('/api/watch', {method: 'POST', body: JSON.stringify({id: button.dataset.watch})}); render(); });
}
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
$('saveSettings').onclick = async () => { try { state = await api('/api/settings', {method: 'POST', body: JSON.stringify({latitude: $('latitude').value || null, longitude: $('longitude').value || null, radius_miles: Number($('radius').value), mode: $('mode').value})}); render(); notice('Settings saved'); } catch (e) { notice(e.message, true); } };
$('addForm').onsubmit = async (event) => { event.preventDefault(); try { state = await api('/api/channel', {method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(event.target)))}); event.target.reset(); render(); notice('Channel added'); } catch (e) { notice(e.message, true); } };
$('import').onclick = async () => { const file = $('file').files[0]; if (!file) return notice('Choose a CSV or JSON file first', true); try { state = await api('/api/import', {method: 'POST', body: JSON.stringify({format: file.name.endsWith('.csv') ? 'csv' : 'json', text: await file.text()})}); render(); notice('Channels imported'); } catch (e) { notice(e.message, true); } };
$('download').onclick = async () => { const data = await api('/api/export'); const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'}); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'systems.json'; link.click(); URL.revokeObjectURL(link.href); };
api('/api/state').then(data => { state = data; render(); }).catch(e => notice(e.message, true));
