/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Only use standalone output for production builds (Railway/Docker)
  ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),
};

module.exports = nextConfig;
