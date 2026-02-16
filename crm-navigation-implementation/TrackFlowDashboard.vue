<template>
  <div class="trackflow-dashboard">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">TrackFlow Analytics</h1>
        <p class="mt-1 text-sm text-gray-600">
          Marketing attribution and link tracking
        </p>
      </div>

      <div class="flex gap-3">
        <button
          @click="refreshData"
          class="btn btn-secondary"
        >
          <RefreshCw :size="16" class="mr-2" />
          Refresh
        </button>
        <router-link
          to="/trackflow/campaigns"
          class="btn btn-primary"
        >
          <Plus :size="16" class="mr-2" />
          New Campaign
        </router-link>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4 mb-6">
      <StatCard
        title="Total Clicks"
        :value="stats.totalClicks"
        :change="stats.clicksChange"
        icon="MousePointerClick"
        color="blue"
      />
      <StatCard
        title="Active Campaigns"
        :value="stats.activeCampaigns"
        :change="stats.campaignsChange"
        icon="Target"
        color="green"
      />
      <StatCard
        title="Conversions"
        :value="stats.conversions"
        :change="stats.conversionsChange"
        icon="CheckCircle"
        color="purple"
      />
      <StatCard
        title="Attribution Revenue"
        :value="formatCurrency(stats.revenue)"
        :change="stats.revenueChange"
        icon="DollarSign"
        color="orange"
      />
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Frappe Dashboard Embed (Option 1) -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Campaign Performance</h3>
        </div>
        <div class="card-body">
          <iframe
            :src="frappePageUrl"
            class="w-full h-96 border-0"
            @load="onIframeLoad"
          />
        </div>
      </div>

      <!-- Native Vue Chart (Option 2) -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recent Activity</h3>
        </div>
        <div class="card-body">
          <ActivityList :activities="recentActivities" />
        </div>
      </div>
    </div>

    <!-- Quick Links -->
    <div class="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
      <QuickLinkCard
        title="View All Campaigns"
        description="Manage your marketing campaigns"
        to="/trackflow/campaigns"
        icon="Target"
      />
      <QuickLinkCard
        title="Tracked Links"
        description="Create and manage tracking links"
        to="/trackflow/links"
        icon="Link"
      />
      <QuickLinkCard
        title="Analytics Report"
        description="Deep dive into your data"
        to="/trackflow/analytics"
        icon="BarChart3"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { RefreshCw, Plus } from 'lucide-vue-next'
import StatCard from '@/components/StatCard.vue'
import ActivityList from './components/ActivityList.vue'
import QuickLinkCard from './components/QuickLinkCard.vue'

// Frappe API calls
const { $frappe } = inject('$frappe')

const stats = ref({
  totalClicks: 0,
  clicksChange: 0,
  activeCampaigns: 0,
  campaignsChange: 0,
  conversions: 0,
  conversionsChange: 0,
  revenue: 0,
  revenueChange: 0
})

const recentActivities = ref([])

const frappePageUrl = computed(() => {
  return `${window.location.origin}/app/trackflow-dashboard`
})

async function loadDashboardData() {
  try {
    // Call TrackFlow API
    const response = await $frappe.call({
      method: 'trackflow.api.analytics.get_dashboard_stats',
      args: {
        period: '30d'
      }
    })

    if (response.message) {
      stats.value = response.message.stats
      recentActivities.value = response.message.recent_activities
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    $frappe.toast({
      message: 'Failed to load dashboard data',
      type: 'error'
    })
  }
}

async function refreshData() {
  await loadDashboardData()
  $frappe.toast({
    message: 'Data refreshed',
    type: 'success'
  })
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(value)
}

function onIframeLoad() {
  console.log('Frappe page loaded')
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.trackflow-dashboard {
  @apply p-6;
}

.card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200;
}

.card-header {
  @apply px-6 py-4 border-b border-gray-200;
}

.card-title {
  @apply text-lg font-semibold text-gray-900;
}

.card-body {
  @apply p-6;
}

.btn {
  @apply inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-secondary {
  @apply bg-white text-gray-700 border border-gray-300 hover:bg-gray-50;
}
</style>
