import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { Nav } from "./nav";

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Interview Practice",
  description: "Rehearse behavioral job interviews with an LLM interviewer and get a STAR evaluation.",
};

// The root layout stays a server component so it can export `metadata`.
// Everything interactive lives in "use client" files (ADR-0001).
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      {/* Full-height column: the top bar stays put and <main> scrolls, so the Interview page
          can pin its Answer box to the bottom. Other pages centre themselves with <Page>.
          `relative` keeps the hidden (`sr-only`, absolutely positioned) inputs inside <main>;
          without it they stretch the page and add a second scrollbar. */}
      <body className="flex h-dvh flex-col bg-background text-foreground">
        <Nav />
        <main className="relative min-h-0 flex-1 overflow-y-auto">{children}</main>
      </body>
    </html>
  );
}
