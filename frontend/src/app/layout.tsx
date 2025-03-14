import type { Metadata } from 'next'
import { Inter, Montserrat } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const montserrat = Montserrat({ subsets: ['latin'], variable: '--font-montserrat' })

export const metadata: Metadata = {
  title: 'Só Golasso - Futebol com Estilo',
  description: 'O melhor do futebol brasileiro e mundial, com notícias, análises táticas, memes e muito mais.',
  keywords: 'futebol, brasileirão, libertadores, copa do brasil, memes de futebol, análise tática',
  openGraph: {
    title: 'Só Golasso - Futebol com Estilo',
    description: 'O melhor do futebol brasileiro e mundial',
    url: 'https://sogolasso.com.br',
    siteName: 'Só Golasso',
    locale: 'pt_BR',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Só Golasso - Futebol com Estilo',
    description: 'O melhor do futebol brasileiro e mundial',
    creator: '@sogolasso',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${montserrat.variable}`}>
      <body className="min-h-screen bg-gray-50">
        <header className="bg-pitch-dark text-white">
          {/* Header component will go here */}
        </header>
        <main>{children}</main>
        <footer className="bg-pitch-dark text-white mt-auto">
          {/* Footer component will go here */}
        </footer>
      </body>
    </html>
  )
} 