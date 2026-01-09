(async function(){
  // Show an animation GIF, wait until it's finished (by duration),
  // and navigate to the picked topic once backend result is ready.
  const container = document.getElementById('omikuji');
  if (!container) return;

  // duration in ms; can be overridden by data-duration on the container
  const duration = parseInt(container.dataset.duration || '3000', 10) || 3000;
  const gifSrc = '/static/omikuji_gif.gif';

  // render GIF
  container.innerHTML = '';
  const img = document.createElement('img');
  img.src = gifSrc;
  img.alt = 'おみくじアニメーション';
  img.style.maxWidth = '480px';
  img.style.width = '100%';
  img.style.display = 'block';
  img.style.margin = '0 auto 18px';
  container.appendChild(img);

  // small caption while animating
  const caption = document.createElement('div');
  caption.innerText = 'おみくじを引いています...';
  caption.className = 'center';
  container.appendChild(caption);

  // start backend request in parallel
  const fetchPromise = fetch('/omikuji', { headers: { 'Accept': 'application/json' } })
    .then(r => {
      if (!r.ok) throw new Error('no topics');
      return r.json();
    });

  // wait for animation duration
  const timerPromise = new Promise(resolve => setTimeout(resolve, duration));

  try {
    const [j] = await Promise.all([fetchPromise, timerPromise]);
    // navigate to the selected topic
    window.location.href = '/topics/' + encodeURIComponent(j.id);
  } catch (e) {
    container.innerHTML = '';
    container.innerText = '話題がありません';
    console.error(e);
  }
})();
