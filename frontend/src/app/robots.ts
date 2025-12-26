import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
    return {
        rules: {
            userAgent: '*',
            allow: '/',
            disallow: ['/payment/', '/auth/callback', '/admin/'],
        },
        sitemap: 'https://acoes.vercel.app/sitemap.xml',
    };
}
