<template>
  <div class="flex h-screen flex-col border-r">
    <!-- Logo Section -->
    <div class="flex items-center justify-between px-4 py-4">
      <router-link to="/" class="flex items-center gap-2">
        <div class="grid h-8 w-8 place-items-center rounded bg-gray-900 text-white">
          <span class="text-lg font-bold">C</span>
        </div>
        <span class="text-lg font-semibold text-gray-900">CRM</span>
      </router-link>
    </div>

    <!-- Navigation Items -->
    <nav class="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
      <!-- Standard CRM Items -->
      <SidebarItem
        v-for="item in navigationItems"
        :key="item.label"
        :to="item.route"
        :icon="item.icon"
        :label="item.label"
      />

      <!-- TrackFlow Section -->
      <div class="pt-4 mt-4 border-t border-gray-200">
        <div class="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase">
          Marketing
        </div>

        <SidebarItem
          to="/trackflow"
          icon="TrendingUp"
          label="TrackFlow"
        />

        <!-- TrackFlow Submenu (optional) -->
        <div v-if="isTrackFlowExpanded" class="ml-4 mt-1 space-y-1">
          <SidebarItem
            to="/trackflow/campaigns"
            icon="Target"
            label="Campaigns"
            :is-sub-item="true"
          />
          <SidebarItem
            to="/trackflow/links"
            icon="Link"
            label="Tracked Links"
            :is-sub-item="true"
          />
          <SidebarItem
            to="/trackflow/analytics"
            icon="BarChart3"
            label="Analytics"
            :is-sub-item="true"
          />
        </div>
      </div>
    </nav>

    <!-- User Section -->
    <div class="border-t border-gray-200 p-4">
      <UserMenu />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import SidebarItem from './SidebarItem.vue'
import UserMenu from './UserMenu.vue'

const route = useRoute()

const navigationItems = [
  {
    label: 'Leads',
    icon: 'Users',
    route: '/leads'
  },
  {
    label: 'Deals',
    icon: 'DollarSign',
    route: '/deals'
  },
  {
    label: 'Organizations',
    icon: 'Building2',
    route: '/organizations'
  },
  {
    label: 'Contacts',
    icon: 'User',
    route: '/contacts'
  },
  {
    label: 'Activities',
    icon: 'CalendarCheck',
    route: '/activities'
  }
]

// Track if TrackFlow submenu should be expanded
const isTrackFlowExpanded = computed(() => {
  return route.path.startsWith('/trackflow')
})
</script>

<style scoped>
/* Add any custom styles here */
</style>
