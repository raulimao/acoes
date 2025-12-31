import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    optimizeCss: {
      pruneSource: true,
    },
    // swcMinify is default true in v15+, but adding explicitly as requested
    // Note: 'swcMinify' is deprecated in config but implied by default. 
    // We will stick to optimizeCss object config.
  },
  transpilePackages: ['lucide-react', 'recharts', 'framer-motion'],
};

export default nextConfig;
