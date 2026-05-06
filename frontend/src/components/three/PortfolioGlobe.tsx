'use client';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface AssetNode {
  ticker: string;
  weight: number;
  pnl: number;
}

const MOCK_ASSETS: AssetNode[] = [
  { ticker: 'Equity', weight: 0.6, pnl: 0.05 },
  { ticker: 'Cash', weight: 0.4, pnl: 0 },
];

export default function PortfolioGlobe({ assets = MOCK_ASSETS }: { assets?: AssetNode[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const w = canvas.offsetWidth || 400;
    const h = canvas.offsetHeight || 400;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(w, h);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 100);
    camera.position.z = 4;

    scene.add(new THREE.AmbientLight(0xffffff, 0.3));
    const dir = new THREE.DirectionalLight(0x00D4AA, 0.8);
    dir.position.set(5, 5, 5);
    scene.add(dir);

    // Globe wireframe
    const globeGeo = new THREE.SphereGeometry(1.5, 32, 32);
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0x00D4AA, wireframe: true, transparent: true, opacity: 0.05
    });
    const globe = new THREE.Mesh(globeGeo, globeMat);
    scene.add(globe);

    // Fibonacci-distributed nodes
    const numAssets = assets.length;
    const nodeMeshes: THREE.Mesh[] = [];

    assets.forEach((asset, i) => {
      const phi = Math.acos(-1 + (2 * i) / numAssets);
      const theta = Math.sqrt(numAssets * Math.PI) * phi;
      const x = 1.5 * Math.cos(theta) * Math.sin(phi);
      const y = 1.5 * Math.sin(theta) * Math.sin(phi);
      const z = 1.5 * Math.cos(phi);

      const color = asset.pnl > 0 ? 0x34C759 : asset.pnl < 0 ? 0xFF3B30 : 0xffffff;
      const size = 0.04 + asset.weight * 0.12;

      const geo = new THREE.SphereGeometry(size, 16, 16);
      const mat = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.4 });
      const node = new THREE.Mesh(geo, mat);
      node.position.set(x, y, z);
      scene.add(node);
      nodeMeshes.push(node);
    });

    // Mouse drag orbit
    let isDragging = false, prevX = 0, prevY = 0;
    const onMouseDown = (e: MouseEvent) => { isDragging = true; prevX = e.clientX; prevY = e.clientY; };
    const onMouseUp = () => { isDragging = false; };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      globe.rotation.y += (e.clientX - prevX) * 0.005;
      globe.rotation.x += (e.clientY - prevY) * 0.005;
      nodeMeshes.forEach(n => {
        if (n.parent === null) {
          scene.remove(n);
        }
      });
      prevX = e.clientX; prevY = e.clientY;
    };
    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    window.addEventListener('mousemove', onMouseMove);

    let raf: number;
    const group = new THREE.Group();
    group.add(globe, ...nodeMeshes);
    scene.add(group);

    const animate = () => {
      raf = requestAnimationFrame(animate);
      if (!isDragging) group.rotation.y += 0.002;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onMouseMove);
      renderer.dispose();
    };
  }, [assets]);

  return <canvas ref={canvasRef} style={{ width: '100%', height: 400 }} />;
}
