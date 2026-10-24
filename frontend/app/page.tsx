'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import TopNav from '@/components/layout/TopNav';
import DashboardOverview from '@/components/pages/DashboardOverview';
import ParkingMap from '@/components/pages/ParkingMap';
import AINavigation from '@/components/pages/AINavigation';
import ReservationsPage from '@/components/pages/ReservationsPage';
import AnalyticsPage from '@/components/pages/AnalyticsPage';
import IoTSensorsPage from '@/components/pages/IoTSensorsPage';
import SettingsPage from '@/components/pages/SettingsPage';
import Toast from '@/components/ui/Toast';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SlotStatus, WSEvent } from '@/types';

export type PageId = 'overview' | 'map' | 'navigation' | 'reservations' | 'analytics' | 'iot' | 'settings';

interface ToastMessage {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
}

export default function Home() {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [slotUpdates, setSlotUpdates] = useState<Record<string, SlotStatus>>({});
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [activeRoute, setActiveRoute] = useState<string | null>(null);

  const addToast = useCallback((title: string, message: string, type: ToastMessage['type'] = 'info') => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev.slice(-2), { id, title, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }, []);

  const { status: wsStatus } = useWebSocket({
    onSlotUpdated: useCallback((data) => {
      const { slot_code, status } = data as { slot_code: string; status: SlotStatus };
      setSlotUpdates((prev) => ({ ...prev, [slot_code]: status }));
      if (status === 'occupied') {
        addToast('Slot Occupied', `${slot_code} is now occupied`, 'info');
      }
    }, [addToast]),
    onReservationCreated: useCallback((data) => {
      const { slot_code, reservation_code } = data as { slot_code: string; reservation_code: string };
      addToast('Reservation Created', `${reservation_code} confirmed for ${slot_code}`, 'success');
    }, [addToast]),
    onSimulatorEvent: useCallback((data) => {
      const { event } = data as { event: string };
      if (event === 'demo_started') {
        addToast('Demo Started', 'Live demo sequence is running...', 'info');
      }
    }, [addToast]),
  });

  const renderPage = () => {
    const props = { slotUpdates, addToast, selectedSlot, setSelectedSlot, activeRoute, setActiveRoute, setCurrentPage };
    switch (currentPage) {
      case 'overview': return <DashboardOverview {...props} />;
      case 'map': return <ParkingMap {...props} />;
      case 'navigation': return <AINavigation {...props} />;
      case 'reservations': return <ReservationsPage {...props} />;
      case 'analytics': return <AnalyticsPage {...props} />;
      case 'iot': return <IoTSensorsPage {...props} />;
      case 'settings': return <SettingsPage {...props} />;
      default: return <DashboardOverview {...props} />;
    }
  };

  const pageTitles: Record<PageId, string> = {
    overview: 'Dashboard Overview',
    map: 'Live Parking Map',
    navigation: 'AI Navigation',
    reservations: 'Reservations',
    analytics: 'Analytics',
    iot: 'IoT Sensors',
    settings: 'Settings',
  };

  return (
    <div className="app-shell">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} wsStatus={wsStatus} />
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <TopNav
          title={pageTitles[currentPage]}
          wsStatus={wsStatus}
          currentPage={currentPage}
        />
        <main className="app-content" style={{ flex: 1 }}>
          {renderPage()}
        </main>
      </div>

      {/* Toast notifications */}
      <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            title={toast.title}
            message={toast.message}
            type={toast.type}
            onClose={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
          />
        ))}
      </div>
    </div>
  );
}
