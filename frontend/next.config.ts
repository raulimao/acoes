import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  experimental: {
    optimizeCss: true,
  },
  /* webpack: (config, { isServer }) => {
    if (!isServer) {
        config.resolve.alias['core-js'] = false;
    }
    return config;
  }, */
};

export default nextConfig;
