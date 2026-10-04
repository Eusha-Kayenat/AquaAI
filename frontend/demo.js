// Keeps the three Greenway seed observations switchable in the citizen screen.
// Guarded so that loading this file twice can't wrap renderResult twice.
if (!window.__aquaDemoPatched) {
  window.__aquaDemoPatched = true;

  let demoItems = [];
  const originalRenderResult = renderResult;
  renderResult = async () => {
    await originalRenderResult();
    if (!demoItems.length || !current) return;
    let chooser = document.querySelector('#demoChooser');
    if (!chooser) {
      chooser = document.createElement('div');
      chooser.id = 'demoChooser';
      chooser.className = 'chips';
      document.querySelector('#resultCard').prepend(chooser);
    }
    chooser.innerHTML = demoItems.map((item, index) =>
      `<button class="btn secondary small" onclick="switchDemo(${index})">Demo citizen ${index + 1} · ${item.status}</button>`
    ).join('');
  };
  window.switchDemo = index => {
    current = demoItems[index];
    renderResult();
  };
  window.resetForm = () => {
    demoItems = [];
    current = null;
    document.querySelector('#resultCard').hidden = true;
    document.querySelector('#startCard').hidden = false;
    document.querySelector('#observationText').value = '';
  };
  document.querySelector('#seed').onclick = async () => {
    try {
      demoItems = await api('/seed', { method: 'POST' });
      current = demoItems[0];
      document.querySelector('#startCard').hidden = true;
      await renderResult();
      toast('Demo data loaded. Select one of the three citizens below.');
    } catch (error) {
      toast(error.message);
    }
  };
}
