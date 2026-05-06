'use client';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

// Generate mock OHLC from portfolio timeseries
function generateMockCandles(count = 30): Candle[] {
  let price = 100;
  return Array.from({ length: count }, (_, i) => {
    const open = price;
    const change = (Math.random() - 0.47) * 5;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * 2;
    const low = Math.min(open, close) - Math.random() * 2;
    price = close;
    return {
      date: new Date(Date.now() - (count - i) * 86400000).toISOString().split('T')[0],
      open, high, low, close,
    };
  });
}

export default function CandlestickChart3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const w = canvas.offsetWidth || 600;
    const h = canvas.offsetHeight || 340;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(w, h);
    renderer.shadowMap.enabled = true;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 500);
    camera.position.set(18, 14, 28);
    camera.lookAt(18, 0, 0);

    // Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(10, 20, 10);
    dir.castShadow = true;
    scene.add(dir);

    const candles = generateMockCandles(30);
    const priceMin = Math.min(...candles.map(c => c.low));
    const priceRange = Math.max(...candles.map(c => c.high)) - priceMin;
    const scale = 8 / priceRange;

    const meshes: THREE.Mesh[] = [];

    candles.forEach((day, i) => {
      const isUp = day.close >= day.open;
      const color = isUp ? 0x34C759 : 0xFF3B30;
      const bodyH = Math.max(Math.abs(day.close - day.open) * scale, 0.05);
      const midBody = ((day.open + day.close) / 2 - priceMin) * scale;

      const bodyGeo = new THREE.BoxGeometry(0.6, bodyH, 0.6);
      const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.3, metalness: 0.6 });
      const body = new THREE.Mesh(bodyGeo, bodyMat);
      body.position.set(i * 1.2, midBody, 0);
      body.castShadow = true;
      scene.add(body);
      meshes.push(body);

      // Wick
      const wickH = Math.max((day.high - day.low) * scale, 0.1);
      const wickGeo = new THREE.BoxGeometry(0.08, wickH, 0.08);
      const wick = new THREE.Mesh(wickGeo, bodyMat);
      wick.position.set(i * 1.2, ((day.high + day.low) / 2 - priceMin) * scale, 0);
      scene.add(wick);
    });

    // Floor grid
    const gridHelper = new THREE.GridHelper(40, 40, 0x222222, 0x1a1a1a);
    gridHelper.position.y = -0.1;
    scene.add(gridHelper);

    // Mouse scroll zoom
    const onWheel = (e: WheelEvent) => {
      camera.position.z = Math.max(10, Math.min(60, camera.position.z + e.deltaY * 0.05));
    };
    canvas.addEventListener('wheel', onWheel, { passive: true });

    let raf: number;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      canvas.removeEventListener('wheel', onWheel);
      meshes.forEach(m => { m.geometry.dispose(); (m.material as THREE.Material).dispose(); });
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} style={{ width: '100%', height: 340 }} />;
}
