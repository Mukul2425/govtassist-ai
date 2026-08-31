import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GovtAssist AI — Government Scheme Discovery",
  description:
    "AI-powered platform to discover government schemes and check eligibility for Indian citizens.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
