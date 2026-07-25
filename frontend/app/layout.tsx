import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import QueryProvider from "@/components/QueryProvider";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

export const metadata: Metadata = {
  title: "LeakLens — Find & Fix Your Subscription Leaks",
  description:
    "Scan SMS alerts and bank statements to detect recurring subscriptions, flag price hikes, and redirect savings into a growth fund. Privacy-first, no bank API required.",
  keywords: ["subscription tracker", "money leak", "fintech", "savings", "price hike detector"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body className="min-h-screen">
        <QueryProvider>
          <Navbar />
          <main className="pt-16">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
