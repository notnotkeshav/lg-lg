// src/App.jsx
import Header from './components/UI/Header';
import Footer from './components/UI/Footer';
import './App.css';
import { FrappeProvider } from 'frappe-react-sdk';
import { Outlet } from 'react-router-dom';
import { FilterProvider } from './contexts/FilterContext';

function App() {
  return (
    <FrappeProvider
      socketPort={import.meta.env.VITE_SOCKET_PORT}
      sitename={import.meta.env.VITE_SITENAME}
    >
      <FilterProvider>
        <div className="min-h-screen flex flex-col">
          <Header />
          <main className="flex-1">
            <Outlet />
          </main>
          <Footer />
        </div>
      </FilterProvider>
    </FrappeProvider>
  );
}

export default App;