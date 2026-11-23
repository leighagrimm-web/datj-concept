<script>
// Download links: inside the artifact viewer, files are handed over through the downloads capability.
(function(){
  let dl = null;
  try { if (window.claude && claude.use) claude.use('downloads').then(d => { dl = d; }).catch(() => {}); } catch (e) {}
  document.addEventListener('click', async (e) => {
    const a = e.target.closest && e.target.closest('a[download]');
    if (!a || !dl) return;
    e.preventDefault();
    try {
      const blob = await (await fetch(a.getAttribute('href'))).blob();
      await dl.save({ filename: a.getAttribute('href').split('/').pop(), data: blob });
    } catch (err) { console.log('download not completed', err); }
  });
})();
</script>
