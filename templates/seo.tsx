/**
 * SEO: Next.js metadata helpers for consistent SEO across pages
 * Usage:
 *   // In page.tsx:
 *   export const metadata = seo({
 *     title: "About Us",
 *     description: "Learn more about our company",
 *     image: "/og-about.jpg",
 *   });
 *
 *   // JSON-LD in layout/page:
 *   <JsonLd data={organizationJsonLd({ name: "Acme", url: "https://acme.com" })} />
 */
import type { Metadata } from "next";

// ---- Config ----

const SITE_CONFIG = {
    name: "My App",
    url: "https://yourdomain.com",
    defaultDescription: "Your default site description for SEO",
    defaultImage: "/og-default.jpg",
    twitterHandle: "@yourhandle",
    locale: "en_US",
};

// ---- Metadata Helper ----

interface SeoOptions {
    title: string;
    description?: string;
    image?: string;
    url?: string;
    type?: "website" | "article";
    noIndex?: boolean;
}

export function seo(options: SeoOptions): Metadata {
    const {
        title,
        description = SITE_CONFIG.defaultDescription,
        image = SITE_CONFIG.defaultImage,
        url = SITE_CONFIG.url,
        type = "website",
        noIndex = false,
    } = options;

    const fullTitle = `${title} | ${SITE_CONFIG.name}`;
    const imageUrl = image.startsWith("http") ? image : `${SITE_CONFIG.url}${image}`;

    return {
        title: fullTitle,
        description,
        ...(noIndex && { robots: { index: false, follow: false } }),
        openGraph: {
            title: fullTitle,
            description,
            url,
            siteName: SITE_CONFIG.name,
            images: [{ url: imageUrl, width: 1200, height: 630, alt: title }],
            locale: SITE_CONFIG.locale,
            type,
        },
        twitter: {
            card: "summary_large_image",
            title: fullTitle,
            description,
            images: [imageUrl],
            creator: SITE_CONFIG.twitterHandle,
        },
        alternates: { canonical: url },
    };
}

// ---- JSON-LD Component ----

export function JsonLd({ data }: { data: Record<string, unknown> }) {
    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
        />
    );
}

// ---- JSON-LD Generators ----

export function organizationJsonLd(org: { name: string; url: string; logo?: string }) {
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        name: org.name,
        url: org.url,
        ...(org.logo && { logo: org.logo }),
    };
}

export function articleJsonLd(article: {
    title: string;
    description: string;
    url: string;
    image: string;
    author: string;
    publishedAt: string;
    modifiedAt?: string;
}) {
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        headline: article.title,
        description: article.description,
        url: article.url,
        image: article.image,
        author: { "@type": "Person", name: article.author },
        datePublished: article.publishedAt,
        ...(article.modifiedAt && { dateModified: article.modifiedAt }),
    };
}

export function breadcrumbJsonLd(items: { name: string; url: string }[]) {
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: items.map((item, i) => ({
            "@type": "ListItem",
            position: i + 1,
            name: item.name,
            item: item.url,
        })),
    };
}
