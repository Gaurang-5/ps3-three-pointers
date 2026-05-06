'use client';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';

function getRiskColor(varValue: number): number {
  if (varValue < 0.02) return 0x00D4AA;   // teal — low risk
  if (varValue < 0.035) return 0xFF9F0A;  // amber — medium risk
  return 0xFF3B30;                          // red — high risk
}

interface RiskSphereProps {
  varValue?: number;
}

export default function RiskSphere({ varValue = 0.023 }: RiskSphereProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(200, 200);
    renderer.shadowMap.enabled = true;

    const color = getRiskColor(varValue);

    // Outer wireframe icosphere
    const geo = new THREE.IcosahedronGeometry(1, 3);
    const mat = new THREE.MeshBasicMaterial({ color, wireframe: true, transparent: true, opacity: 0.55 });
    const sphere = new THREE.Mesh(geo, mat);
    scene.add(sphere);

    // Inner glow
    const innerGeo = new THREE.SphereGeometry(0.85, 32, 32);
    const innerMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.06 });
    scene.add(new THREE.Mesh(innerGeo, innerMat));

    // Concentric ring
    const ringGeo = new THREE.RingGeometry(0.95, 1.0, 64);
    const ringMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    scene.add(ring);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(color, 1);
    dirLight.position.set(2, 2, 2);
    scene.add(dirLight);

    let raf: number;
    const animate = () => {
      raf = requestAnimationFrame(animate);
      sphere.rotation.y += 0.003;
      sphere.rotation.x += 0.001;
      ring.rotation.z += 0.002;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      geo.dispose(); mat.dispose();
      innerGeo.dispose(); innerMat.dispose();
      ringGeo.dispose(); ringMat.dispose();
      renderer.dispose();
    };
  }, [varValue]);

  return <canvas ref={canvasRef} style={{ width: 200, height: 200 }} />;
}
