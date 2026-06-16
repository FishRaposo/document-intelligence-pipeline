import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { FileStack } from "lucide-react";
import Link from "next/link";
import ErrorBoundary from "@/components/ErrorBoundary";
import DemoModeBadge from "@/components/DemoModeBadge";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Document Intelligence Pipeline",
  description:
    "Ingest, chunk, embed, and search documents — with quarantine review and processing insights.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 text-gray-900 antialiased`}>
        <div className="flex min-h-screen flex-col">
          <header className="sticky top-0 z-20 border-b border-gray-200 bg-white">
            <div className="flex items-center justify-between px-4 py-3 sm:px-6">
              <Link href="/" className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
                  <FileStack className="h-5 w-5" />
                </span>
                <span className="text-base font-bold tracking-tight text-gray-900">
                  Document Intelligence
                </span>
              </Link>
              <div className="flex items-center gap-3">
                <DemoModeBadge />
                <span className="hidden text-xs text-gray-400 sm:inline">
                  v1.0.0
                </span>
              </div>
            </div>
          </header>

          <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-6 sm:px-6">
            <aside className="hidden w-56 flex-shrink-0 md:block">
              <div className="sticky top-20">
                <Sidebar />
              </div>
            </aside>
            <main className="min-w-0 flex-1">
              <ErrorBoundary>{children}</ErrorBoundary>
            </main>
          </div>

          {/* Mobile nav */}
          <div className="sticky bottom-0 z-20 border-t border-gray-200 bg-white px-2 py-1 md:hidden">
            <Sidebar />
          </div>
        </div>
      </body>
    </html>
  );
}
