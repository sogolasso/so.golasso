import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { ShareIcon, HeartIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';

interface ArticleCardProps {
  id: string;
  title: string;
  excerpt: string;
  imageUrl: string;
  category: string;
  publishedAt: string;
  author: string;
  likes: number;
  comments: number;
  shares: number;
  slug: string;
}

export default function ArticleCard({
  id,
  title,
  excerpt,
  imageUrl,
  category,
  publishedAt,
  author,
  likes,
  comments,
  shares,
  slug,
}: ArticleCardProps) {
  return (
    <article className="article-card">
      <Link href={`/noticia/${slug}`} className="block">
        <div className="relative h-48 w-full">
          <Image
            src={imageUrl}
            alt={title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          <div className="absolute inset-0 gradient-overlay" />
          <span className="absolute top-4 left-4 bg-golasso-500 text-white px-2 py-1 rounded text-sm">
            {category}
          </span>
        </div>
        <div className="p-4">
          <h3 className="font-display font-bold text-xl mb-2 line-clamp-2">
            {title}
          </h3>
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{excerpt}</p>
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>{author}</span>
            <span>{publishedAt}</span>
          </div>
        </div>
      </Link>
      <div className="px-4 pb-4 border-t border-gray-100 mt-2 pt-2">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <button className="flex items-center space-x-1 hover:text-golasso-500">
            <HeartIcon className="h-5 w-5" />
            <span>{likes}</span>
          </button>
          <button className="flex items-center space-x-1 hover:text-golasso-500">
            <ChatBubbleLeftIcon className="h-5 w-5" />
            <span>{comments}</span>
          </button>
          <button className="flex items-center space-x-1 hover:text-golasso-500">
            <ShareIcon className="h-5 w-5" />
            <span>{shares}</span>
          </button>
        </div>
      </div>
    </article>
  );
} 