import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], weight: ["300", "400", "500", "600", "700", "800", "900"], variable: "--font-inter" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-space-grotesk" });

export const metadata: Metadata = {
  title: "NorteAcoes | Dashboard Fundamentalista",
  description: "Análise fundamentalista de ações da B3 com inteligência artificial para encontrar as melhores oportunidades.",
  metadataBase: new URL('https://acoes.vercel.app'),
  openGraph: {
    title: "NorteAcoes | Inteligência Artificial na Bolsa",
    description: "Descubra as ações mais baratas e rentáveis da B3 com nossos rankings exclusivos.",
    images: [{
      url: '/og-image.png', // Needs to be added to public folder later
      width: 1200,
      height: 630,
      alt: 'NorteAcoes Dashboard'
    }],
    locale: 'pt_BR',
    type: 'website',
  },
  robots: {
    index: true,
    follow: true,
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://acoes.onrender.com" />
      </head>
      <body className={`${inter.variable} ${spaceGrotesk.variable} antialiased`} suppressHydrationWarning>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
