import type { Metadata } from 'next';
import {
  AnalyticsDashboard,
  type AnalyticsData,
} from '@/components/app/analytics-dashboard';

export const metadata: Metadata = {
  title: 'Call Analytics — SpeakEasy AI',
  description:
    'Real-time call analytics dashboard tracking voice session outcomes, exercise completions, and call metrics.',
};

// Revalidate on every request (always fresh server data)
export const revalidate = 0;

async function fetchAnalyticsData(): Promise<AnalyticsData | undefined> {
  try {
    const backendUrl = process.env.ESCALATIONS_API_URL ?? 'http://localhost:8080';
    const res = await fetch(`${backendUrl}/api/analytics`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      console.error(
        `[analytics-page] Failed to fetch analytics: ${res.status} ${res.statusText}`
      );
      return undefined;
    }

    return res.json();
  } catch (err) {
    console.error('[analytics-page] Error fetching analytics:', err);
    return undefined;
  }
}

export default async function AnalyticsPage() {
  const initialData = await fetchAnalyticsData();

  return <AnalyticsDashboard initialData={initialData} />;
}
