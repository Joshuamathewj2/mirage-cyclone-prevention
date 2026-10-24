import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MIRAGE | Disaster Response Dashboard",
  description: "Digital twin situational awareness and governed disaster response planning.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
