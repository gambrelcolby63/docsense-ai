import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { Header } from "@/components/Header";

import "./globals.css";

export const metadata: Metadata = {
  title: "DocSense AI",
  description: "Upload a PDF or a photo of a page. Get a summary and answers that quote the document.",
  icons: { icon: "/favicon.svg" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#f4efe6",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-paper font-sans text-ink antialiased">
        <div className="min-h-screen bg-[radial-gradient(1100px_480px_at_0%_-10%,#efe2cc,transparent),radial-gradient(800px_420px_at_100%_0%,#d9eee6,transparent)]">
          <Header />
          {children}
        </div>
      </body>
    </html>
  );
}
