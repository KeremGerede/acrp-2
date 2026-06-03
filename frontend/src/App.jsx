import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tenants from './pages/Tenants'
import Integrations from './pages/Integrations'
import ReviewRules from './pages/ReviewRules'
import FunctionalTestConfigs from './pages/FunctionalTestConfigs'
import EventLogs from './pages/EventLogs'
import MergeReviews from './pages/MergeReviews'
import MergeReviewDetail from './pages/MergeReviewDetail'
import FunctionalTests from './pages/FunctionalTests'
import FunctionalTestDetail from './pages/FunctionalTestDetail'
import Promotions from './pages/Promotions'
import UserStats from './pages/UserStats'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="tenants" element={<Tenants />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="review-rules" element={<ReviewRules />} />
          <Route path="test-configs" element={<FunctionalTestConfigs />} />
          <Route path="events" element={<EventLogs />} />
          <Route path="merge-reviews" element={<MergeReviews />} />
          <Route path="merge-reviews/:id" element={<MergeReviewDetail />} />
          <Route path="functional-tests" element={<FunctionalTests />} />
          <Route path="functional-tests/:id" element={<FunctionalTestDetail />} />
          <Route path="promotions" element={<Promotions />} />
          <Route path="stats" element={<UserStats />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
