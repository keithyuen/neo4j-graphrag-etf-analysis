import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './pages/Home'
import Graph from './pages/Graph'
import ErrorBoundary from './components/common/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/graph" element={<Graph />} />
        </Routes>
      </Layout>
    </ErrorBoundary>
  )
}

export default App