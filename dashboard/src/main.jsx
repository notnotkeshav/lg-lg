import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import './index.css'
import App from './App.jsx'

import ErrorPage from './pages/Error.jsx'
import Homepage from './pages/Homepage'
import Region from './pages/Region'
import Branch from './pages/Branch'
import Manager from './pages/Manager'

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    // Top-level catch: handles render errors in any child route
    errorElement: <ErrorPage />,
    children: [
      {
        index: true,
        element: <Homepage />,
        errorElement: <ErrorPage />,
      },
      {
        path: '/region/:regionId',
        element: <Region />,
        errorElement: <ErrorPage />,
      },
      {
        path: '/branch/:branchId',
        element: <Branch />,
        errorElement: <ErrorPage />,
      },
      {
        path: '/manager/:managerId',
        element: <Manager />,
        errorElement: <ErrorPage />,
      },
    ]
  }
], { basename: import.meta.env.VITE_BASENAME })

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
