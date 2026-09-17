import './globals.css'

export const metadata = {
  title: 'VisualNote AI — Turn Videos into Visual Notes',
  description: 'AI-Powered Video-to-Visual Learning Platform (FYP Edition)',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
