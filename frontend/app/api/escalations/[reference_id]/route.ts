import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.ESCALATIONS_API_URL ?? 'http://localhost:8080';

interface RouteParams {
  params: Promise<{ reference_id: string }>;
}

// PATCH /api/escalations/[reference_id]/status — update status
export async function PATCH(req: Request, { params }: RouteParams) {
  const { reference_id } = await params;
  try {
    const body = await req.json();
    const res = await fetch(
      `${BACKEND_URL}/api/escalations/${encodeURIComponent(reference_id)}/status`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    );
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error(`[escalations] PATCH ${reference_id} failed:`, err);
    return NextResponse.json(
      { error: 'Could not reach escalations backend.' },
      { status: 502 }
    );
  }
}
