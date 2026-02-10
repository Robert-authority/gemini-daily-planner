async function loadJadwal() {
  // kalau lagi di halaman login, jangan fetch jadwal
  if (!document.getElementById("jadwalList")) {
    startFX();
    return;
  }

  const res = await fetch("/jadwal");
  const data = await res.json();

  const list = document.getElementById("jadwalList");
  list.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    list.innerHTML = `
      <div class="item">
        <div class="item-left">
          <b>Belum ada jadwal</b>
          <small>Coba input jadwal dulu.</small>
        </div>
      </div>
    `;
    startFX();
    return;
  }

  data.forEach(item => {
    const div = document.createElement("div");
    div.className = "item";

    div.innerHTML = `
      <div class="item-left">
        <b>${escapeHTML(item.judul)}</b>
        <small>${escapeHTML(item.tanggal)} • ${escapeHTML(item.jam)}</small>
      </div>
      <button class="btn-delete" onclick="hapus(${item.id})">✕</button>
    `;

    list.appendChild(div);
  });

  startFX();
}

async function kirim() {
  const text = document.getElementById("inputText").value.trim();

  if (!text) {
    alert("Tulis jadwal dulu 😭");
    return;
  }

  const res = await fetch("/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });

  const result = await res.json();

  if (result.status === "success") {
    document.getElementById("inputText").value = "";
    loadJadwal();
  } else {
    alert("Error: " + result.message);
  }
}

async function hapus(id) {
  await fetch("/delete/" + id, { method: "DELETE" });
  loadJadwal();
}

function escapeHTML(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadJadwal();


// ====== FX: Spark Fireworks (Sunset aesthetic) ======
let fxStarted = false;

function startFX() {
  if (fxStarted) return;
  fxStarted = true;

  const canvas = document.getElementById("fx");
  const ctx = canvas.getContext("2d");

  let W = 0, H = 0;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  const sparks = [];

  function rand(min, max) {
    return Math.random() * (max - min) + min;
  }

  function spawnSpark() {
    const x = rand(0, W);
    const y = rand(0, H * 0.7);
    const count = Math.floor(rand(12, 24));

    for (let i = 0; i < count; i++) {
      sparks.push({
        x,
        y,
        vx: rand(-2.2, 2.2),
        vy: rand(-2.2, 2.2),
        life: rand(25, 60),
        size: rand(1, 2.6),
        alpha: 1
      });
    }
  }

  for (let i = 0; i < 6; i++) spawnSpark();

  setInterval(() => {
    if (sparks.length < 900) spawnSpark();
  }, 900);

  function animate() {
    ctx.clearRect(0, 0, W, H);

    for (let i = sparks.length - 1; i >= 0; i--) {
      const p = sparks[i];

      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.02;

      p.life -= 1;
      p.alpha = Math.max(0, p.life / 60);

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);

      ctx.fillStyle = `rgba(255, 200, 120, ${p.alpha})`;
      ctx.shadowBlur = 14;
      ctx.shadowColor = `rgba(120, 80, 255, ${p.alpha})`;
      ctx.fill();

      if (p.life <= 0) sparks.splice(i, 1);
    }

    requestAnimationFrame(animate);
  }

  animate();
}
