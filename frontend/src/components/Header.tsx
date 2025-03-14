import React from 'react';
import Link from 'next/link';
import { useSession, signIn, signOut } from 'next-auth/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Início', href: '/' },
  { name: 'Notícias', href: '/noticias' },
  { name: 'Jogos', href: '/jogos' },
  { name: 'Times', href: '/times' },
  { name: 'Memes', href: '/memes' },
];

export default function Header() {
  const { data: session } = useSession();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  return (
    <nav className="bg-pitch-dark">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl font-display font-bold text-white">
              Só Golasso
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="nav-link font-medium"
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* User Menu */}
          <div className="hidden md:flex items-center space-x-4">
            {session ? (
              <div className="flex items-center space-x-4">
                <span className="text-white">{session.user?.name}</span>
                <button
                  onClick={() => signOut()}
                  className="btn-secondary text-sm"
                >
                  Sair
                </button>
              </div>
            ) : (
              <button
                onClick={() => signIn()}
                className="btn-primary text-sm"
              >
                Entrar
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-white p-2"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="block px-3 py-2 nav-link font-medium"
                onClick={() => setIsMenuOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            {!session ? (
              <button
                onClick={() => signIn()}
                className="w-full text-left px-3 py-2 nav-link font-medium"
              >
                Entrar
              </button>
            ) : (
              <button
                onClick={() => signOut()}
                className="w-full text-left px-3 py-2 nav-link font-medium"
              >
                Sair
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
} 