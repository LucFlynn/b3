import { Space_Grotesk } from "next/font/google";
import type { Metadata } from "next";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "EPI — Lead Quality Scoring for Media Buyers",
  description:
    "Score every lead with 7 automated checks. See the math on every score. No black box. Built for media buyers and agencies. 100 leads free.",
  openGraph: {
    title: "Stop reporting fake leads. Start scoring real ones.",
    description:
      "Score every lead with 7 automated checks. See the math on every score. No black box. Built for media buyers and agencies. 100 leads free.",
  },
};

export default function LPLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={`${display.variable} min-h-screen bg-[#09090b] text-zinc-100`}
    >
      {children}
    </div>
  );
}
