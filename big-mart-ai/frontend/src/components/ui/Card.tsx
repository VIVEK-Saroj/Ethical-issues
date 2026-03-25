import { clsx } from 'clsx';
import { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  padding?: boolean;
  hover?: boolean;
}

export default function Card({ children, className, padding = true, hover = false, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800',
        hover && 'hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-700 transition-all duration-200',
        padding && 'p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
