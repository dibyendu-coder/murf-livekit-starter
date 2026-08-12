import type { Metadata } from 'next';
import {
  EscalationsDashboard,
  type Escalation,
} from '@/components/app/escalations-dashboard';

export const metadata: Metadata = {
  title: 'Human Help Dashboard — SpeakEasy AI',
  description:
    'Teacher dashboard for reviewing and managing human-help requests created by the voice learning agent.',
};

// Revalidate on every request (always fresh data)
export const revalidate = 0;

async function fetchEscalations(): Promise<Escalation[]> {
  try {
    const backendUrl = process.env.ESCALATIONS_API_URL ?? 'http://localhost:8080';
    const res = await fetch(`${backendUrl}/api/escalations`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      console.error(
        `[dashboard] Failed to fetch escalations: ${res.status} ${res.statusText}`
      );
      return [];
    }

    return res.json();
  } catch (err) {
    console.error('[dashboard] Error fetching escalations:', err);
    return [];
  }
}

export default async function DashboardPage() {
  const escalations = await fetchEscalations();

  return <EscalationsDashboard initialEscalations={escalations} />;
}
