import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // We check for the auth_token cookie or header.
  // Note: Since the login uses localStorage right now, we can't read it natively in Edge middleware.
  // For a robust implementation, the auth token should be stored in cookies. 
  // For now, we will allow basic pass-through and let the client-side handle immediate redirects if token is missing.
  // Let's implement a basic cookie check. If we update login to set a cookie, this will work.
  // Since we know the login sets localStorage, this middleware is more of a placeholder until cookies are used.
  
  const token = request.cookies.get('auth_token')?.value;
  const isAuthPage = request.nextUrl.pathname.startsWith('/login');
  
  if (isAuthPage) {
    if (token) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
    return NextResponse.next();
  }

  // Protect all other routes (except static files, api, etc. which are filtered by the matcher)
  if (!token) {
    // If no token in cookie, we can't definitively block here without breaking the localStorage approach,
    // but in a "totally set up" app, cookies should be used.
    // For now, we'll let it pass and rely on client-side or we can enforce the cookie.
    // Let's enforce it and we will update the login form to set a cookie as well.
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
