
import type { SVGProps } from 'react';
import Link from 'next/link';

// A simple placeholder logo. Replace with actual SVG or Image component.
const PlaceholderLogoIcon = (props: SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
  </svg>
);

interface AppLogoProps {
  className?: string;
  iconSize?: number;
  textSize?: string;
  href?: string;
}

export function AppLogo({ className, iconSize = 28, textSize = "text-xl", href = "/dashboard" }: AppLogoProps) {
  return (
    <Link href={href} className={`flex items-center gap-2 select-none group ${className}`}>
      <div className="relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg blur opacity-25 group-hover:opacity-60 transition duration-500"></div>
        <PlaceholderLogoIcon 
          className="relative text-blue-600 dark:text-blue-400 transition-transform duration-500 group-hover:scale-110" 
          style={{ height: iconSize, width: iconSize }} 
          data-ai-hint="geometric abstract" 
        />
      </div>
      <span className={`font-black ${textSize} tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400`}>
        SCADA Assistant
      </span>
    </Link>
  );
}
