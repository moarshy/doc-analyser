import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Check if the request is for protected routes
  const protectedPaths = ['/dashboard', '/projects', '/api/protected'];
  const isProtectedPath = protectedPaths.some(path => 
    request.nextUrl.pathname.startsWith(path)
  );

  if (isProtectedPath) {
    // For API routes, check for Authorization header
    if (request.nextUrl.pathname.startsWith('/api/protected')) {
      const authHeader = request.headers.get('authorization');
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }
    }
    
    // For dashboard routes, we'll rely on client-side auth check
    // This is a placeholder for server-side auth validation
    // In production, you might want to validate JWT tokens here
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/projects/:path*', '/api/protected/:path*'],
};