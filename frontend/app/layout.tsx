import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ParkFlow AI — Smart Parking & Indoor Navigation',
  description: 'Real-time smart parking management with AI-powered indoor navigation across multi-floor garages.',
  keywords: 'smart parking, indoor navigation, IoT, parking management, AI routing',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
