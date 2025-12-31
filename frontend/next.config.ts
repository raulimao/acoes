import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    scrollRestoration: true,
  },
  transpilePackages: ['lucide-react', 'recharts', 'framer-motion'],
};

export default nextConfig;
