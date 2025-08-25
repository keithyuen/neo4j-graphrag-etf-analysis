import { Link, useLocation } from 'react-router-dom'
import { Activity, BarChart3 } from 'lucide-react'
import clsx from 'clsx'

function Header() {
  const location = useLocation()
  
  const navigation = [
    { name: 'Query', href: '/', icon: Activity },
    { name: 'Graph', href: '/graph', icon: BarChart3 }
  ]
  
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">ETF GraphRAG</h1>
                <p className="text-xs text-gray-500 -mt-1">Analysis Platform</p>
              </div>
            </Link>
          </div>
          
          {/* Navigation */}
          <nav className="flex space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                    isActive
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
          
          {/* Status indicator */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-500">Online</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header