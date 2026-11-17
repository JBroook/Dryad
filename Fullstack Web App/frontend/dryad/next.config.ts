import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  devIndicators : false,
  allowedDevOrigins: ['192.168.100.7'],
  experimental: {
    agentUpgrade: false,
  },
};

export default nextConfig;
