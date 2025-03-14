import React from 'react';
import Image from 'next/image';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <section className="mb-12">
        <h1 className="text-4xl md:text-6xl font-display font-bold text-pitch-dark mb-4">
          Só Golasso
        </h1>
        <p className="text-xl text-gray-600">
          O melhor do futebol brasileiro e mundial, com estilo e personalidade
        </p>
      </section>

      {/* Trending Articles Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-display font-bold text-pitch-dark mb-6">
          🔥 Em Alta
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Article cards will be mapped here */}
        </div>
      </section>

      {/* Latest News Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-display font-bold text-pitch-dark mb-6">
          📰 Últimas Notícias
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* News items will be mapped here */}
        </div>
      </section>

      {/* Match Highlights Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-display font-bold text-pitch-dark mb-6">
          ⚽ Melhores Momentos
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Embedded videos will be mapped here */}
        </div>
      </section>

      {/* Meme Corner Section */}
      <section className="mb-12">
        <h2 className="text-2xl font-display font-bold text-pitch-dark mb-6">
          😂 Zoeira do Dia
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Meme content will be mapped here */}
        </div>
      </section>

      {/* Social Media Feed Sidebar */}
      <aside className="fixed top-0 right-0 w-80 h-screen bg-white shadow-lg p-4 transform translate-x-full lg:translate-x-0 transition-transform duration-200">
        <h3 className="text-xl font-display font-bold text-pitch-dark mb-4">
          📱 Feed Social
        </h3>
        {/* Social media feed will be embedded here */}
      </aside>
    </div>
  );
} 