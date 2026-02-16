// Add these routes to frontend/src/router/index.js

// Import TrackFlow views
import TrackFlowDashboard from '@/views/TrackFlow/Dashboard.vue'
import TrackFlowCampaigns from '@/views/TrackFlow/Campaigns.vue'
import TrackFlowLinks from '@/views/TrackFlow/Links.vue'
import TrackFlowAnalytics from '@/views/TrackFlow/Analytics.vue'

// Add to routes array
const trackflowRoutes = [
  {
    path: '/trackflow',
    name: 'TrackFlow',
    component: TrackFlowDashboard,
    meta: {
      requiresAuth: true,
      title: 'TrackFlow Dashboard'
    }
  },
  {
    path: '/trackflow/campaigns',
    name: 'TrackFlowCampaigns',
    component: TrackFlowCampaigns,
    meta: {
      requiresAuth: true,
      title: 'Campaigns'
    }
  },
  {
    path: '/trackflow/links',
    name: 'TrackFlowLinks',
    component: TrackFlowLinks,
    meta: {
      requiresAuth: true,
      title: 'Tracked Links'
    }
  },
  {
    path: '/trackflow/analytics',
    name: 'TrackFlowAnalytics',
    component: TrackFlowAnalytics,
    meta: {
      requiresAuth: true,
      title: 'Analytics'
    }
  }
]

export default trackflowRoutes
