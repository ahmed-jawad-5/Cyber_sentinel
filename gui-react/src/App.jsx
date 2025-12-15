import './App.css';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';

function App() {
  return (
    <div className="desktop-app">
      {/* Sidebar / Navbar */}
      <aside className="sidebar">
        <div className="logo">
          <img src={viteLogo} alt="Vite" />
          <img src={reactLogo} alt="React" className="react-logo" />
        </div>
        <nav>
          <ul>
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#alerts">Alerts</a></li>
            <li><a href="#analytics">Analytics</a></li>
            <li><a href="#settings">Settings</a></li>
          </ul>
        </nav>
      </aside>

      {/* Main content area */}
      <main className="main-content">
        <section id="dashboard" className="panel">
          <h1>UDP Network Anomaly Detector</h1>
          <p>Welcome to your desktop GUI dashboard!</p>
          <button className="cta-btn">Launch Detection</button>
        </section>

        <section id="alerts" className="panel">
          <h2>Real-Time Alerts</h2>
          <p>Get notified instantly about unusual network traffic.</p>
        </section>

        <section id="analytics" className="panel">
          <h2>Analytics Dashboard</h2>
          <p>Visualize network activity and anomalies in real-time charts.</p>
        </section>

        <section id="settings" className="panel">
          <h2>Settings</h2>
          <p>Configure alert thresholds, notifications, and AI parameters.</p>
        </section>
      </main>
    </div>
  );
}

export default App;
