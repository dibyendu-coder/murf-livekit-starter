import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.ESCALATIONS_API_URL ?? 'http://localhost:8080';

// GET /api/escalations — proxy to Python backend
export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/escalations`, {
      cache: 'no-store',
    });
    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend returned ${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data, {
      headers: { 'Cache-Control': 'no-store' },
    });
  } catch (err) {
    console.error('[escalations] GET failed:', err);
    return NextResponse.json(
      { error: 'Could not reach escalations backend.' },
      { status: 502 }
    );
  }
}
