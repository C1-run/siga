// siga landing — Three.js 3D engine (vanilla ES module, minimized)
// crystal → explosion → survivor glow, driven by scroll progress.
// Perf budget: no post-processing, no transmission pass, 40 shards, DPR 1,
// paused when hero is offscreen or tab hidden, skipped on small touch screens;
// reduced-motion renders a single static frame instead of hiding the scene.

import * as THREE from 'three';

const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
// Skip only on actual phones: coarse pointer (touch) + narrow viewport.
// A narrow desktop window keeps the 3D scene.
const isMobile =
  window.matchMedia('(pointer: coarse)').matches && window.matchMedia('(max-width: 768px)').matches;
const canvas3d = document.getElementById('three-canvas');
const heroSection = document.getElementById('hero');

if (canvas3d && heroSection && !isMobile) {
  window.__diag.scene = 'init';
  // --- Setup ---
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 0, 8);
  const renderer = new THREE.WebGLRenderer({ canvas: canvas3d, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1));

  // Lights — multi-color for caustic refraction
  scene.add(new THREE.AmbientLight(0x111111, 2));
  const keyLight = new THREE.PointLight(0x00ff94, 3, 25);
  keyLight.position.set(0, 2, 5);
  scene.add(keyLight);
  const fillLight = new THREE.PointLight(0x4488ff, 1.5, 20);
  fillLight.position.set(-3, -1, 3);
  scene.add(fillLight);
  const rimLight = new THREE.PointLight(0xffffff, 1, 15);
  rimLight.position.set(3, 1, -2);
  scene.add(rimLight);
  const redLight = new THREE.PointLight(0xff4d4d, 0, 20);
  redLight.position.set(-2, 1, 3);
  scene.add(redLight);

  // --- Environment map for crystal reflections (procedural) ---
  const pmremGenerator = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  envScene.background = new THREE.Color(0x050505);
  const envGeo = new THREE.SphereGeometry(50, 16, 16);
  const envCanvas = document.createElement('canvas');
  envCanvas.width = 512;
  envCanvas.height = 256;
  const ectx = envCanvas.getContext('2d');
  const grad = ectx.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, '#001a0d');
  grad.addColorStop(0.4, '#000000');
  grad.addColorStop(0.7, '#000000');
  grad.addColorStop(1, '#0a0a0a');
  ectx.fillStyle = grad;
  ectx.fillRect(0, 0, 512, 256);
  // Bright spots for sparkle
  for (let s = 0; s < 8; s++) {
    ectx.fillStyle = `rgba(0,255,148,${0.3 + Math.random() * 0.4})`;
    ectx.beginPath();
    ectx.arc(Math.random() * 512, Math.random() * 120, 8 + Math.random() * 20, 0, Math.PI * 2);
    ectx.fill();
  }
  const envTex = new THREE.CanvasTexture(envCanvas);
  envTex.mapping = THREE.EquirectangularReflectionMapping;
  const envMap = pmremGenerator.fromEquirectangular(envTex).texture;

  // --- Hero Crystal (faceted gem with flat shading) ---
  // No transmission: it forces an extra internal render pass. envMap + iridescence
  // on an opaque-ish physical material keeps the gem look at a fraction of the cost.
  const crystalGeo = new THREE.IcosahedronGeometry(1.3, 1);
  const crystalMat = new THREE.MeshPhysicalMaterial({
    color: 0x00ff94,
    metalness: 0.25,
    roughness: 0.05,
    clearcoat: 1,
    clearcoatRoughness: 0,
    iridescence: 1,
    iridescenceIOR: 1.8,
    iridescenceThicknessRange: [100, 700],
    transparent: true,
    opacity: 0.9,
    envMap: envMap,
    envMapIntensity: 1.6,
    flatShading: true,
  });
  const crystal = new THREE.Mesh(crystalGeo, crystalMat);
  crystal.position.set(0, 0, 0);
  scene.add(crystal);

  // --- Inner glowing core ---
  const coreGeo = new THREE.IcosahedronGeometry(0.45, 0);
  const coreMat = new THREE.MeshBasicMaterial({
    color: 0x00ff94,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
  });
  const core = new THREE.Mesh(coreGeo, coreMat);
  crystal.add(core);

  // Core glow sprite (soft halo — replaces bloom post-processing)
  const glowCanvas = document.createElement('canvas');
  glowCanvas.width = 128;
  glowCanvas.height = 128;
  const gctx = glowCanvas.getContext('2d');
  const glowGrad = gctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  glowGrad.addColorStop(0, 'rgba(0,255,148,0.8)');
  glowGrad.addColorStop(0.4, 'rgba(0,255,148,0.3)');
  glowGrad.addColorStop(1, 'rgba(0,255,148,0)');
  gctx.fillStyle = glowGrad;
  gctx.fillRect(0, 0, 128, 128);
  const glowTex = new THREE.CanvasTexture(glowCanvas);
  const glowMat = new THREE.SpriteMaterial({ map: glowTex, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending });
  const glowSprite = new THREE.Sprite(glowMat);
  glowSprite.scale.set(3.4, 3.4, 1);
  crystal.add(glowSprite);

  // Wireframe overlay on crystal
  const wireGeo = new THREE.IcosahedronGeometry(1.32, 1);
  const wireMat = new THREE.LineBasicMaterial({ color: 0x00ff94, transparent: true, opacity: 0.25 });
  const wireframe = new THREE.LineSegments(new THREE.WireframeGeometry(wireGeo), wireMat);
  crystal.add(wireframe);

  // --- Orbiting satellites (3 small shards) ---
  const satellites = [];
  for (let i = 0; i < 3; i++) {
    const satGeo = new THREE.OctahedronGeometry(0.08, 0);
    const satMat = new THREE.MeshBasicMaterial({ color: 0x00ff94, transparent: true, opacity: 0.9 });
    const sat = new THREE.Mesh(satGeo, satMat);
    sat.userData = { angle: (i / 3) * Math.PI * 2, radius: 1.8 + i * 0.15, speed: 0.5 + i * 0.2, tilt: i * 0.3 };
    crystal.add(sat);
    satellites.push(sat);
  }

  // --- Caustic light on floor ---
  const causticCanvas = document.createElement('canvas');
  causticCanvas.width = 256;
  causticCanvas.height = 256;
  const cctx = causticCanvas.getContext('2d');
  const causGrad = cctx.createRadialGradient(128, 128, 0, 128, 128, 128);
  causGrad.addColorStop(0, 'rgba(0,255,148,0.15)');
  causGrad.addColorStop(0.5, 'rgba(0,100,50,0.05)');
  causGrad.addColorStop(1, 'rgba(0,0,0,0)');
  cctx.fillStyle = causGrad;
  cctx.fillRect(0, 0, 256, 256);
  const causticTex = new THREE.CanvasTexture(causticCanvas);
  const causticMat = new THREE.MeshBasicMaterial({ map: causticTex, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
  const caustic = new THREE.Mesh(new THREE.PlaneGeometry(4, 4), causticMat);
  caustic.position.set(0, -2.5, 0);
  caustic.rotation.x = -Math.PI / 2;
  scene.add(caustic);

  // --- Shard system (explosion, reduced count) ---
  const shards = [];
  const shardCount = 40;
  const shardGroup = new THREE.Group();
  scene.add(shardGroup);

  for (let i = 0; i < shardCount; i++) {
    const size = 0.05 + Math.random() * 0.15;
    const geo = new THREE.TetrahedronGeometry(size, 0);
    const mat = new THREE.MeshStandardMaterial({
      color: Math.random() > 0.3 ? 0x1a1a1a : 0x0d0d0d,
      metalness: 0.8,
      roughness: 0.3,
      transparent: true,
      opacity: 0,
    });
    const shard = new THREE.Mesh(geo, mat);
    shard.position.set(0, 0, 0);
    shard.userData = {
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      vz: (Math.random() - 0.5) * 0.15,
      rx: (Math.random() - 0.5) * 0.05,
      ry: (Math.random() - 0.5) * 0.05,
      rz: (Math.random() - 0.5) * 0.05,
      settled: false,
      targetOpacity: 0.7,
    };
    shardGroup.add(shard);
    shards.push(shard);
  }

  // --- Survivor green glow (cased section) ---
  const survivorLight = new THREE.PointLight(0x00ff94, 0, 10);
  survivorLight.position.set(0, -3, 2);
  scene.add(survivorLight);

  const survivorRing = new THREE.Mesh(
    new THREE.RingGeometry(0.3, 0.35, 32),
    new THREE.MeshBasicMaterial({ color: 0x00ff94, transparent: true, opacity: 0, side: THREE.DoubleSide })
  );
  survivorRing.position.set(0, -3, 2);
  survivorRing.rotation.x = Math.PI / 2;
  scene.add(survivorRing);

  // --- Reduced motion: static frame only, no listeners, no rAF loop ---
  if (isReduced) {
    window.__diag.scene = 'static-reduced-motion';
    causticMat.opacity = 0.3;
    renderer.render(scene, camera);
    window.addEventListener('resize', () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.render(scene, camera);
    });
  } else {
  // --- Scroll state ---
  let scrollProgress = 0;
  let exploded = false;
  let explosionTime = 0;

  function updateScroll() {
    const maxScroll = document.body.scrollHeight - window.innerHeight;
    scrollProgress = Math.min(1, window.scrollY / maxScroll);
  }
  window.addEventListener('scroll', updateScroll, { passive: true });
  updateScroll();

  // --- Mouse parallax ---
  let mouseX = 0, mouseY = 0;
  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  // --- Resize ---
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // --- Animation loop ---
  let time = 0;
  function animate() {
    rafId = requestAnimationFrame(animate);
    time += 0.016;

    // Phase: hero (<0.12), explosion (0.12-0.20), debris+survivor (0.20+)
    const heroPhase = scrollProgress < 0.12;
    const explosionPhase = scrollProgress >= 0.12 && scrollProgress < 0.20;
    const debrisPhase = scrollProgress >= 0.20;

    // Trigger explosion
    if (explosionPhase && !exploded) {
      exploded = true;
      explosionTime = 0;
      crystalMat.opacity = 0;
      wireMat.opacity = 0;
      coreMat.opacity = 0;
      glowMat.opacity = 0;
      causticMat.opacity = 0;
      satellites.forEach((s) => (s.material.opacity = 0));
      redLight.intensity = 5;
      keyLight.intensity = 0;
      fillLight.intensity = 0;
      shards.forEach((s) => { s.userData.settled = false; });
    }

    // Reset on scroll back up
    if (heroPhase && exploded) {
      exploded = false;
      crystalMat.opacity = 0.9;
      wireMat.opacity = 0.25;
      coreMat.opacity = 0.8;
      glowMat.opacity = 0.6;
      keyLight.intensity = 3;
      fillLight.intensity = 1.5;
      redLight.intensity = 0;
      satellites.forEach((s) => (s.material.opacity = 0.9));
      shards.forEach((s) => {
        s.position.set(0, 0, 0);
        s.material.opacity = 0;
      });
    }

    // Crystal animation (hero phase)
    if (heroPhase) {
      crystal.rotation.y += 0.004;
      crystal.rotation.x = Math.sin(time * 0.3) * 0.12;
      // Smooth follow mouse position (lerp toward mouse world coords)
      const targetX = mouseX * 1.5;
      const targetY = -mouseY * 1.0;
      crystal.position.x += (targetX - crystal.position.x) * 0.08;
      crystal.position.y += (targetY - crystal.position.y) * 0.08;
      // Crystal tilts toward mouse direction
      crystal.rotation.z += (mouseX * 0.15 - crystal.rotation.z) * 0.05;

      // Inner core pulsing
      const corePulse = 1 + Math.sin(time * 1.5) * 0.15;
      core.scale.setScalar(corePulse);
      coreMat.opacity = 0.6 + Math.sin(time * 1.5) * 0.2;

      // Glow sprite breathing
      glowSprite.scale.setScalar(3.4 + Math.sin(time * 0.8) * 0.4);
      glowMat.opacity = 0.55 + Math.sin(time * 0.8) * 0.15;

      // Satellites orbiting
      satellites.forEach((sat) => {
        sat.userData.angle += 0.012 * sat.userData.speed;
        const r = sat.userData.radius;
        sat.position.x = Math.cos(sat.userData.angle) * r;
        sat.position.z = Math.sin(sat.userData.angle) * r;
        sat.position.y = Math.sin(sat.userData.angle * 2 + sat.userData.tilt) * 0.3;
        sat.rotation.x += 0.02;
        sat.rotation.y += 0.03;
      });

      // Caustic on floor
      causticMat.opacity = 0.3 + Math.sin(time * 0.6) * 0.1;
      caustic.position.x = crystal.position.x;
      caustic.scale.setScalar(1 + Math.sin(time * 0.6) * 0.1);

      // Key light follows crystal with drift
      keyLight.position.x += (crystal.position.x - keyLight.position.x) * 0.1;
      keyLight.position.y += (2 + Math.cos(time * 0.3) * 1 - keyLight.position.y) * 0.1;

      // Vibrate before explosion
      if (scrollProgress > 0.08) {
        const shake = (scrollProgress - 0.08) / 0.04;
        crystal.position.x += (Math.random() - 0.5) * shake * 0.12;
        crystal.position.y += (Math.random() - 0.5) * shake * 0.12;
        crystal.rotation.z += (Math.random() - 0.5) * shake * 0.08;
        crystalMat.emissive = new THREE.Color(0xff4d4d);
        crystalMat.emissiveIntensity = shake * 0.5;
        coreMat.color.setHex(0xff4d4d);
        glowMat.opacity = 0.6 * shake;
        keyLight.color.setHex(0xff4d4d);
        keyLight.intensity = 3 * (1 - shake) + shake * 2;
      } else {
        crystal.rotation.z *= 0.9;
        crystalMat.emissive = new THREE.Color(0x00ff94);
        crystalMat.emissiveIntensity = 0.08;
        coreMat.color.setHex(0x00ff94);
        keyLight.color.setHex(0x00ff94);
      }
    }

    // Explosion physics
    if (exploded && explosionTime < 3) {
      explosionTime += 0.016;
      shards.forEach((s, i) => {
        if (!s.userData.settled) {
          s.position.x += s.userData.vx;
          s.position.y += s.userData.vy;
          s.position.z += s.userData.vz;
          s.userData.vy -= 0.001; // gravity
          s.rotation.x += s.userData.rx;
          s.rotation.y += s.userData.ry;
          s.rotation.z += s.userData.rz;
          s.material.opacity = Math.min(s.userData.targetOpacity, s.material.opacity + 0.05);

          // Settle on floor
          if (s.position.y < -3) {
            s.position.y = -3;
            s.userData.vy *= -0.3;
            s.userData.vx *= 0.8;
            s.userData.vz *= 0.8;
            if (Math.abs(s.userData.vy) < 0.001) s.userData.settled = true;
          }
        } else {
          // Micro-vibration
          s.position.y += Math.sin(time * 3 + i) * 0.0005;
        }
      });
      redLight.intensity = Math.max(0, redLight.intensity - 0.05);
    }

    // Camera parallax — deeper offset for 3D depth feel
    camera.position.x += (mouseX * 0.8 - camera.position.x) * 0.04;
    camera.position.y += (-mouseY * 0.5 - camera.position.y) * 0.04;
    camera.lookAt(crystal.position.x * 0.3, crystal.position.y * 0.3, 0);

    // Camera scroll
    const scrollOffset = scrollProgress * 2;
    camera.position.z = 8 - scrollOffset * 0.5;

    // Survivor glow (cased section ~0.35-0.52 scroll)
    const survivorStart = 0.35;
    const survivorEnd = 0.52;
    if (scrollProgress > survivorStart && scrollProgress < survivorEnd) {
      const t = (scrollProgress - survivorStart) / (survivorEnd - survivorStart);
      survivorLight.intensity = t * 3;
      survivorRing.material.opacity = t * 0.6;
      const pulse = 1 + Math.sin(time * 2) * 0.2;
      survivorRing.scale.setScalar(pulse * t);
      survivorLight.position.x = Math.sin(time * 0.3) * 1;
    } else if (scrollProgress >= survivorEnd) {
      survivorLight.intensity = Math.max(0, survivorLight.intensity - 0.05);
      survivorRing.material.opacity = Math.max(0, survivorRing.material.opacity - 0.02);
    }

    renderer.render(scene, camera);
  }

  // --- Pause when hidden or hero offscreen (single rAF owner) ---
  let running = false;
  let rafId = 0;
  let heroVisible = true;
  let tabVisible = !document.hidden;

  function syncRun() {
    const shouldRun = heroVisible && tabVisible;
    if (shouldRun && !running) {
      running = true;
      animate();
    } else if (!shouldRun && running) {
      running = false;
      cancelAnimationFrame(rafId);
    }
  }

  document.addEventListener('visibilitychange', () => {
    tabVisible = !document.hidden;
    syncRun();
  });

  const heroObserver = new IntersectionObserver(
    (entries) => {
      heroVisible = entries[0].isIntersecting;
      syncRun();
    },
    { threshold: 0 }
  );
  heroObserver.observe(heroSection);

  syncRun();
  window.__diag.scene = 'animating';
  }
} else {
  window.__diag.scene = !canvas3d ? 'no-canvas' : !heroSection ? 'no-hero' : 'skipped-mobile';
}
